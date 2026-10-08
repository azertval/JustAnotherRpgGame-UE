#!/usr/bin/env python3
"""Pose le mannequin d'Unreal et ses animations dans le projet (LOT-1015, D-63, D-64).

Le moteur livre, dans `Templates/TemplateResources/High/Characters/Content/Mannequins/`, un
mannequin (Manny, Quinn, leur squelette `SK_Mannequin`), ses matières, ses textures, son asset
de physique et un jeu d'animations. C'est la première source de corps et de clips de la version
(D-63 : « le contenu livré avec le moteur reste la première source »). Les assets y sont rangés
sous `/Game/Characters/Mannequins/…` : copiés au même chemin relatif sous `Content/`, leurs
références entre eux restent valides, sans import ni geste dans l'éditeur.

Ce qui vient, et rien d'autre :

- `Meshes/` (SKM_Manny_Simple, SKM_Quinn_Simple, SK_Mannequin), `Materials/`, `Textures/`,
  `Rigs/` (PA_Mannequin, les Control Rigs que le squelette cite) ;
- six clips, un par clip du jeu : repos, marche, attaque, incantation, coup reçu, mort
  (`CLIPS` ci-dessous ; l'incantation est l'attaque chargée du mannequin, faute d'un clip de sort
  dans le contenu du moteur).

Rejoué, le script ne copie que ce qui manque ou diffère (empreinte SHA-256), et ne retouche
jamais une copie. La description du créateur (`Source/Elements/Assets/Characters/humanoid.json`)
nomme ces assets ; `check_orphans.py` les retrouve par là.

    python scripts/assetsGeneration/import_mannequin_unreal.py --engine "E:\\Epic Games\\UE_5.8"
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "Content"
# Le chemin des assets dans le moteur et dans le projet : le même, pour que les références tiennent.
RELATIVE = Path("Characters/Mannequins")
SOURCE_IN_ENGINE = Path("Templates/TemplateResources/High/Characters/Content/Mannequins")

FOLDERS = ("Meshes", "Materials", "Textures", "Rigs")

# Un clip du jeu -> l'animation du mannequin qui le joue, sous `Anims/`.
CLIPS = {
    "idle": "Unarmed/MM_Idle",
    "walk": "Unarmed/Walk/MF_Unarmed_Walk_Fwd",
    "attack": "Unarmed/Attack/MM_Attack_01",
    "cast": "Unarmed/Attack/MM_ChargedAttack",
    "hit": "Rifle/HitReact/MM_HitReact_Front_Med_01",
    "death": "Death/MM_Death_Front_01",
}


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def engine_dir(argument: str | None) -> Path:
    """Le dossier du moteur : l'argument, sinon celui de l'éditeur qui exécute ce script."""
    if argument:
        return Path(argument)
    try:
        import unreal  # noqa: PLC0415 — n'existe que sous l'éditeur

        return Path(unreal.Paths.engine_dir()).resolve().parent
    except ImportError:
        sys.exit("import_mannequin_unreal : --engine est requis hors de l'éditeur")


def wanted_files(source: Path) -> list[Path]:
    files: list[Path] = []
    for folder in FOLDERS:
        files.extend(sorted((source / folder).rglob("*.uasset")))
    for clip in CLIPS.values():
        files.append(source / "Anims" / f"{clip}.uasset")
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--engine", help="dossier du moteur (contient Engine/ et Templates/)")
    args = parser.parse_args()

    source = engine_dir(args.engine) / SOURCE_IN_ENGINE
    if not source.is_dir():
        sys.exit(f"import_mannequin_unreal : mannequin absent du moteur : {source}")
    target = CONTENT / RELATIVE

    copied = kept = 0
    for file in wanted_files(source):
        if not file.is_file():
            sys.exit(f"import_mannequin_unreal : fichier absent du moteur : {file}")
        destination = target / file.relative_to(source)
        if destination.is_file() and sha256_of(destination) == sha256_of(file):
            kept += 1
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(file, destination)
        copied += 1
    print(f"import_mannequin_unreal : {copied} copié(s), {kept} déjà à jour, sous {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
