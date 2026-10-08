# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Construit une carte Unreal depuis une description de scène en JSON (LOT-1012, D-52).

Script Python **d'éditeur** : il tourne dans UnrealEditor, sans fenêtre, et produit la carte
(`.umap`) et les assets (`.uasset`) qu'elle montre. Aucun acteur n'est posé à la main, aucun
Blueprint n'est créé ; relancé, il refait la carte entière.

    pwsh scripts/build.ps1 -Unreal -Scene porte-1012

c'est-à-dire, le chemin du script étant absolu (le moteur résout un chemin relatif depuis ses
propres binaires) :

    UnrealEditor-Cmd.exe JustAnotherRpgGame.uproject -run=pythonscript ^
        -script="<dépôt>/scripts/maps/build_scene_unreal.py" -unattended -nosplash -nullrhi

Options sur la ligne de commande du moteur :
    -JadgScene=porte-1012     la description, sous Source/Elements/Scenes/ (défaut : porte-1012)

La description (`Source/Elements/Scenes/<scène>.json`) est l'embryon du format de carte du
LOT-1018. Son repère est celui d'un .glb posé : X vers l'est, Y vers le haut, Z vers le sud, en
mètres. Elle porte :

- `groups` : d'autres fichiers d'objets, posés d'un bloc (le Colisée, écrit par
  `build_gate_scene.py`) ;
- `fills` : un dallage, tiré case par case entre plusieurs dalles, hors des ellipses qu'il exclut ;
- `objects` : un maillage, sa position, son lacet, son échelle (ou sa hauteur) ; une source de
  lumière, déclarée comme dans les manifestes de scène de l'ancien moteur (`light`) ;
- `characters` : un personnage lié, ses clips de repos et de marche, sa ronde ;
- `navigation`, `shots`, `daylight` : le volume de navigation, les cadrages de capture, la table
  du jour ;
- `frameReference` : la pièce sur laquelle le changement de repère se mesure ;
- `assetsRoot` (facultatif) : le dossier, relatif au dépôt, où se lisent les maillages de la
  scène, à la place des kits. La scène du socle (`socle-1014`, LOT-1014) lit ainsi les données
  d'essai suivies par Git (`Source/Test/Fixtures/Meshes/Assets`) : elle se construit sur un poste
  sans kit, et ses assets vont sous `/Game/Fixtures/…`.

Ce que le script fait, dans l'ordre :

  1. chaque maillage cité est importé par Interchange s'il ne l'est pas déjà — un maître par son
     manifeste, empreinte vérifiée (`import_master_unreal.py`), une pièce de kit sous
     `/Game/Kit/…`, un personnage avec son squelette et ses clips — Nanite actif, la collision
     prise sur le maillage lui-même ;
  2. **le changement de repère est mesuré, pas supposé** : la boîte englobante de la première
     pièce importée, lue dans son .glb, est comparée à celle de l'asset ; le script en tire ce
     que chaque axe devient dans le moteur et s'arrête s'il ne peut pas le dire ;
  3. une carte vide est créée, les acteurs y sont posés, puis le soleil, le ciel, la lumière du
     ciel (un cube blanc, que la table du jour teinte), l'exposition fixe, la navigation, les
     cadrages, le mode de jeu ;
  4. la carte est sauvée sous le chemin que la description nomme (`map`).

Le script sort en erreur (commandlet en -1) à la première pièce fautive.
"""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

import unreal

PROJECT_DIR = Path(unreal.Paths.project_dir()).resolve()
ELEMENTS = PROJECT_DIR / "Source" / "Elements"
ASSETS = ELEMENTS / "Assets"
SCENES = ELEMENTS / "Scenes"

sys.path.insert(0, str(PROJECT_DIR / "scripts" / "assetsGeneration"))
import import_master_unreal as master_import  # noqa: E402

KIT_ROOT = "/Game/Kit"
FIXTURE_ROOT = "/Game/Fixtures"
AMBIENT_CUBE = "/Game/Scenes/Common/T_AmbientWhite"
CHARACTER_MATERIAL = "/Game/Scenes/Common/M_Character"
GROUND_MATERIAL = "/Game/Scenes/Common/M_Ground"
GAME_CLASSES = "/Script/JustAnotherRpgGame"
LAMP_TAG = "JadgLamp"


def log(message: str) -> None:
    unreal.log(f"[Scene] {message}")


def fail(message: str) -> None:
    unreal.log_error(f"[Scene] {message}")
    raise RuntimeError(message)


# --- La description ---------------------------------------------------------------------------

def turn(point: list[float], yaw: float) -> list[float]:
    """`point` tourné de `yaw` degrés autour de +Y (repère direct : +Z tourne vers +X)."""
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return [c * point[0] + s * point[2], point[1], -s * point[0] + c * point[2]]


def cell_choice(i: int, j: int, count: int) -> int:
    """Le tirage d'une dalle pour la case (i, j) : le même à chaque construction."""
    return ((i * 73856093) ^ (j * 19349663)) % count


