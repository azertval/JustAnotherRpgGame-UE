# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Installe une pièce de décor dans le projet Unreal depuis sa fiche : maillage au maître en Nanite,
matière complète, textures compressées par le moteur (LOT-1019, D-52, D-53, D-55).

Script Python **d'éditeur** : il tourne dans UnrealEditor, sans fenêtre, et produit les `.uasset`
que le dépôt ne retouche jamais à la main. Relancé, il redonne les mêmes assets. Il est **la seule
chaîne** d'une pièce de décor : `build_level.py` l'appelle pour chaque maillage qu'une carte pose,
et ses options l'appellent seul pour les maîtres, une bibliothèque ou un kit.

    UnrealEditor-Cmd.exe JustAnotherRpgGame.uproject -run=pythonscript ^
        -script="<dépôt>/scripts/assetsGeneration/import_scenery_unreal.py" -unattended -nosplash -nullrhi

Options sur la ligne de commande du moteur :
    -JadgOnly=Weapons/Ironwood_Spear,Statues/Harvest_Fairy   n'installer que ces pièces
    -JadgFamily=Weapons                                      n'installer qu'une famille du maître
    -JadgLimit=3                                             s'arrêter après N pièces
    -JadgKit=Regions/…/arena-of-fate/Scene                   les pièces d'un kit, depuis son manifeste
    -JadgForce                                               réimporter même si l'asset existe

**Les fiches** (`scenery_sheets.py`) : le manifeste des maîtres
(`Source/Elements/Assets/Master/manifest.json`, retours Meshy), celui des pièces de bibliothèque
(`Source/Elements/Assets/Library/manifest.json`, Fab et Megascans, licence et identifiant), celui
d'un kit (`<kit>/Scene/manifest.json`). Pour chaque pièce :

  1. l'empreinte SHA-256 du `.glb` est vérifiée quand la fiche la donne (un maillage retouché
     n'entre pas) ;
  2. le `.glb` passe par Interchange (glTF) vers le dossier de contenu de la pièce ; le maillage
     est renommé comme la fiche le nomme, Nanite activé, la collision prise sur le maillage ;
  3. **la matière** : chaque image du `.glb` devient une texture du projet, une fois par contenu
     (`/Game/Scenery/Textures/T_<rôle>_<empreinte>` : deux pièces qui portent la même image la
     partagent), compressée par le moteur — **BC7** pour la couleur de base (sRGB) et
     l'occlusion-rugosité-métal (linéaire), **BC5** pour le relief (vert retourné : glTF est en
     repère OpenGL) ; chaque matière du `.glb` devient une instance de `M_Scenery` (ou de
     `M_SceneryMasked` pour un alpha), partagée de même (`/Game/Scenery/Materials/MI_<empreinte>`),
     avec ses facteurs glTF ; ce qu'Interchange avait produit (`Materials/`, `Textures/` de la
     pièce) est retiré.

`M_Scenery` est la matière parente, écrite ici nœud par nœud : couleur × facteur, relief, occlusion
(rouge, quand le `.glb` la déclare), rugosité (vert) × facteur, métal (bleu) × facteur, deux
faces ; utilisable en instances (`ISM`) et en Nanite — ce qui manquait à la matière glTF du moteur,
remplacée par la matière par défaut dans le jeu lancé (la carte grise du LOT-1018).

Un rapport par passage : `Saved/Jadg/scenery/<ensemble>.json` — chaque pièce, ses triangles, son
`.glb`, le poids sur disque de son maillage et de ses textures dans le projet.

