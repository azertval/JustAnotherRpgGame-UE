# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Importe les maillages au maître dans le projet Unreal, en Nanite, depuis le manifeste du kit.

Script Python **d'éditeur** (D-52) : il tourne dans UnrealEditor, sans fenêtre, et produit les
`.uasset` que le dépôt ne retouche jamais à la main. Relancé, il redonne les mêmes assets.

    UnrealEditor-Cmd.exe JustAnotherRpgGame.uproject -run=pythonscript ^
        -script="scripts/assetsGeneration/import_master_unreal.py" -unattended -nosplash -nullrhi

Options sur la ligne de commande du moteur :
    -JadgOnly=Weapons/Ironwood_Spear,Statues/Harvest_Fairy   n'importer que ces pièces
    -JadgFamily=Weapons                                      n'importer qu'une famille
    -JadgLimit=3                                             s'arrêter après N pièces
    -JadgForce                                               réimporter même si l'asset existe

Pour chaque pièce du manifeste (`Source/Elements/Assets/Master/manifest.json`) :
  1. l'empreinte SHA-256 du `.glb` est vérifiée (un maillage retouché n'entre pas) ;
  2. le `.glb` passe par Interchange (glTF) vers le dossier de contenu de la pièce ;
  3. le maillage statique obtenu est renommé comme le manifeste le nomme, Nanite activé ;
  4. tout ce que l'import a produit (maillage, matière, textures) est sauvé.

Les pièces non riggées seulement : un personnage lié passe par `import_character_unreal.py`
(LOT-1015). Le script sort en erreur (commandlet en -1) à la première pièce fautive, comme `build.ps1` l'exige.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import unreal

PROJECT_DIR = Path(unreal.Paths.project_dir()).resolve()
MANIFEST = PROJECT_DIR / "Source" / "Elements" / "Assets" / "Master" / "manifest.json"
KIT_DIR = PROJECT_DIR / "Source" / "Elements" / "Assets"


def log(message: str) -> None:
    unreal.log(f"[Master] {message}")


def fail(message: str) -> None:
    # Une exception non rattrapée fait sortir le commandlet pythonscript en -1 : c'est le code
    # d'erreur que build.ps1 attend.
    unreal.log_error(f"[Master] {message}")
    raise RuntimeError(message)


def command_line_option(name: str) -> str | None:
    """`-Name=valeur` sur la ligne de commande du moteur, ou `-Name` seul (chaîne vide)."""
    for token in unreal.SystemLibrary.get_command_line().split():
        if token.lower() == f"-{name.lower()}":
            return ""
        prefix = f"-{name.lower()}="
        if token.lower().startswith(prefix):
            return token[len(prefix):].strip('"')
    return None


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def select_pieces(pieces: list[dict]) -> list[dict]:
    only = command_line_option("JadgOnly")
    family = command_line_option("JadgFamily")
    limit = command_line_option("JadgLimit")
    chosen = pieces
    if only:
        wanted = {item.strip() for item in only.split(",") if item.strip()}
        chosen = [p for p in chosen if p["id"] in wanted]
        missing = wanted - {p["id"] for p in chosen}
        if missing:
            fail(f"pièces absentes du manifeste : {sorted(missing)}")
    if family:
        chosen = [p for p in chosen if p["family"].lower() == family.lower()]
    if limit:
        chosen = chosen[: int(limit)]
    return chosen


def import_glb(glb: Path, family_folder: str, piece_folder: str, asset_path: str) -> unreal.StaticMesh:
    """Passe le .glb par Interchange dans `family_folder` ; Interchange crée `piece_folder`
    (le nom du fichier) et ses sous-dossiers StaticMeshes/, Materials/, Textures/."""
    task = unreal.AssetImportTask()
    task.filename = str(glb)
    task.destination_path = family_folder
    task.destination_name = asset_path.rsplit("/", 1)[1]
    task.automated = True
    task.replace_existing = True
    task.replace_existing_settings = True
    task.save = False
    task.set_editor_property("async_", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    meshes = []
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    for asset_data in registry.get_assets_by_path(piece_folder, recursive=True):
        if asset_data.asset_class_path.asset_name == "StaticMesh":
            meshes.append(asset_data.get_asset())
    if not meshes:
        fail(f"{glb.name} : aucun maillage statique importé sous {piece_folder}")
    if len(meshes) > 1:
        fail(f"{glb.name} : {len(meshes)} maillages statiques sous {piece_folder}, un seul attendu")
    mesh = meshes[0]
    if mesh.get_path_name().split(".")[0] != asset_path:
        if not unreal.EditorAssetLibrary.rename_asset(mesh.get_path_name(), asset_path):
            fail(f"{glb.name} : impossible de déplacer {mesh.get_path_name()} vers {asset_path}")
        mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
    return mesh


def enable_nanite(mesh: unreal.StaticMesh) -> None:
    """Nanite sur le maillage. Interchange le construit déjà à l'import (`bBuildNanite`) ; on le
    vérifie, et on l'active par la propriété si un réglage de projet l'avait coupé. Le
    sous-système d'édition des maillages n'existe pas en mode commandlet : la propriété, si."""
    settings = mesh.get_editor_property("nanite_settings")
    if settings.enabled:
        return
    settings.enabled = True
    mesh.set_editor_property("nanite_settings", settings)
    if not mesh.get_editor_property("nanite_settings").enabled:
        fail(f"{mesh.get_name()} : Nanite refusé")


def main() -> None:
    if not MANIFEST.exists():
        fail(f"manifeste absent : {MANIFEST} (lancer build_master_manifest.py)")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pieces = select_pieces(manifest["pieces"])
    force = command_line_option("JadgForce") is not None
    log(f"{len(pieces)} pièce(s) à importer depuis {MANIFEST}")

    imported = skipped = 0
    for piece in pieces:
        glb = KIT_DIR / piece["file"]
        asset_path = piece["asset"]  # /Game/Master/<Famille>/<Pièce>/StaticMeshes/SM_<...>
        piece_folder = asset_path.rsplit("/", 2)[0]
        family_folder = piece_folder.rsplit("/", 1)[0]
        if not glb.exists():
            fail(f"{piece['id']} : fichier absent {glb}")
        if sha256_of(glb) != piece["sha256"]:
            fail(f"{piece['id']} : empreinte différente du manifeste, le .glb a changé")
        if not force and unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
            enable_nanite(mesh)
            skipped += 1
            continue

        log(f"{piece['id']} : {piece['triangles']} triangles -> {asset_path}")
        mesh = import_glb(glb, family_folder, piece_folder, asset_path)
        enable_nanite(mesh)
        unreal.EditorAssetLibrary.save_directory(piece_folder, only_if_is_dirty=False, recursive=True)
        imported += 1

    log(f"terminé : {imported} importée(s), {skipped} déjà présente(s)")


if __name__ == "__main__":
    main()