def load_scene(name: str) -> dict:
    path = SCENES / f"{name}.json"
    if not path.exists():
        fail(f"description absente : {path}")
    scene = json.loads(path.read_text(encoding="utf-8"))
    objects: list[dict] = []
    for group in scene.get("groups", ()):
        content = json.loads((SCENES / group["file"]).read_text(encoding="utf-8"))
        # Un groupe se pose d'un bloc : tourné, mis à l'échelle (`scale`), puis déplacé.
        size = group.get("scale", 1.0)
        for item in content["objects"]:
            placed = dict(item)
            moved = turn([v * size for v in item["position"]], group.get("yaw", 0.0))
            placed["position"] = [moved[k] + group["position"][k] for k in range(3)]
            placed["yaw"] = item.get("yaw", 0.0) + group.get("yaw", 0.0)
            placed["scale"] = item.get("scale", 1.0) * size
            placed["groupScale"] = size
            placed["id"] = f"{group['id']}/{item['id']}"
            placed["folder"] = group["id"]
            objects.append(placed)
    for fill in scene.get("fills", ()):
        cell = fill["cell"]
        # Les cases qu'un sol déjà posé occupe (`except` : un préfixe d'identifiant) restent à lui.
        # Une dalle de sol fait une case à l'échelle 1 : agrandie, elle en couvre plusieurs.
        seen: set[tuple[int, int]] = set()
        for o in objects:
            if "except" in fill and o["id"].startswith(fill["except"]):
                # Sont à lui les cases dont le centre tombe sous la dalle.
                half = cell * o.get("scale", 1.0) / 2
                x, z = o["position"][0], o["position"][2]
                for i in range(math.ceil((x - half) / cell - 0.5), math.floor((x + half) / cell - 0.5) + 1):
                    for j in range(math.ceil((z - half) / cell - 0.5), math.floor((z + half) / cell - 0.5) + 1):
                        seen.add((i, j))
        # Les cases sous une ellipse exclue (le Colisée : centre, demi-axes, en mètres) restent vides.
        ellipses = fill.get("excludeEllipses", ())
        for x0, z0, x1, z1 in fill["areas"]:
            for i in range(round(x0 / cell), round(x1 / cell)):
                for j in range(round(z0 / cell), round(z1 / cell)):
                    x, z = (i + 0.5) * cell, (j + 0.5) * cell
                    if (i, j) in seen:
                        continue
                    if any(((x - cx) / a) ** 2 + ((z - cz) / b) ** 2 < 1.0 for cx, cz, a, b in ellipses):
                        continue
                    seen.add((i, j))
                    objects.append({"id": f"{fill['id']}/{i},{j}", "folder": fill["id"],
                                    "mesh": fill["meshes"][cell_choice(i, j, len(fill["meshes"]))],
                                    "position": [x, 0.0, z], "yaw": 0.0, "scale": 1.0})
    for item in scene.get("objects", ()):
        objects.append({"folder": "parvis", **item})
    scene["placed"] = objects
    return scene


# --- Les assets -------------------------------------------------------------------------------

def glb_bounds(path: Path) -> tuple[list[float], list[float]]:
    """La boîte englobante d'un .glb à un seul maillage non transformé, lue dans son en-tête."""
    with path.open("rb") as stream:
        stream.read(12)
        length, _ = struct.unpack("<II", stream.read(8))
        document = json.loads(stream.read(length))
    nodes = [n for n in document["nodes"] if "mesh" in n]
    if len(nodes) != 1 or any(k in nodes[0] for k in ("matrix", "rotation", "scale", "translation")):
        fail(f"{path.name} : un seul maillage sans transformation attendu pour mesurer le repère")
    low, high = [math.inf] * 3, [-math.inf] * 3
    for primitive in document["meshes"][nodes[0]["mesh"]]["primitives"]:
        accessor = document["accessors"][primitive["attributes"]["POSITION"]]
        low = [min(low[k], accessor["min"][k]) for k in range(3)]
        high = [max(high[k], accessor["max"][k]) for k in range(3)]
    return low, high