Les pièces non riggées seulement. Le script sort en erreur (commandlet en -1) à la première pièce
fautive, comme `build.ps1` l'exige.
"""

from __future__ import annotations

import hashlib
import json
import re
import struct
import sys
import zlib
from pathlib import Path

import unreal

PROJECT_DIR = Path(unreal.Paths.project_dir()).resolve()
KIT_DIR = PROJECT_DIR / "Source" / "Elements" / "Assets"
MANIFEST = KIT_DIR / "Master" / "manifest.json"
LIBRARY_MANIFEST = KIT_DIR / "Library" / "manifest.json"
LIBRARY_ROOT = "/Game/Library"
CONTENT_DIR = PROJECT_DIR / "Content"
STAGING = PROJECT_DIR / "Intermediate" / "Jadg" / "scenery"
REPORTS = PROJECT_DIR / "Saved" / "Jadg" / "scenery"

SCENERY = "/Game/Scenery"
TEXTURES = f"{SCENERY}/Textures"
MATERIALS = f"{SCENERY}/Materials"
PARENT = f"{SCENERY}/Common/M_Scenery"
PARENT_MASKED = f"{SCENERY}/Common/M_SceneryMasked"
WHITE = f"{SCENERY}/Common/T_White"
WHITE_LINEAR = f"{SCENERY}/Common/T_WhiteLinear"
FLAT_NORMAL = f"{SCENERY}/Common/T_FlatNormal"
# Le numéro de la chaîne : changé, toute matière et toute instance se refont.
CHAIN_VERSION = 1
ROLE_TAGS = {"baseColor": "C", "normal": "N", "orm": "ORM"}

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scenery_sheets as sheets  # noqa: E402


def log(message: str) -> None:
    unreal.log(f"[Decor] {message}")


def fail(message: str) -> None:
    # Une exception non rattrapée fait sortir le commandlet pythonscript en -1 : c'est le code
    # d'erreur que build.ps1 attend.
    unreal.log_error(f"[Decor] {message}")
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


def assets() -> unreal.EditorAssetLibrary:
    return unreal.EditorAssetLibrary


# --- L'import du maillage ---------------------------------------------------------------------

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
        if not assets().rename_asset(mesh.get_path_name(), asset_path):
            fail(f"{glb.name} : impossible de déplacer {mesh.get_path_name()} vers {asset_path}")
        mesh = assets().load_asset(asset_path)
    return mesh


def finish(mesh: unreal.StaticMesh) -> bool:
    """Nanite et la collision prise sur le maillage lui-même ; vrai si l'asset a changé.

    Interchange construit Nanite à l'import (`bBuildNanite`) ; on l'active par la propriété si un
    réglage de projet l'avait coupé (le sous-système d'édition des maillages n'existe pas en mode
    commandlet). La marche et le clic se font sur le maillage : pas de collision à dessiner."""
    changed = False
    settings = mesh.get_editor_property("nanite_settings")
    if not settings.enabled:
        settings.enabled = True
        mesh.set_editor_property("nanite_settings", settings)
        if not mesh.get_editor_property("nanite_settings").enabled:
            fail(f"{mesh.get_name()} : Nanite refusé")
        changed = True
    body = mesh.get_editor_property("body_setup")
    if body is not None and body.get_editor_property("collision_trace_flag") != unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE:
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        changed = True
    return changed


# --- Les matières parentes et leurs textures par défaut ---------------------------------------

def png_rgba(width: int, height: int, pixel: tuple[int, int, int, int]) -> bytes:
    raw = b"".join(b"\x00" + bytes(pixel) * width for _ in range(height))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def import_image(content: bytes, extension: str, path: str, role: str) -> unreal.Texture2D:
    """Une image en texture du projet, réglée pour son rôle, sauvée."""
    folder, name = path.rsplit("/", 1)
    source = STAGING / "images" / f"{name}.{extension}"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(content)
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = folder
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = False
    task.set_editor_property("async_", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = assets().load_asset(path)
    if not isinstance(texture, unreal.Texture2D):
        fail(f"{path} : l'import de l'image n'a pas donné une texture")
    if role == "normal":
        texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        texture.set_editor_property("srgb", False)
        texture.set_editor_property("flip_green_channel", True)
        texture.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD_NORMAL_MAP)
    else:
        texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_BC7)
        texture.set_editor_property("srgb", role == "baseColor")
        texture.set_editor_property("flip_green_channel", False)
        texture.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
    assets().save_asset(path, only_if_is_dirty=False)
    return texture


def default_texture(path: str, pixel: tuple[int, int, int, int], role: str) -> unreal.Texture2D:
    if assets().does_asset_exist(path):
        return assets().load_asset(path)
    return import_image(png_rgba(4, 4, pixel), "png", path, role)


def parent_material(masked: bool) -> unreal.Material:
    """La matière parente d'une pièce : refaite si elle manque ou si la chaîne a changé."""
    path = PARENT_MASKED if masked else PARENT
    library = unreal.MaterialEditingLibrary
    if assets().does_asset_exist(path):
        material = assets().load_asset(path)
        if library.get_material_default_scalar_parameter_value(material, "JadgChain") == CHAIN_VERSION:
            return material
    else:
        folder, name = path.rsplit("/", 1)
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.Material,
                                                                           unreal.MaterialFactoryNew())
    white = default_texture(WHITE, (255, 255, 255, 255), "baseColor")
    white_linear = default_texture(WHITE_LINEAR, (255, 255, 255, 255), "orm")
    flat = default_texture(FLAT_NORMAL, (128, 128, 255, 255), "normal")
    library.delete_all_material_expressions(material)

    def node(kind, x: int, y: int):
        return library.create_material_expression(material, kind, x, y)

    def texture(name: str, default, sampler, y: int):
        sample = node(unreal.MaterialExpressionTextureSampleParameter2D, -900, y)
        sample.set_editor_property("parameter_name", name)
        sample.set_editor_property("texture", default)
        sample.set_editor_property("sampler_type", sampler)
        return sample

    def scalar(name: str, value: float, y: int):
        parameter = node(unreal.MaterialExpressionScalarParameter, -900, y)
        parameter.set_editor_property("parameter_name", name)
        parameter.set_editor_property("default_value", value)
        return parameter

    def multiply(a, a_pin: str, b, b_pin: str, y: int):
        product = node(unreal.MaterialExpressionMultiply, -400, y)
        library.connect_material_expressions(a, a_pin, product, "A")
        library.connect_material_expressions(b, b_pin, product, "B")
        return product

    base = texture("BaseColor", white, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, 0)
    factor = node(unreal.MaterialExpressionVectorParameter, -900, 250)
    factor.set_editor_property("parameter_name", "BaseColorFactor")
    factor.set_editor_property("default_value", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
    colour = multiply(base, "RGB", factor, "RGB", 0)
    library.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)

    normal = texture("Normal", flat, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, 500)
    library.connect_material_property(normal, "RGB", unreal.MaterialProperty.MP_NORMAL)

    orm = texture("ORM", white_linear, unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR, 800)
    one = node(unreal.MaterialExpressionConstant, -600, 750)
    one.set_editor_property("r", 1.0)
    occlusion = node(unreal.MaterialExpressionLinearInterpolate, -400, 800)
    library.connect_material_expressions(one, "", occlusion, "A")
    library.connect_material_expressions(orm, "R", occlusion, "B")
    library.connect_material_expressions(scalar("OcclusionStrength", 0.0, 1050), "", occlusion, "Alpha")
    library.connect_material_property(occlusion, "", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    rough = multiply(orm, "G", scalar("RoughnessFactor", 1.0, 1150), "", 1000)
    library.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    metal = multiply(orm, "B", scalar("MetallicFactor", 1.0, 1250), "", 1200)
    library.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    scalar("JadgChain", float(CHAIN_VERSION), 1400)

    if masked:
        opacity = multiply(base, "A", factor, "A", 300)
        library.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY_MASK)
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    else:
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    material.set_editor_property("two_sided", True)
    # Ce que la matière glTF du moteur n'avait pas : les pièces posées en instances, et Nanite.
    material.set_editor_property("used_with_instanced_static_meshes", True)
    material.set_editor_property("used_with_nanite", True)
    library.recompile_material(material)
    assets().save_asset(path, only_if_is_dirty=False)
    log(f"matière parente écrite : {path}")
    return material


