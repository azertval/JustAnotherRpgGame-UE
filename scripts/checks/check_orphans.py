#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Garde-fou : pas d'asset mort, pas de script sans appelant, pas de sortie du moteur sans script
(LOT-1001, décision D-32 ; LOT-1014, décision D-52).

Un lot qui remplace quelque chose le supprime dans sa propre PR. Ce contrôle est ce qui fait tenir
la règle lot après lot : il échoue sur ce qu'un remplacement laisse derrière lui.

**Les assets** — sous `Source/Elements/Assets/` :

- tout fichier est **cité** : par un manifeste ou une fiche (un JSON de l'arbre qui le nomme, par
  un chemin relatif à son propre dossier ou, comme le manifeste des maîtres, à la racine des
  assets ; ou l'atlas `Maps/world-maps.json`, qui nomme l'image d'une zone depuis cette racine),
  ou — pour un manifeste, une fiche ou une police, que rien d'autre ne peut citer — par le code
  qui le charge ;
- une pièce venue par passation dont le **lecteur n'est pas encore écrit** dans le nouveau moteur
  (une police avant l'interface du LOT-1020) est citée par `awaiting.json`, à la racine des
  assets, avec le lot qui l'attend : la liste dit ce qui est en attente, au lieu de le laisser
  passer pour mort ou de le supprimer. Une entrée dont le lot est livré est une erreur ;
- toute **entrée citée existe** : un chemin écrit sous une clé de fichier (`file`, `mesh`…) ou un
  dossier de personnage (`npcs`) désigne quelque chose sur le disque.

Un dossier de personnage cite tout ce qu'il contient : le détail de ses bandes est l'affaire de
`check_hd_assets.py`, qui connaît leur gabarit. Les provenances (`source`, `sources`) nomment des
fichiers de l'atelier local, hors dépôt : elles ne citent rien. Les pages d'accompagnement
(`README.md`, `CREDITS.md`, licences `.txt`) ne sont pas des assets.

**Les scripts** — sous `scripts/` : tout script est **appelé** par la CI (donc par `check.py`, qui
la lit), par un hook, par le build, par un document en vigueur, ou par un script lui-même appelé.
Un test n'est pas un appelant : un script que seul son test nomme est mort, et son test avec lui.
L'histoire (`CHANGELOG.md`, fiches de lots, archives) n'est pas un document en vigueur.

**Les sorties du moteur** — sous `Content/` (LOT-1014, D-52) : un `.uasset` ou un `.umap` est la
sortie d'un script du dépôt, jamais un fichier fait à la main dans l'éditeur. Chacun est donc
**cité par le script qui le produit** : son chemin de contenu (`/Game/…`), ou un dossier qui le
contient, est écrit dans un script appelé, ou dans une description de scène que
`build_scene_unreal.py` lit (`Source/Elements/Scenes/*.json`, champ `map`). Un asset que rien ne
cite ne se régénère pas : c'est une erreur, comme tout autre fichier trouvé sous `Content/`.

Les images des kits ne sont pas suivies par Git : le contrôle lit le **disque**, après
`scripts/fetch_assets.py`, comme `check_hd_assets.py`. `Content/` se lit sur le disque aussi : là
où il n'existe pas (un runner sans moteur), il n'y a rien à vérifier. Aucune dépendance.

Usage :
    python scripts/checks/check_orphans.py                # code de sortie non nul si orphelin
    python scripts/checks/check_orphans.py --sans-kits    # sans les assets : un poste ou un
                                                          # runner où les kits ne sont pas installés
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Les clés dont la valeur est le chemin d'un fichier d'asset, relatif au dossier du JSON.
FILE_KEYS = ("file", "mesh", "model", "texture", "portrait", "token")
# Les clés dont les valeurs sont des dossiers de personnage : ils citent leur contenu.
FOLDER_KEYS = ("npcs",)
# Les provenances : des chemins de l'atelier local (`Tools/`), jamais des fichiers du dépôt.
# De même les doublons écartés d'une livraison (`duplicates`, manifeste des maîtres).
PROVENANCE_KEYS = ("source", "sources", "duplicates")
# Les pièces dont le lecteur arrive dans un lot nommé (voir l'en-tête).
AWAITING = "awaiting.json"
LOT_ID = re.compile(r"^LOT-\d+$")
# Ce qui accompagne les assets sans en être.
COMPANIONS = (".md", ".txt")
# Ce que seul le code peut citer : un manifeste, une fiche, une police.
CODE_CITED = (".json", ".ttf", ".otf")
# Le code qui charge les assets, et l'outillage qui les installe.
CODE_TREES = ("Source/JustAnotherRpgGame", "scripts")
CODE_SUFFIXES = (".h", ".cpp", ".cs", ".py", ".cmake", ".txt")
IGNORED_DIRS = {"__pycache__", ".git", "build", "generated", "External"}

SCRIPT_SUFFIXES = (".py", ".ps1")
# Les fichiers d'un script qui n'ont pas d'appelant propre : structure d'un paquet, réglage de pytest.
STRUCTURAL = {"__init__.py", "__main__.py", "conftest.py"}
# Ce qui appelle un script. Les tests n'en sont pas.
CALLER_FILES = (".pre-commit-config.yaml", "CMakeLists.txt", "CMakePresets.json", "pyproject.toml",
                "README.md", "CONTRIBUTING.md", "AGENTS.md")
CALLER_TREES = (".github", "cmake", "Documentation", "Planning/standards", "Planning/outils",
                "Source", "Site")
CALLER_SUFFIXES = (".yml", ".yaml", ".md", ".ps1", ".py", ".cmake", ".txt")
# L'histoire n'appelle rien : un script cité là seulement a disparu de l'usage. Les données non plus.
HISTORY_DIRS = ("Planning/standards/archives/", "Documentation/Archives/", "Source/Elements/",
                "Source/Test/")

# Les sorties du moteur, et ce qui les cite : un chemin de contenu d'au moins un dossier.
ENGINE_OUTPUTS = (".uasset", ".umap")
CONTENT_PATH = re.compile(r"/Game(?:/[\w.\-]+)+")
SCENE_DESCRIPTIONS = "Source/Elements/Scenes"


def walk(base: Path):
    """Les fichiers sous `base`, hors dossiers ignorés, dans un ordre stable."""
    if not base.is_dir():
        return
    for path in sorted(base.rglob("*"), key=lambda p: p.as_posix()):
        parts = path.relative_to(base).parts
        # Un dossier pointé est un état local (`.kits/`, l'inventaire de `fetch_assets.py`).
        if path.is_file() and not IGNORED_DIRS.intersection(parts) \
                and not any(part.startswith(".") for part in parts[:-1]):
            yield path


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


# ----------------------------------------------------------------------------------------------
# Les assets
# ----------------------------------------------------------------------------------------------

def citations(value, key: str | None = None):
    """Les chaînes d'un JSON, avec la clé qui les porte, hors provenances : (clé, chaîne)."""
    if isinstance(value, dict):
        for name, child in value.items():
            if name not in PROVENANCE_KEYS:
                yield from citations(child, name)
    elif isinstance(value, list):
        for child in value:
            yield from citations(child, key)
    elif isinstance(value, str):
        yield key, value


def is_path(text: str) -> bool:
    """Une chaîne qui peut être un chemin relatif : ni vide, ni absolue, ni une phrase."""
    return bool(text) and len(text) < 260 and "\n" not in text and not text.startswith(("/", "#")) \
        and ":" not in text and ".." not in Path(text).parts


def check_awaiting(assets: Path, planning: Path | None) -> list[str]:
    """Les entrées fautives de la liste d'attente : sans lot, ou dont le lot est livré."""
    listing = assets / AWAITING
    if not listing.is_file():
        return []
    try:
        entries = json.loads(read(listing)).get("awaiting", [])
    except json.JSONDecodeError:
        return []  # dit par `check_assets`, qui lit tous les JSON de l'arbre
    errors: list[str] = []
    for entry in entries:
        lot = entry.get("lot", "")
        if not LOT_ID.match(lot):
            errors.append(f"{AWAITING} : {entry.get('file', '?')} n'attend aucun lot (« lot »)")
            continue
        fiches = list(planning.glob(f"versions/**/lots/{lot}-*.md")) if planning is not None else []
        if any(re.search(r'^statut\s*=\s*"livre"', read(fiche), re.M) for fiche in fiches):
            errors.append(f"{AWAITING} : {entry['file']} attend le {lot}, qui est livré — son lecteur "
                          "le cite, ou la pièce se supprime (D-32)")
    return errors


def check_assets(assets: Path, code: str, atlas: Path | None = None,
                 planning: Path | None = None) -> list[str]:
    """Les orphelins de `assets` ; `code` est le texte du code qui charge les assets, `atlas` un
    manifeste hors de l'arbre qui cite depuis sa racine, `planning` le dossier des fiches de lot."""
    errors: list[str] = check_awaiting(assets, planning)
    files = list(walk(assets))
    cited: set[Path] = set()

    if atlas is not None and atlas.is_file():
        try:
            for _, text in citations(json.loads(read(atlas))):
                if is_path(text):
                    cited.update(base / text for base in (assets, assets / "Maps") if (base / text).is_file())
        except json.JSONDecodeError as error:
            errors.append(f"{atlas.name} : illisible ({error})")

    for manifest in (path for path in files if path.suffix == ".json"):
        label = manifest.relative_to(assets).as_posix()
        try:
            content = json.loads(read(manifest))
        except json.JSONDecodeError as error:
            errors.append(f"{label} : illisible ({error})")
            continue
        for key, text in citations(content):
            if not is_path(text):
                continue
            target = manifest.parent / text
            if key in FOLDER_KEYS:
                if target.is_dir():
                    cited.update(walk(target))
                else:
                    errors.append(f"{label} : « {key} » cite le dossier absent {text}")
            elif target.is_file():
                cited.add(target)
            elif (assets / text).is_file():
                cited.add(assets / text)  # cité depuis la racine des assets (les maîtres)
            elif key in FILE_KEYS:
                errors.append(f"{label} : « {key} » cite le fichier absent {text}")

    for path in files:
        if path in cited or path.suffix in COMPANIONS:
            continue
        # La description d'animation d'une image citée la suit : `arrow.anim.json` pour `arrow.png`.
        if path.name.endswith(".anim.json"):
            stem = path.name[: -len(".anim.json")]
            if any(image in cited for image in path.parent.glob(stem + ".*") if image != path):
                continue
        if path.suffix in CODE_CITED and path.name in code:
            continue
        errors.append(f"{path.relative_to(assets).as_posix()} : aucun manifeste ni fiche ne le cite")
    return errors


def asset_code(root: Path) -> str:
    """Le texte du code qui charge les assets : il cite les manifestes et les polices par leur nom."""
    parts = []
    for tree in CODE_TREES:
        parts += [read(path) for path in walk(root / tree) if path.suffix in CODE_SUFFIXES]
    return "\n".join(parts)


# ----------------------------------------------------------------------------------------------
# Les scripts
# ----------------------------------------------------------------------------------------------

def package_of(script: Path, scripts: Path) -> Path | None:
    """Le paquet Python qui contient `script` (le dossier le plus haut portant `__init__.py`)."""
    package = None
    for parent in script.relative_to(scripts).parents:
        if (scripts / parent / "__init__.py").is_file() and parent != Path("."):
            package = scripts / parent
    return package


def names(script: Path, scripts: Path) -> list[re.Pattern]:
    """Ce par quoi un appelant désigne `script` : son nom de fichier, ou l'import de son module."""
    stem = re.escape(script.stem)
    patterns = [re.compile(r"(?<![\w.-])" + re.escape(script.name) + r"(?![\w-])")]
    if script.suffix == ".py":
        patterns.append(re.compile(r"^\s*(?:import|from)\s+(?:[\w.]*\.)?" + stem + r"\b", re.M))
        patterns.append(re.compile(r"^\s*from\s+[\w.]*\s+import\s+[^\n]*\b" + stem + r"\b", re.M))
    package = package_of(script, scripts)
    if package is not None and script.name in STRUCTURAL:
        # Un paquet s'appelle par son nom : `python -m sourcebook`, `scripts/sourcebook`.
        name = re.escape(package.name)
        patterns = [re.compile(r"-m\s+(?:scripts\.)?" + name + r"\b"),
                    re.compile(r"scripts[/\\]" + name + r"\b")]
    return patterns


def callers(root: Path) -> str:
    """Le texte de tout ce qui appelle un script, hors `scripts/` et hors histoire."""
    parts = [read(root / name) for name in CALLER_FILES if (root / name).is_file()]
    for tree in CALLER_TREES:
        for path in walk(root / tree):
            if path.suffix in CALLER_SUFFIXES and not path.relative_to(root).as_posix().startswith(HISTORY_DIRS):
                parts.append(read(path))
    return "\n".join(parts)


def check_scripts(scripts: Path, calling: str) -> list[str]:
    """Les scripts de `scripts` que rien n'appelle ; `calling` est le texte des appelants."""
    candidates = [path for path in walk(scripts)
                  if path.suffix in SCRIPT_SUFFIXES and "tests" not in path.relative_to(scripts).parts
                  and path.name != "conftest.py"]
    called: set[Path] = set()
    text = calling
    progress = True
    while progress:  # un script appelé appelle à son tour : on ferme la relation
        progress = False
        for script in candidates:
            if script not in called and any(p.search(text) for p in names(script, scripts)):
                called.add(script)
                text += "\n" + read(script)
                progress = True
    return [f"scripts/{path.relative_to(scripts).as_posix()} : ni la CI, ni un hook, ni un document "
            "en vigueur, ni un script appelé ne le nomme"
            for path in candidates if path not in called]


# ----------------------------------------------------------------------------------------------
# Les sorties du moteur
# ----------------------------------------------------------------------------------------------

def content_citations(root: Path) -> set[str]:
    """Les chemins de contenu (`/Game/…`) que nomment les scripts et les descriptions de scène."""
    cited: set[str] = set()
    for path in walk(root / "scripts"):
        if path.suffix in SCRIPT_SUFFIXES and "tests" not in path.relative_to(root / "scripts").parts:
            cited.update(CONTENT_PATH.findall(read(path)))
    for path in walk(root / SCENE_DESCRIPTIONS):
        if path.suffix == ".json":
            cited.update(CONTENT_PATH.findall(read(path)))
    return cited


def check_content(content: Path, cited: set[str]) -> list[str]:
    """Les fichiers de `content` qu'aucun script ne produit ; `cited` vient de `content_citations`."""
    errors: list[str] = []
    for path in walk(content):
        relative = path.relative_to(content).as_posix()
        if path.suffix not in ENGINE_OUTPUTS:
            errors.append(f"Content/{relative} : ni .uasset ni .umap, rien à faire sous Content/")
            continue
        package = "/Game/" + relative[: -len(path.suffix)]
        # Cité lui-même, ou par un dossier qui le contient (`/Game/Kit`, `/Game/Master/Statues`).
        if not any(package == prefix or package.startswith(prefix + "/") for prefix in cited):
            errors.append(f"Content/{relative} : aucun script du dépôt ne le produit "
                          "(aucun ne cite son chemin /Game/… ni un dossier qui le contient)")
    return errors


def check(root: Path = ROOT, kits: bool = True) -> list[str]:
    assets = root / "Source" / "Elements" / "Assets"
    atlas = root / "Source" / "Elements" / "Maps" / "world-maps.json"
    errors = check_assets(assets, asset_code(root), atlas, root / "Planning") if kits else []
    return (errors + check_scripts(root / "scripts", callers(root))
            + check_content(root / "Content", content_citations(root)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sans-kits", action="store_true",
                        help="ne pas contrôler les assets : leurs images viennent des kits")
    arguments = parser.parse_args()
    errors = check(kits=not arguments.sans_kits)
    for error in errors:
        print(f"check_orphans : {error}", file=sys.stderr)
    if errors:
        print(f"check_orphans : {len(errors)} orphelin(s) — un lot supprime ce qu'il remplace, et "
              "une sortie du moteur se régénère par script (Planning/vision/decisions.md, D-32, D-52)",
              file=sys.stderr)
        return 1
    print("check_orphans : aucun asset ni script orphelin, aucune sortie du moteur sans script")
    return 0


if __name__ == "__main__":
    sys.exit(main())