class Frame:
    """Ce que deviennent, dans le moteur, les axes d'un .glb : mesuré sur une pièce importée."""

    def __init__(self, glb: Path, mesh: unreal.StaticMesh) -> None:
        low, high = glb_bounds(glb)
        box = mesh.get_bounding_box()
        ue_low = [box.min.x, box.min.y, box.min.z]
        ue_high = [box.max.x, box.max.y, box.max.z]
        # axes[k] = (i, s) : l'axe k du moteur est l'axe i du .glb, de signe s, en centimètres.
        self.axes: list[tuple[int, float]] = []
        for k in range(3):
            matches = []
            for i in range(3):
                for sign in (1.0, -1.0):
                    a, b = (low[i], high[i]) if sign > 0 else (-high[i], -low[i])
                    if abs(ue_low[k] - a * 100.0) < 2.0 and abs(ue_high[k] - b * 100.0) < 2.0:
                        matches.append((i, sign))
            if len(matches) != 1:
                fail(f"repère : l'axe {'XYZ'[k]} du moteur ne se lit pas sur {glb.name} "
                     f"({len(matches)} correspondances ; .glb {low} {high}, moteur {ue_low} {ue_high})")
            self.axes.append(matches[0])
        if self.axes[2] != (1, 1.0) or {self.axes[0][0], self.axes[1][0]} != {0, 2}:
            fail(f"repère inattendu : {self.axes} (le haut du .glb, +Y, devrait être +Z du moteur)")
        log(f"repère mesuré sur {glb.name} : X moteur = {self.describe(0)}, Y = {self.describe(1)}, "
            f"Z = {self.describe(2)}")

    def describe(self, k: int) -> str:
        i, sign = self.axes[k]
        return f"{'+' if sign > 0 else '-'}{'XYZ'[i]} du .glb"

    def direction(self, vector: list[float]) -> unreal.Vector:
        return unreal.Vector(*[sign * vector[i] for i, sign in self.axes])

    def point(self, metres: list[float]) -> unreal.Vector:
        return unreal.Vector(*[sign * metres[i] * 100.0 for i, sign in self.axes])

    def yaw(self, degrees: float) -> float:
        """Le lacet du moteur qui vaut une rotation de `degrees` autour de +Y dans le .glb."""
        (ix, a), (_, b) = self.axes[0], self.axes[1]
        return (-degrees if ix == 0 else degrees) * a * b

    def mirror_scale(self, scale: float) -> unreal.Vector:
        """L'échelle d'une pièce en miroir : l'axe X du .glb est retourné."""
        return unreal.Vector(*[-scale if i == 0 else scale for i, _ in self.axes])

    def look(self, heading: float, pitch: float = 0.0) -> unreal.Rotator:
        """Le regard d'une boussole (0 = nord, 90 = est), `pitch` degrés sous l'horizon."""
        h, p = math.radians(heading), math.radians(pitch)
        toward = [math.sin(h) * math.cos(p), -math.sin(p), -math.cos(h) * math.cos(p)]
        return unreal.MathLibrary.find_look_at_rotation(unreal.Vector(0, 0, 0), self.direction(toward))


def kit_folder(mesh: str, root: str = KIT_ROOT) -> str:
    """`Regions/…/arena-of-fate/Scene/af-pyre.glb` → `/Game/Kit/Regions/…/arena-of-fate`."""
    parts = [p for p in Path(mesh).parent.parts if p != "Scene"]
    return "/".join([root, *parts])