# --- La matière d'une pièce -------------------------------------------------------------------

def texture_for(image: dict, role: str) -> unreal.Texture2D:
    """La texture du projet d'une image du .glb : une par contenu et par rôle."""
    path = f"{TEXTURES}/T_{ROLE_TAGS[role]}_{image['sha256'][:16]}"
    if assets().does_asset_exist(path):
        return assets().load_asset(path)
    extension = "png" if image["mime"] == "image/png" else "jpg"
    return import_image(image["content"], extension, path, role)


def instance_for(slot: dict) -> unreal.MaterialInstanceConstant:
    """L'instance de matière d'une matière du .glb : une par contenu (images, facteurs, alpha)."""
    textures = {role: texture_for(image, role) for role, image in slot["images"].items()}
    key = {
        "chain": CHAIN_VERSION,
        "alpha": slot["alpha"],
        "textures": {role: texture.get_path_name() for role, texture in sorted(textures.items())},
        "factors": [slot["baseColorFactor"], slot["metallicFactor"], slot["roughnessFactor"], slot["occlusionStrength"]],
    }
    name = "MI_" + hashlib.sha256(json.dumps(key, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    path = f"{MATERIALS}/{name}"
    if assets().does_asset_exist(path):
        return assets().load_asset(path)
    library = unreal.MaterialEditingLibrary
    instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIALS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    library.set_material_instance_parent(instance, parent_material(slot["alpha"] == "masked"))
    for role, parameter in (("baseColor", "BaseColor"), ("normal", "Normal"), ("orm", "ORM")):
        if role in textures:
            library.set_material_instance_texture_parameter_value(instance, parameter, textures[role])
    factor = slot["baseColorFactor"]
    library.set_material_instance_vector_parameter_value(instance, "BaseColorFactor", unreal.LinearColor(*factor))
    library.set_material_instance_scalar_parameter_value(instance, "MetallicFactor", slot["metallicFactor"])
    library.set_material_instance_scalar_parameter_value(instance, "RoughnessFactor", slot["roughnessFactor"])
    library.set_material_instance_scalar_parameter_value(instance, "OcclusionStrength", slot["occlusionStrength"])
    library.update_material_instance(instance)
    assets().save_asset(path, only_if_is_dirty=False)
    return instance


def match_slots(mesh: unreal.StaticMesh, slots: list[dict], label: str) -> list[dict]:
    """La matière du .glb de chaque emplacement du maillage, par son nom (Interchange nomme un
    emplacement d'après la matière glTF, `<pièce>_material_<n>` pour une matière sans nom)."""
    names = [str(m.material_slot_name) for m in mesh.static_materials]
    if len(names) == 1 and len(slots) == 1:
        return slots
    by_name = {slot["name"]: slot for slot in slots if slot["name"]}
    matched = []
    for name in names:
        slot = by_name.get(name) or by_name.get(re.sub(r"_\d{3}$", "", name))
        if slot is None:
            number = re.search(r"_material_(\d+)$", name)
            slot = slots[int(number.group(1))] if number and int(number.group(1)) < len(slots) else None
        if slot is None:
            fail(f"{label} : l'emplacement « {name} » ne se relie à aucune matière du .glb ({sorted(by_name)})")
        matched.append(slot)
    return matched


def dress(mesh: unreal.StaticMesh, glb: Path) -> bool:
    """Donne à chaque emplacement du maillage l'instance de sa matière ; retire ce qu'Interchange
    avait produit. Vrai si l'asset a changé."""
    document, binary = sheets.read_glb(glb)
    try:
        slots = sheets.material_slots(document, binary)
    except sheets.SceneryError as error:
        fail(f"{glb.name} : {error}")
    matched = match_slots(mesh, slots, glb.name)
    changed = False
    for index, slot in enumerate(matched):
        if slot["normalScale"] != 1.0:
            log(f"{glb.name} : force du relief {slot['normalScale']} ignorée (1 appliqué)")
        instance = instance_for(slot)
        current = mesh.get_material(index)
        if current is None or current.get_path_name() != instance.get_path_name():
            mesh.set_material(index, instance)
            changed = True
    piece_folder = mesh.get_path_name().split(".")[0].rsplit("/", 2)[0]
    for leftover in ("Materials", "Textures"):
        folder = f"{piece_folder}/{leftover}"
        if assets().does_directory_exist(folder):
            if changed:
                assets().save_asset(mesh.get_path_name().split(".")[0], only_if_is_dirty=False)
            assets().delete_directory(folder)
    return changed


def install(glb: Path, asset_path: str, force: bool = False, reimport: bool = False) -> tuple[unreal.StaticMesh, bool]:
    """La pièce dans le projet : importée si elle manque (ou si `reimport`), finie, habillée.
    Rend le maillage, et vrai s'il a été importé."""
    piece_folder = asset_path.rsplit("/", 2)[0]
    imported = False
    if force or reimport or not assets().does_asset_exist(asset_path):
        if assets().does_directory_exist(piece_folder):
            assets().delete_directory(piece_folder)
        mesh = import_glb(glb, piece_folder.rsplit("/", 1)[0], piece_folder, asset_path)
        imported = True
    else:
        mesh = assets().load_asset(asset_path)
    changed = finish(mesh)
    changed = dress(mesh, glb) or changed
    if changed or imported:
        assets().save_asset(asset_path, only_if_is_dirty=False)
    return mesh, imported


# --- Le poids ---------------------------------------------------------------------------------

def disk_bytes(package: str) -> int:
    """Le poids sur disque d'un paquet du projet (`.uasset` et ses `.ubulk`, `.uexp`)."""
    stem = CONTENT_DIR / package.removeprefix("/Game/")
    return sum(path.stat().st_size for path in stem.parent.glob(stem.name + ".*") if path.is_file())


def weigh(mesh: unreal.StaticMesh, glb: Path) -> dict:
    asset = mesh.get_path_name().split(".")[0]
    textures = set()
    for index in range(len(mesh.static_materials)):
        material = mesh.get_material(index)
        if isinstance(material, unreal.MaterialInstance):
            for parameter in unreal.MaterialEditingLibrary.get_texture_parameter_names(material):
                texture = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(material, parameter)
                if texture is not None and texture.get_path_name().startswith(TEXTURES):
                    textures.add(texture.get_path_name().split(".")[0])
    return {
        "asset": asset,
        "triangles": mesh.get_num_nanite_triangles() or mesh.get_num_triangles(0),
        "glbBytes": glb.stat().st_size,
        "meshBytes": disk_bytes(asset),
        "textures": sorted(textures),
        "textureBytes": sum(disk_bytes(t) for t in textures),
    }


# --- Les fiches -------------------------------------------------------------------------------

def kit_pieces(kit: str) -> list[dict]:
    """Les fiches d'un kit (`<kit>/manifest.json`), au chemin de contenu que `build_level.py` leur donne."""
    folder = KIT_DIR / kit
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    parts = [p for p in Path(kit).parts if p != "Scene"]
    pieces = []
    for key, entry in sorted(manifest.get("textures", {}).items()):
        if not isinstance(entry, dict) or "mesh" not in entry:
            continue
        stem = Path(entry["mesh"]).stem
        pieces.append({**entry, "id": key, "file": (Path(kit) / entry["mesh"]).as_posix(),
                       "asset": "/".join(["/Game/Kit", *parts, stem, "StaticMeshes", f"SM_{stem}"])})
    return pieces


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
            fail(f"pièces absentes des fiches : {sorted(missing)}")
    if family:
        chosen = [p for p in chosen if str(p.get("family", "")).lower() == family.lower()]
    if limit:
        chosen = chosen[: int(limit)]
    return chosen


def main() -> None:
    kit = command_line_option("JadgKit")
    if kit:
        label = kit.replace("/", "-")
        pieces = kit_pieces(kit)
    else:
        label = "maitres"
        if not MANIFEST.exists():
            fail(f"manifeste absent : {MANIFEST} (lancer build_master_manifest.py)")
        pieces = json.loads(MANIFEST.read_text(encoding="utf-8"))["pieces"]
        try:
            for piece in sheets.library_manifest(LIBRARY_MANIFEST):
                pieces.append({**piece, "asset": f"{LIBRARY_ROOT}/{piece['id']}/StaticMeshes/SM_{Path(piece['file']).stem}"})
        except sheets.SceneryError as error:
            fail(f"bibliothèque : {error}")
    pieces = select_pieces(pieces)
    errors = [e for piece in pieces for e in sheets.validate(sheets.sheet_of(piece))]
    if errors:
        fail(" ; ".join(errors))
    force = command_line_option("JadgForce") is not None
    log(f"{len(pieces)} pièce(s) à installer ({label})")

    imported = 0
    report = []
    for piece in pieces:
        glb = KIT_DIR / piece["file"]
        if not glb.exists():
            fail(f"{piece['id']} : fichier absent {glb}")
        if "sha256" in piece and sha256_of(glb) != piece["sha256"]:
            fail(f"{piece['id']} : empreinte différente de la fiche, le .glb a changé")
        mesh, fresh = install(glb, piece["asset"], force=force)
        imported += fresh
        report.append({"id": piece["id"], **weigh(mesh, glb)})
        log(f"{piece['id']} : {report[-1]['triangles']} triangles" + (" (importée)" if fresh else ""))

    REPORTS.mkdir(parents=True, exist_ok=True)
    textures = sorted({t for entry in report for t in entry["textures"]})
    summary = {
        "set": label,
        "pieces": len(report),
        "glbBytes": sum(e["glbBytes"] for e in report),
        "meshBytes": sum(e["meshBytes"] for e in report),
        "textures": len(textures),
        "textureBytes": sum(disk_bytes(t) for t in textures),
        "largest": max(report, key=lambda e: e["triangles"])["id"] if report else None,
        "detail": report,
    }
    (REPORTS / f"{label}.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    log(f"terminé : {imported} importée(s), {len(report) - imported} déjà présente(s) ; "
        f"{len(textures)} texture(s) ; rapport Saved/Jadg/scenery/{label}.json")


if __name__ == "__main__":
    main()
