# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Importe les images du kit `UI` dans le projet Unreal (LOT-1020).

Script Python **d'éditeur** (D-52) : il tourne dans UnrealEditor, sans fenêtre, et produit les
`.uasset` que le dépôt ne retouche jamais à la main. Relancé sans changement, il ne réimporte rien.

    UnrealEditor-Cmd.exe JustAnotherRpgGame.uproject -run=pythonscript ^
        -script="scripts/assetsGeneration/import_ui_unreal.py" -unattended -nosplash -nullrhi

Options sur la ligne de commande du moteur :
    -JadgForce      réimporter même si l'empreinte n'a pas changé

Ce qu'il importe :

| Source | Liste | Asset |
|---|---|---|
| les images du kit `Source/Elements/Assets/UI/` | `illustrations.json` (fichier, empreinte SHA-256) | `/Game/UI/Kit/<fichier sans extension>`, texture d'interface sans mipmaps |

Les polices des écrans (`style.json`, section `fonts`) deviennent `/Game/UI/Fonts/<fichier>` par le
commandlet `JadgImportFonts`, que `build.ps1` lance juste après ce script : l'importeur de polices
du moteur demande une fenêtre et s'arrête sans elle (relevé du 9 octobre 2026).

L'empreinte de la source est gardée sur l'asset (étiquette `JadgSha256`) : une image ou une police
dont l'empreinte n'a pas changé ne se réimporte pas. Une image du manifeste absente du poste (les
kits ne sont pas suivis par Git, `scripts/fetch_assets.py` les installe) est sautée et comptée ; une
image présente dont l'empreinte diffère du manifeste arrête le script (commandlet en -1) : une image
retouchée n'entre pas. Les écrans retombent sur un aplat des couleurs du style pour ce qui manque
(`UI/JadgStyle.h`).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import unreal

PROJECT_DIR = Path(unreal.Paths.project_dir()).resolve()
UI_DIR = PROJECT_DIR / "Source" / "Elements" / "Assets" / "UI"
MANIFEST = UI_DIR / "illustrations.json"
KIT_ROOT = "/Game/UI/Kit"
# Les polices : `/Game/UI/Fonts`, écrites par le commandlet JadgImportFonts (voir plus haut).
TAG = "JadgSha256"


def log(message: str) -> None:
    unreal.log(f"[UI] {message}")


def fail(message: str) -> None:
    # Une exception non rattrapée fait sortir le commandlet pythonscript en -1.
    unreal.log_error(f"[UI] {message}")
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


def up_to_date(asset_path: str, fingerprint: str) -> bool:
    """Vrai si l'asset existe et porte l'empreinte de sa source."""
    if not unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return False
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    return unreal.EditorAssetLibrary.get_metadata_tag(asset, TAG) == fingerprint


def import_file(source: Path, asset_path: str) -> unreal.Object:
    folder, name = asset_path.rsplit("/", 1)
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = folder
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.replace_existing_settings = True
    task.save = False
    task.set_editor_property("async_", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    if not unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        fail(f"{source.name} : l'import n'a pas produit {asset_path}")
    return unreal.EditorAssetLibrary.load_asset(asset_path)


def settle_texture(texture: unreal.Texture2D) -> None:
    """Une image d'interface : sans mipmaps, compression d'interface, groupe UI, sRGB."""
    texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    texture.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    texture.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property("srgb", True)
    texture.set_editor_property("never_stream", True)


def main() -> None:
    force = command_line_option("JadgForce") is not None
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    imported = skipped = missing = 0
    saved: list[str] = []

    for entry in manifest["illustrations"]:
        source = UI_DIR / entry["file"]
        asset_path = f"{KIT_ROOT}/{entry['file'].rsplit('.', 1)[0]}"
        if not source.exists():
            missing += 1
            continue
        fingerprint = sha256_of(source)
        if fingerprint != entry["sha256"]:
            fail(f"{entry['file']} : empreinte différente du manifeste, l'image a changé")
        if not force and up_to_date(asset_path, fingerprint):
            skipped += 1
            continue
        texture = import_file(source, asset_path)
        settle_texture(texture)
        unreal.EditorAssetLibrary.set_metadata_tag(texture, TAG, fingerprint)
        saved.append(asset_path)
        imported += 1

    for asset_path in saved:
        unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False)
    log(f"terminé : {imported} importé(s), {skipped} à jour, {missing} image(s) du manifeste absente(s) du poste")


if __name__ == "__main__":
    main()