class Library:
    """Les assets de la scène : importés une fois, relus ensuite.

    Une pièce **construite par script** (`Built/…`, `build_colosseum.py`) change quand son script
    change : l'empreinte du `.glb` importé est notée (`Intermediate/Jadg/imports.json`), et une
    pièce dont l'empreinte diffère est réimportée ; de même une donnée d'essai (`assetsRoot`,
    `build_mesh_fixture.py`). Un maître ne change jamais (son manifeste le vérifie) ; une pièce de
    kit ne change qu'avec le verrou des kits."""

    def __init__(self, assets_root: str | None = None) -> None:
        # Les maillages de la scène : les kits, ou le dossier que la description nomme.
        self.assets = PROJECT_DIR / assets_root if assets_root else ASSETS
        self.content_root = FIXTURE_ROOT if assets_root else KIT_ROOT
        manifest = json.loads(master_import.MANIFEST.read_text(encoding="utf-8"))
        self.master = {piece["file"]: piece for piece in manifest["pieces"]}
        self.static: dict[str, unreal.StaticMesh] = {}
        self.imported = 0
        self.imports_file = PROJECT_DIR / "Intermediate" / "Jadg" / "imports.json"
        self.imports: dict[str, str] = (json.loads(self.imports_file.read_text(encoding="utf-8"))
                                        if self.imports_file.exists() else {})

    def static_mesh(self, mesh: str) -> unreal.StaticMesh:
        if mesh in self.static:
            return self.static[mesh]
        glb = self.assets / mesh
        if not glb.exists():
            fail(f"{mesh} : fichier absent (kits : python scripts/fetch_assets.py ; "
                 f"Colisée : python scripts/assetsGeneration/build_colosseum.py)")
        scripted = mesh.startswith("Built/") or self.assets != ASSETS
        piece = None if self.assets != ASSETS else self.master.get(mesh)
        stale = False
        if piece is not None:
            asset_path = piece["asset"]
            if master_import.sha256_of(glb) != piece["sha256"]:
                fail(f"{mesh} : empreinte différente du manifeste du maître")
        elif mesh.startswith("Master/") and not scripted:
            fail(f"{mesh} : absent du manifeste du maître")
        else:
            asset_path = f"{kit_folder(mesh, self.content_root)}/{glb.stem}/StaticMeshes/SM_{glb.stem}"
            if scripted:
                digest = master_import.sha256_of(glb)
                stale = self.imports.get(asset_path) != digest
                self.imports[asset_path] = digest
        piece_folder = asset_path.rsplit("/", 2)[0]
        if unreal.EditorAssetLibrary.does_asset_exist(asset_path) and not stale:
            asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        else:
            log(f"import de {mesh} -> {asset_path}" + (" (pièce régénérée)" if stale else ""))
            if unreal.EditorAssetLibrary.does_directory_exist(piece_folder):
                unreal.EditorAssetLibrary.delete_directory(piece_folder)
            asset = master_import.import_glb(glb, piece_folder.rsplit("/", 1)[0], piece_folder, asset_path)
            self.imported += 1
            self.imports_file.parent.mkdir(parents=True, exist_ok=True)
            self.imports_file.write_text(json.dumps(self.imports, indent=1), encoding="utf-8")
        master_import.enable_nanite(asset)
        # La marche et le clic se font sur le maillage lui-même : pas de collision simplifiée à
        # dessiner à la main.
        body = asset.get_editor_property("body_setup")
        if body.get_editor_property("collision_trace_flag") != unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE:
            body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            unreal.EditorAssetLibrary.save_directory(piece_folder, only_if_is_dirty=False, recursive=True)
        self.static[mesh] = asset
        return asset

    def character(self, mesh: str) -> tuple[unreal.SkeletalMesh, list, dict[str, unreal.AnimSequence]]:
        """Le maillage lié d'un personnage, ses matières (une par emplacement) et ses clips, par nom."""
        glb = self.assets / mesh
        if not glb.exists():
            fail(f"{mesh} : fichier absent (kits : python scripts/fetch_assets.py)")
        parent = kit_folder(mesh, self.content_root)
        folder = f"{parent}/{glb.stem}"
        registry = unreal.AssetRegistryHelpers.get_asset_registry()

        def find(class_name: str) -> list:
            return [data.get_asset() for data in registry.get_assets_by_path(folder, recursive=True)
                    if data.asset_class_path.asset_name == class_name]

        if not find("SkeletalMesh"):
            log(f"import de {mesh} -> {folder}")
            task = unreal.AssetImportTask()
            task.filename = str(glb)
            task.destination_path = parent
            task.automated = True
            task.replace_existing = True
            task.replace_existing_settings = True
            task.save = False
            task.set_editor_property("async_", False)
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            unreal.EditorAssetLibrary.save_directory(folder, only_if_is_dirty=False, recursive=True)
            self.imported += 1
        meshes = find("SkeletalMesh")
        if len(meshes) != 1:
            fail(f"{mesh} : {len(meshes)} maillage(s) lié(s) sous {folder}, un seul attendu")
        skins = self.skin_materials(meshes[0], folder, glb.stem)
        clips = {clip.get_name(): clip for clip in find("AnimSequence")}
        log(f"{glb.stem} : {meshes[0].get_name()}, clips {sorted(clips)}")
        return meshes[0], skins, clips


    @staticmethod
    def skin_materials(skeletal: unreal.SkeletalMesh, folder: str, stem: str) -> list:
        """Les matières d'un maillage lié qui s'appliquent à un maillage lié, une par emplacement.

        Interchange range la matière d'un .glb sous une matière du moteur (`M_GLTF`) qui n'est pas
        compilée pour les maillages liés : dans l'éditeur elle se recompile à la volée, dans le jeu
        elle est remplacée par la matière par défaut, et le personnage sort sans sa texture. Chaque
        emplacement a donc une instance de `M_Character`, avec la carte de couleur que l'import a
        trouvée ; l'acteur la porte (`place_characters`), l'asset importé n'est pas retouché.
        """
        library = unreal.MaterialEditingLibrary
        parent = character_material()
        skins = []
        for index, slot in enumerate(skeletal.materials):
            current = slot.material_interface
            if current is None:
                fail(f"{stem} : emplacement de matière {index} vide")
            texture = library.get_material_instance_texture_parameter_value(current, "BaseColorTexture")
            if texture is None:
                fail(f"{stem} : la matière {current.get_name()} n'a pas de carte de couleur")
            name = f"MI_{stem}_{index}"
            path = f"{folder}/Materials/{name}"
            instance = (unreal.EditorAssetLibrary.load_asset(path)
                        if unreal.EditorAssetLibrary.does_asset_exist(path)
                        else unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                            name, f"{folder}/Materials", unreal.MaterialInstanceConstant,
                            unreal.MaterialInstanceConstantFactoryNew()))
            library.set_material_instance_parent(instance, parent)
            library.set_material_instance_texture_parameter_value(instance, "BaseColorTexture", texture)
            library.update_material_instance(instance)
            unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
            skins.append(instance)
        return skins


def new_material(path: str) -> unreal.Material:
    folder, name = path.rsplit("/", 1)
    return unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, folder, unreal.Material, unreal.MaterialFactoryNew())


def character_material() -> unreal.Material:
    """La matière des personnages liés : une carte de couleur, mate, sans métal — ce que porte un
    `.glb` de la chaîne des personnages (`rig_character.py`)."""
    if unreal.EditorAssetLibrary.does_asset_exist(CHARACTER_MATERIAL):
        return unreal.EditorAssetLibrary.load_asset(CHARACTER_MATERIAL)
    library = unreal.MaterialEditingLibrary
    material = new_material(CHARACTER_MATERIAL)
    colour = library.create_material_expression(material, unreal.MaterialExpressionTextureSampleParameter2D, -400, 0)
    colour.set_editor_property("parameter_name", "BaseColorTexture")
    library.connect_material_property(colour, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = library.create_material_expression(material, unreal.MaterialExpressionScalarParameter, -400, 300)
    rough.set_editor_property("parameter_name", "Roughness")
    rough.set_editor_property("default_value", 1.0)
    library.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    material.set_editor_property("used_with_skeletal_mesh", True)
    library.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(CHARACTER_MATERIAL)
    return material


def ground_material(colour: unreal.LinearColor) -> unreal.Material:
    """La matière du sol lointain : une couleur unie et mate."""
    library = unreal.MaterialEditingLibrary
    material = (unreal.EditorAssetLibrary.load_asset(GROUND_MATERIAL)
                if unreal.EditorAssetLibrary.does_asset_exist(GROUND_MATERIAL) else new_material(GROUND_MATERIAL))
    library.delete_all_material_expressions(material)
    tint = library.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -400, 0)
    tint.set_editor_property("constant", colour)
    library.connect_material_property(tint, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = library.create_material_expression(material, unreal.MaterialExpressionConstant, -400, 300)
    rough.set_editor_property("r", 1.0)
    library.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    library.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(GROUND_MATERIAL)
    return material


def clip_named(clips: dict[str, unreal.AnimSequence], name: str, owner: str) -> unreal.AnimSequence:
    """Le clip `name` : Interchange le nomme tel quel, ou le fait précéder du nom du fichier
    (`brawleridle`)."""
    exact = [clip for key, clip in clips.items() if key.lower() == name.lower()]
    loose = [clip for key, clip in clips.items() if key.lower().endswith(name.lower())]
    found = exact or loose
    if len(found) != 1:
        fail(f"{owner} : clip « {name} » introuvable ou ambigu parmi {sorted(clips)}")
    return found[0]


def ambient_cube() -> unreal.TextureCube:
    """Un cube blanc uniforme : la source de la lumière du ciel, que la table du jour teinte."""
    if unreal.EditorAssetLibrary.does_asset_exist(AMBIENT_CUBE):
        return unreal.EditorAssetLibrary.load_asset(AMBIENT_CUBE)
    # Une image Radiance de 16 × 8, chaque pixel à (1, 1, 1) : mantisse 128, exposant 129.
    source = PROJECT_DIR / "Intermediate" / "Jadg" / "T_AmbientWhite.hdr"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y 8 +X 16\n" + bytes([128, 128, 128, 129]) * 128)
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = AMBIENT_CUBE.rsplit("/", 1)[0]
    task.destination_name = AMBIENT_CUBE.rsplit("/", 1)[1]
    task.automated = True
    task.replace_existing = True
    task.save = True
    task.set_editor_property("async_", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    cube = unreal.EditorAssetLibrary.load_asset(AMBIENT_CUBE)
    if not isinstance(cube, unreal.TextureCube):
        fail(f"{AMBIENT_CUBE} : l'import a donné {type(cube).__name__}, un cube attendu")
    return cube


# --- La carte ---------------------------------------------------------------------------------

def game_class(name: str):
    cls = unreal.load_class(None, f"{GAME_CLASSES}.{name}")
    if cls is None:
        fail(f"classe {name} absente : construire le projet (pwsh scripts/build.ps1 -Unreal)")
    return cls


class Level:
    """La carte en construction.

    Les acteurs sont créés dans le monde lui-même, par `UJadgSceneBuild` (C++ du jeu) : la voie
    de l'éditeur (`EditorActorSubsystem.spawn_actor_from_*`) passe par une vue de niveau, qu'un
    éditeur sans fenêtre n'a pas.
    """

    def __init__(self, world: unreal.World) -> None:
        self.world = world

    def spawn(self, what, location: unreal.Vector, rotation: unreal.Rotator, label: str, folder: str,
              scale: unreal.Vector | None = None) -> unreal.Actor:
        """Un acteur de la classe `what`, ou un acteur de maillage statique si `what` en est un."""
        mesh = what if isinstance(what, unreal.StaticMesh) else None
        actor_class = unreal.StaticMeshActor if mesh is not None else what
        transform = unreal.Transform(location, rotation, scale or unreal.Vector(1.0, 1.0, 1.0))
        actor = unreal.JadgSceneBuild.spawn_actor(self.world, actor_class, transform)
        if actor is None:
            fail(f"{label} : l'acteur n'a pas pu être créé")
        if mesh is not None:
            actor.static_mesh_component.set_static_mesh(mesh)
        return self.name(actor, label, folder)

    def box_volume(self, volume_class, centre: unreal.Vector, size: unreal.Vector, label: str,
                   folder: str) -> unreal.Actor:
        """Un volume en boîte : sa brosse ne se dessine que par l'éditeur (`UJadgSceneBuild`)."""
        actor = unreal.JadgSceneBuild.spawn_box_volume(self.world, volume_class, centre, size)
        if actor is None:
            fail(f"{label} : le volume n'a pas pu être créé")
        return self.name(actor, label, folder)

    @staticmethod
    def name(actor: unreal.Actor, label: str, folder: str) -> unreal.Actor:
        actor.set_actor_label(label)
        actor.set_folder_path(folder)
        return actor


def colour(text: str) -> unreal.Color:
    return unreal.Color(int(text[5:7], 16), int(text[3:5], 16), int(text[1:3], 16), 255)


def place_objects(level: Level, scene: dict, library: Library, frame: Frame) -> None:
    lighting = scene.get("lighting", {})
    for item in scene["placed"]:
        mesh = library.static_mesh(item["mesh"])
        label = item["id"].replace("/", "_")
        location = frame.point(item["position"])
        scale = item.get("scale", 1.0)
        if "height" in item:
            box = mesh.get_bounding_box()
            scale = item["height"] * 100.0 / (box.max.z - box.min.z)
            location.z -= box.min.z * scale
        level.spawn(mesh, location, unreal.Rotator(0.0, 0.0, frame.yaw(item.get("yaw", 0.0))),
                    label, item["folder"],
                    frame.mirror_scale(scale) if item.get("mirrored") else unreal.Vector(scale, scale, scale))
        emission = item.get("light")
        if emission is None:
            continue
        # Une source d'un groupe agrandi s'agrandit avec lui : sa hauteur et sa portée suivent
        # l'échelle, son intensité le carré de l'échelle (le même éclairement à la même place).
        grown = item.get("groupScale", 1.0)
        position = list(item["position"])
        position[1] += emission.get("height", 0.0) * grown
        always = emission.get("always", False)
        lamp = level.spawn(unreal.PointLight, frame.point(position), unreal.Rotator(0, 0, 0),
                           f"{label}_lumiere", f"{item['folder']}/lumieres")
        component = lamp.point_light_component
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
        component.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
        component.set_editor_property(
            "intensity", lighting.get("fireCandelas" if always else "lampCandelas", 20.0) * grown * grown)
        component.set_editor_property("light_color", colour(emission["color"]))
        component.set_editor_property(
            "attenuation_radius", emission.get("radius", emission.get("range", 6.0)) * 100.0 * grown)
        # Un feu de l'arène éclaire sans ombre portée ; une lampe du parvis en porte.
        component.set_editor_property("cast_shadows", not always)
        if not always:
            lamp.tags = [LAMP_TAG]


def place_sky(level: Level, scene: dict, frame: Frame) -> None:
    origin, flat = unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
    sun = level.spawn(unreal.DirectionalLight, unreal.Vector(0, 0, 3000), unreal.Rotator(0, -48, 0), "Soleil", "ciel")
    sun.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sun.light_component.set_editor_property("atmosphere_sun_light", True)
    lighting = scene.get("lighting", {})
    sun.light_component.set_editor_property("contact_shadow_length", 0.02)
    atmosphere = level.spawn(unreal.SkyAtmosphere, origin, flat, "Atmosphere", "ciel")
    # Le ciel visible est celui de l'atmosphère du moteur, éclairée par le soleil de la table ;
    # `skyLuminance` l'éclaircit, la table étant écrite pour une lumière sans ciel.
    glow = lighting.get("skyLuminance", 1.0)
    atmosphere.get_component_by_class(unreal.SkyAtmosphereComponent).set_editor_property(
        "sky_luminance_factor", unreal.LinearColor(glow, glow, glow, 1.0))

    haze = lighting.get("fog")
    if haze is not None:
        fog = level.spawn(unreal.ExponentialHeightFog, origin, flat, "Brume", "ciel")
        component = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
        component.set_editor_property("fog_density", haze["density"])
        component.set_editor_property("fog_height_falloff", haze["falloff"])
        component.set_editor_property("enable_volumetric_fog", haze.get("volumetric", False))

    ground = scene.get("ground")
    if ground is not None:
        # Le sol lointain : un plan uni sous le dallage, jusqu'à l'horizon.
        tint = colour(ground["colour"])
        plane = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane")
        side = ground["size"]
        actor = level.spawn(plane, frame.point([0.0, ground.get("height", -0.02), 0.0]), flat, "SolLointain", "ciel",
                            unreal.Vector(side, side, 1.0))
        actor.static_mesh_component.set_material(0, ground_material(
            unreal.LinearColor(tint.r / 255.0, tint.g / 255.0, tint.b / 255.0, 1.0)))

    sky = level.spawn(unreal.SkyLight, unreal.Vector(0, 0, 3000), flat, "LumiereDuCiel", "ciel")
    sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property("real_time_capture", False)
    sky.light_component.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    sky.light_component.set_editor_property("cubemap", ambient_cube())

    exposure = level.spawn(unreal.PostProcessVolume, origin, flat, "Exposition", "ciel")
    exposure.set_editor_property("unbound", True)
    settings = exposure.get_editor_property("settings")
    # Exposition fixe de 1 : les intensités de la table du jour s'appliquent sans autre échelle.
    settings.set_editor_property("override_auto_exposure_method", True)
    settings.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    settings.set_editor_property("override_auto_exposure_bias", True)
    settings.set_editor_property("auto_exposure_bias", lighting.get("exposureBias", 0.0))
    settings.set_editor_property("override_auto_exposure_apply_physical_camera_exposure", True)
    settings.set_editor_property("auto_exposure_apply_physical_camera_exposure", False)
    for name, value in lighting.get("post", {}).items():
        # Un réglage de post-traitement du moteur, par son nom (`bloom_intensity`, `vignette_intensity`…).
        settings.set_editor_property(f"override_{name}", True)
        settings.set_editor_property(name, value)
    exposure.set_editor_property("settings", settings)

    day = level.spawn(game_class("JadgDayLight"), origin, flat, "Jour", "ciel")
    day.set_editor_property("table_file", scene["daylight"])
    day.set_editor_property("sun", sun)
    day.set_editor_property("sky", sky)
    day.set_editor_property("sun_scale", lighting.get("sunScale", 1.0))
    day.set_editor_property("ambient_scale", lighting.get("ambientScale", 1.0))
    day.set_editor_property("east", frame.direction([1.0, 0.0, 0.0]))
    day.set_editor_property("up", frame.direction([0.0, 1.0, 0.0]))
    day.set_editor_property("south", frame.direction([0.0, 0.0, 1.0]))


def place_navigation(level: Level, scene: dict, frame: Frame) -> None:
    if "navigation" not in scene:
        return  # une scène sans marche (le socle) n'a pas de volume de navigation
    x0, z0, x1, z1 = scene["navigation"]["area"]
    height = scene["navigation"]["height"]
    centre = frame.point([(x0 + x1) / 2, height / 2 - 0.5, (z0 + z1) / 2])
    east, south = frame.point([x1 - x0, 0, 0]), frame.point([0, 0, z1 - z0])
    size = unreal.Vector(abs(east.x) + abs(south.x), abs(east.y) + abs(south.y), (height + 1.0) * 100.0)
    level.box_volume(unreal.NavMeshBoundsVolume, centre, size, "Navigation", "navigation")


def place_characters(level: Level, scene: dict, library: Library, frame: Frame) -> None:
    walker = game_class("JadgWalker")
    # Le devant d'un modèle de la chaîne est +Z du .glb ; un personnage du moteur avance vers +X.
    front = frame.direction([0.0, 0.0, 1.0])
    mesh_yaw = -math.degrees(math.atan2(front.y, front.x))
    for item in scene.get("characters", ()):
        skeletal, skins, clips = library.character(item["mesh"])
        bounds = skeletal.get_bounds()
        half = bounds.box_extent.z
        radius = max(20.0, min(bounds.box_extent.x, bounds.box_extent.y, half))
        feet = bounds.origin.z - bounds.box_extent.z
        location = frame.point(item["position"])
        location.z += half
        actor = level.spawn(walker, location, frame.look(item.get("heading", 0.0)), item["id"], "personnages")
        actor.capsule_component.set_editor_property("capsule_half_height", half)
        actor.capsule_component.set_editor_property("capsule_radius", radius)
        actor.mesh.set_skeletal_mesh_asset(skeletal)
        for index, skin in enumerate(skins):
            actor.mesh.set_material(index, skin)
        actor.mesh.set_relative_location(unreal.Vector(0, 0, -half - feet), False, False)
        actor.mesh.set_relative_rotation(unreal.Rotator(0, 0, mesh_yaw), False, False)
        actor.set_editor_property("idle_clip", clip_named(clips, item["idle"], item["id"]))
        actor.set_editor_property("walk_clip", clip_named(clips, item["walk"], item["id"]))
        actor.set_editor_property("walk_speed", item["walkSpeed"] * 100.0)
        actor.set_editor_property("playable", item.get("playable", False))
        patrol = []
        for point in item.get("patrol", ()):
            stop = frame.point(point)
            stop.z += half
            patrol.append(stop)
        actor.set_editor_property("patrol", patrol)
        if item.get("playable"):
            level.spawn(unreal.PlayerStart, location, frame.look(0.0), "Depart", "personnages")


def place_shots(level: Level, scene: dict, frame: Frame) -> None:
    shot_class = game_class("JadgShot")
    for order, item in enumerate(scene.get("shots", ())):
        actor = level.spawn(shot_class, frame.point(item["target"]), frame.look(item["heading"], item["pitch"]),
                      f"Cadrage_{item['id']}", "cadrages")
        actor.set_editor_property("shot_id", item["id"])
        actor.set_editor_property("order", order)
        actor.set_editor_property("distance", item["distance"] * 100.0)


def main() -> None:
    name = master_import.command_line_option("JadgScene") or "porte-1012"
    scene = load_scene(name)
    library = Library(scene.get("assetsRoot"))

    # Le repère se mesure sur une pièce que la description nomme : il la faut dissymétrique sur
    # ses trois axes (le quart de gradins du Colisée l'est), sans quoi un signe ne se lit pas.
    reference = scene["frameReference"]
    frame = Frame(library.assets / reference, library.static_mesh(reference))

    world = unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    if world is None:
        fail("la carte vide n'a pas pu être créée")
    level = Level(world)
    place_objects(level, scene, library, frame)
    place_sky(level, scene, frame)
    place_navigation(level, scene, frame)
    place_characters(level, scene, library, frame)
    place_shots(level, scene, frame)
    world.get_world_settings().set_editor_property("default_game_mode", game_class("JadgGameMode"))

    # La carte doit porter tout ce que la description pose : un acteur perdu arrête le script.
    meshes = len(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor))
    expected = len(scene["placed"]) + (1 if "ground" in scene else 0)
    if meshes != expected:
        fail(f"{meshes} acteurs de maillage dans la carte, {expected} attendus")

    if not unreal.EditorLoadingAndSavingUtils.save_map(world, scene["map"]):
        fail(f"{scene['map']} : la carte n'a pas pu être sauvée")
    log(f"terminé : {scene['map']}, {len(scene['placed'])} objets, "
        f"{len(scene.get('characters', ()))} personnage(s), {len(scene.get('shots', ()))} cadrage(s), "
        f"{library.imported} import(s)")


if __name__ == "__main__":
    main()
