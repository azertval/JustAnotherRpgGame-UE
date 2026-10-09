# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Construit le niveau Unreal d'une carte depuis sa description v5 (LOT-1018, D-51, D-52).

Script Python **d'éditeur** : il tourne dans UnrealEditor, sans fenêtre, et produit le niveau
(`.umap`) et les assets (`.uasset`) qu'il montre. Aucun acteur n'est posé à la main, aucun
Blueprint n'est créé ; relancé, il refait le niveau entier, à l'identique (son **empreinte**).

    UnrealEditor-Cmd.exe JustAnotherRpgGame.uproject -run=pythonscript ^
        -script="<dépôt>/scripts/maps/build_level.py" -JadgMap=essai/etals -unattended -nosplash -nullrhi

(le chemin du script est absolu : le moteur résout un chemin relatif depuis ses binaires), ou
`powershell scripts/build.ps1 -Unreal -Map <carte>`.

Options sur la ligne de commande du moteur :
    -JadgMap=<carte>     la carte, par son identifiant (`essai/etals`, `central-empire/capital/martpart`)
    -JadgCheck           puis contrôle le maillage de navigation : chaque entité, chaque point
                         d'arrivée atteint depuis l'entrée ; une case inatteignable est une erreur

La description (`jadg_map.py`) est lue telle quelle. Son repère : x vers l'est, y vers le sud, z
vers le haut, en mètres ; le coin de la case (0, 0) en `origin`. Le niveau se nomme d'après la
carte, `/Game/Maps/Levels/<carte>` : c'est ce qu'un portail ouvre (`AJadgMapFrame::MapPackage`).

Ce que le script pose, dans l'ordre :

  1. chaque maillage cité est importé par Interchange s'il ne l'est pas déjà — un maître par son
     manifeste, empreinte vérifiée (`import_master_unreal.py`), une pièce de kit sous `/Game/Kit/…`,
     une donnée d'essai sous `/Game/Fixtures/…` —, Nanite actif, la collision prise sur le
     maillage lui-même ;
  2. **le changement de repère est mesuré, pas supposé**, sur le bloc repère des données d'essai
     (`Scene/socle/repere.glb`, dissymétrique sur ses trois axes) ;
  3. un niveau vide, puis :
     - le **terrain** (`terrain`) : un `Landscape` dont les hauteurs et les poids des couches de
       matière sont **régénérés** depuis la description — formes de relief, contours qui mettent
       à une hauteur ou peignent une couche, routes —, écrits en images sous
       `Saved/Jadg/levels/<carte>/` pour qu'on les relise, et l'eau des contours (`water`) ;
     - les **couches de pièces** (`layers`, la v4 migrée) : une pièce du kit du lieu par case,
       posées par instances, une couche et une pièce par acteur ;
     - les **objets** (`objects`) : un acteur par objet, sa position, son lacet, son tangage, son
       roulis, son échelle, son étage ; l'entité de Core qu'il montre (`entity`) ; sa lumière ;
     - les **dallages** (`fills`) et les **préfabriqués** (`prefabs`, un `AJadgPrefab` et ses
       objets attachés) ;
     - le ciel, le soleil, la lumière du ciel, l'exposition fixe, la table du jour ;
     - la **navigation** et les **volumes** des entités (zone de combat, marqueur de rencontre) ;
     - le **groupe** à l'entrée (`party`) et les **PNJ** par leur fiche d'apparence (`appearance`) ;
     - un **repère** par entité (`JadgMarker:<id>`) : ce que l'auteur déplace dans l'éditeur, et
       que `read_level.py` relit ;
     - le cadre de la carte de Core (`AJadgMapFrame`, ses étages), les cadrages, le mode de jeu ;
  4. le niveau est sauvé, et son **empreinte** écrite : `Saved/Jadg/levels/<carte>.json` — chaque
     acteur par son étiquette, sa classe, sa transformation arrondie, son maillage, ses réglages ;
     deux constructions de la même description donnent la même empreinte.

Le script sort en erreur (commandlet en -1) à la première pièce fautive. Une pièce d'une couche
que le kit du lieu n'a pas reste dans le texte et n'est pas posée : elle est comptée et nommée.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
import time
import zlib
from pathlib import Path

import unreal

PROJECT_DIR = Path(unreal.Paths.project_dir()).resolve()
ELEMENTS = PROJECT_DIR / "Source" / "Elements"
ASSETS = ELEMENTS / "Assets"
PREFABS = ELEMENTS / "Editor" / "Prefabs"
FIXTURE_ASSETS = PROJECT_DIR / "Source" / "Test" / "Fixtures" / "Meshes" / "Assets"
FRAME_REFERENCE = "Scene/socle/repere.glb"

sys.path.insert(0, str(PROJECT_DIR / "scripts" / "assetsGeneration"))
sys.path.insert(0, str(PROJECT_DIR / "scripts" / "maps"))
import import_master_unreal as master_import  # noqa: E402
import jadg_map  # noqa: E402

KIT_ROOT = "/Game/Kit"
FIXTURE_ROOT = "/Game/Fixtures"
LEVEL_MAPS = jadg_map.MAP_PACKAGES
AMBIENT_CUBE = "/Game/Scenes/Common/T_AmbientWhite"
CHARACTER_MATERIAL = "/Game/Scenes/Common/M_Character"
GROUND_MATERIAL = "/Game/Scenes/Common/M_Ground"
OUTLINE_MATERIAL = "/Game/Scenes/Common/M_Outline"
WATER_MATERIAL = "/Game/Scenes/Common/M_Water"
OUTLINE_COLOUR = (1.0, 0.78, 0.36)  # l'or du HUD (`JadgHud.cpp`)
OUTLINE_PIXELS = 3.0
GAME_CLASSES = "/Script/JustAnotherRpgGame"
LAMP_TAG = "JadgLamp"
ENTITY_TAG = "JadgEntity:"
OBJECT_TAG = "JadgObject:"
MARKER_TAG = "JadgMarker:"
VOLUME_TAG = "JadgVolume:"
FOOTPRINTS = PROJECT_DIR / "Saved" / "Jadg" / "levels"
# Un terrain : des composants de 63 quads ; 32 768 au niveau de l'acteur ; une échelle verticale de
# 100 donne 1/128 de centimètre par pas de hauteur.
LANDSCAPE_QUADS = 63
LANDSCAPE_Z_SCALE = 100.0


def log(message: str) -> None:
    unreal.log(f"[Scene] {message}")


def fail(message: str) -> None:
    unreal.log_error(f"[Scene] {message}")
    raise RuntimeError(message)


def to_glb(point: list[float]) -> list[float]:
    """Un point de la carte (x est, y sud, z haut) dans le repère d'un .glb posé (X est, Y haut, Z sud)."""
    return [point[0], point[2], point[1]]


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

    # Du .glb au moteur.
    def direction(self, vector: list[float]) -> unreal.Vector:
        return unreal.Vector(*[sign * vector[i] for i, sign in self.axes])

    def point(self, metres: list[float]) -> unreal.Vector:
        return unreal.Vector(*[sign * metres[i] * 100.0 for i, sign in self.axes])

    # De la carte au moteur.
    def map_point(self, metres: list[float]) -> unreal.Vector:
        return self.point(to_glb(metres))

    def map_direction(self, vector: list[float]) -> unreal.Vector:
        return self.direction(to_glb(vector))

    # Du moteur à la carte (`read_level.py`).
    def glb_of(self, vector: unreal.Vector, scale: float = 1.0) -> list[float]:
        glb = [0.0, 0.0, 0.0]
        for k, (i, sign) in enumerate(self.axes):
            glb[i] = sign * [vector.x, vector.y, vector.z][k] / scale
        return glb

    def map_of_point(self, location: unreal.Vector) -> list[float]:
        g = self.glb_of(location, 100.0)
        return [g[0], g[2], g[1]]

    def map_of_direction(self, vector: unreal.Vector) -> list[float]:
        g = self.glb_of(vector)
        return [g[0], g[2], g[1]]

    def local_map_axis(self, k: int) -> int:
        """L'axe de la carte que l'axe local k du maillage dans le moteur porte."""
        return {0: 0, 1: 2, 2: 1}[self.axes[k][0]]

    def rotation(self, yaw: float, pitch: float = 0.0, roll: float = 0.0) -> unreal.Rotator:
        """La rotation du moteur d'un objet tourné de `roll` (le sud monte), puis `pitch` (l'est
        monte), puis `yaw` (le sud tourne vers l'est), dans le repère de la carte."""
        matrix = map_rotation(yaw, pitch, roll)
        images = []
        for k in (0, 2):
            i, sign = self.axes[k]
            local = [0.0, 0.0, 0.0]
            local[i] = sign
            turned = apply(matrix, [local[0], local[2], local[1]])
            images.append(self.map_direction(turned))
        return unreal.MathLibrary.make_rot_from_xz(images[0], images[1])

    def angles_of(self, rotator: unreal.Rotator) -> tuple[float, float, float]:
        """Lacet, tangage, roulis de la carte d'une rotation du moteur (l'inverse de `rotation`)."""
        columns = []
        for axis in (unreal.MathLibrary.get_forward_vector(rotator), unreal.MathLibrary.get_right_vector(rotator),
                     unreal.MathLibrary.get_up_vector(rotator)):
            columns.append(self.map_of_direction(axis))
        # La matrice de la carte : l'image de chaque axe de la carte.
        image = [[0.0] * 3 for _ in range(3)]
        for k in range(3):
            i, sign = self.axes[k]
            m = {0: 0, 1: 2, 2: 1}[i]
            for row in range(3):
                image[row][m] = sign * columns[k][row]
        return angles(image)

    def scale(self, value) -> unreal.Vector:
        """L'échelle du moteur d'une échelle de la carte : un nombre, ou trois (x, y, z du maillage)."""
        if isinstance(value, list):
            return unreal.Vector(*[value[self.local_map_axis(k)] for k in range(3)])
        return unreal.Vector(value, value, value)

    def map_scale(self, scale: unreal.Vector) -> list[float]:
        values = [scale.x, scale.y, scale.z]
        result = [0.0, 0.0, 0.0]
        for k in range(3):
            result[self.local_map_axis(k)] = values[k]
        return result

    def mirror_scale(self, scale: float) -> unreal.Vector:
        """L'échelle d'une pièce en miroir : l'axe X du .glb est retourné."""
        return unreal.Vector(*[-scale if i == 0 else scale for i, _ in self.axes])

    def look(self, heading: float, pitch: float = 0.0) -> unreal.Rotator:
        """Le regard d'une boussole (0 = nord, 90 = est), `pitch` degrés sous l'horizon."""
        h, p = math.radians(heading), math.radians(pitch)
        toward = [math.sin(h) * math.cos(p), -math.cos(h) * math.cos(p), -math.sin(p)]
        return unreal.MathLibrary.find_look_at_rotation(unreal.Vector(0, 0, 0), self.map_direction(toward))


def map_rotation(yaw: float, pitch: float, roll: float) -> list[list[float]]:
    """R = R_lacet · R_tangage · R_roulis, dans le repère de la carte (x est, y sud, z haut)."""
    a, b, c = (math.radians(v) for v in (yaw, pitch, roll))
    ry = [[math.cos(a), math.sin(a), 0.0], [-math.sin(a), math.cos(a), 0.0], [0.0, 0.0, 1.0]]
    rp = [[math.cos(b), 0.0, -math.sin(b)], [0.0, 1.0, 0.0], [math.sin(b), 0.0, math.cos(b)]]
    rr = [[1.0, 0.0, 0.0], [0.0, math.cos(c), -math.sin(c)], [0.0, math.sin(c), math.cos(c)]]
    return multiply(multiply(ry, rp), rr)


def multiply(m: list[list[float]], n: list[list[float]]) -> list[list[float]]:
    return [[sum(m[i][k] * n[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def apply(m: list[list[float]], v: list[float]) -> list[float]:
    return [sum(m[i][k] * v[k] for k in range(3)) for i in range(3)]


def angles(m: list[list[float]]) -> tuple[float, float, float]:
    """Lacet, tangage, roulis d'une matrice `map_rotation` (l'inverse) : m[2][0] = sin(tangage),
    m[2][1] / m[2][2] donnent le roulis, -m[1][0] / m[0][0] le lacet."""
    b = math.asin(max(-1.0, min(1.0, m[2][0])))
    if abs(math.cos(b)) > 1e-6:
        c = math.atan2(m[2][1], m[2][2])
        a = math.atan2(-m[1][0], m[0][0])
    else:  # tangage de ±90° : le roulis se confond avec le lacet
        c = 0.0
        a = math.atan2(m[0][1], m[1][1])
    return math.degrees(a), math.degrees(b), math.degrees(c)


def kit_folder(mesh: str, root: str = KIT_ROOT) -> str:
    """`Regions/…/arena-of-fate/Scene/af-pyre.glb` → `/Game/Kit/Regions/…/arena-of-fate`."""
    parts = [p for p in Path(mesh).parent.parts if p != "Scene"]
    return "/".join([root, *parts])


class Library:
    """Les assets de la carte : importés une fois, relus ensuite.

    Une pièce **construite par script** (`Built/…`, `build_colosseum.py`) change quand son script
    change : l'empreinte du `.glb` importé est notée (`Intermediate/Jadg/imports.json`), et une
    pièce dont l'empreinte diffère est réimportée ; de même une donnée d'essai (`assetsRoot`,
    `build_mesh_fixture.py`). Un maître ne change jamais (son manifeste le vérifie) ; une pièce de
    kit ne change qu'avec le verrou des kits."""

    def __init__(self, assets_root: str | None = None) -> None:
        # Les maillages de la carte : les kits, ou le dossier que la description nomme.
        self.assets = PROJECT_DIR / assets_root if assets_root else ASSETS
        self.content_root = FIXTURE_ROOT if assets_root else KIT_ROOT
        manifest = json.loads(master_import.MANIFEST.read_text(encoding="utf-8"))
        self.master = {piece["file"]: piece for piece in manifest["pieces"]}
        self.static: dict[str, unreal.StaticMesh] = {}
        self.imported = 0
        self.import_seconds = 0.0
        self.imports_file = PROJECT_DIR / "Intermediate" / "Jadg" / "imports.json"
        self.imports: dict[str, str] = (json.loads(self.imports_file.read_text(encoding="utf-8"))
                                        if self.imports_file.exists() else {})

    def asset_path(self, mesh: str) -> str:
        piece = None if self.assets != ASSETS else self.master.get(mesh)
        if piece is not None:
            return piece["asset"]
        glb = self.assets / mesh
        return f"{kit_folder(mesh, self.content_root)}/{glb.stem}/StaticMeshes/SM_{glb.stem}"

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
        asset_path = self.asset_path(mesh)
        if piece is not None:
            if master_import.sha256_of(glb) != piece["sha256"]:
                fail(f"{mesh} : empreinte différente du manifeste du maître")
        elif mesh.startswith("Master/") and not scripted:
            fail(f"{mesh} : absent du manifeste du maître")
        elif scripted:
            digest = master_import.sha256_of(glb)
            stale = self.imports.get(asset_path) != digest
            self.imports[asset_path] = digest
        piece_folder = asset_path.rsplit("/", 2)[0]
        if unreal.EditorAssetLibrary.does_asset_exist(asset_path) and not stale:
            asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        else:
            started = time.perf_counter()
            log(f"import de {mesh} -> {asset_path}" + (" (pièce régénérée)" if stale else ""))
            if unreal.EditorAssetLibrary.does_directory_exist(piece_folder):
                unreal.EditorAssetLibrary.delete_directory(piece_folder)
            asset = master_import.import_glb(glb, piece_folder.rsplit("/", 1)[0], piece_folder, asset_path)
            self.imported += 1
            self.import_seconds += time.perf_counter() - started
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


def flat_material(path: str, colour: unreal.LinearColor, roughness: float = 1.0) -> unreal.Material:
    """Une matière d'une couleur unie : le sol lointain, l'eau."""
    library = unreal.MaterialEditingLibrary
    material = (unreal.EditorAssetLibrary.load_asset(path)
                if unreal.EditorAssetLibrary.does_asset_exist(path) else new_material(path))
    library.delete_all_material_expressions(material)
    tint = library.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -400, 0)
    tint.set_editor_property("constant", colour)
    library.connect_material_property(tint, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = library.create_material_expression(material, unreal.MaterialExpressionConstant, -400, 300)
    rough.set_editor_property("r", roughness)
    library.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    library.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(path)
    return material


def terrain_material(path: str, layers: list[dict]) -> unreal.Material:
    """La matière d'un terrain : la couleur de chaque couche, pesée par son poids peint
    (`LandscapeLayerWeight` en chaîne)."""
    library = unreal.MaterialEditingLibrary
    material = (unreal.EditorAssetLibrary.load_asset(path)
                if unreal.EditorAssetLibrary.does_asset_exist(path) else new_material(path))
    library.delete_all_material_expressions(material)
    blended = None
    for index, layer in enumerate(layers):
        tint = colour(layer["colour"])
        constant = library.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -900, index * 200)
        constant.set_editor_property("constant", unreal.LinearColor(tint.r / 255.0, tint.g / 255.0, tint.b / 255.0, 1.0))
        weight = library.create_material_expression(material, unreal.MaterialExpressionLandscapeLayerWeight, -500, index * 200)
        weight.set_editor_property("parameter_name", layer["name"])
        library.connect_material_expressions(constant, "", weight, "Layer")
        if blended is not None:
            library.connect_material_expressions(blended, "", weight, "Base")
        blended = weight
    library.connect_material_property(blended, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = library.create_material_expression(material, unreal.MaterialExpressionConstant, -400, -300)
    rough.set_editor_property("r", 1.0)
    library.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    library.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(path)
    return material


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


def outline_material() -> unreal.Material:
    """Le contour de ce que le meneur peut solliciter (LOT-1016) : une matière de post-traitement.

    Le jeu marque l'acteur désigné dans le tampon de gabarit (profondeur personnalisée, valeur 1 :
    `AJadgWalker::SetOutlined`, `AJadgParty`). Un pixel hors de la silhouette dont un voisin, à
    `OUTLINE_PIXELS` pixels, est dedans prend la couleur du contour ; tous les autres gardent
    l'image. Le tampon de gabarit demande `r.CustomDepth=3` (`Config/DefaultEngine.ini`)."""
    library = unreal.MaterialEditingLibrary
    material = (unreal.EditorAssetLibrary.load_asset(OUTLINE_MATERIAL)
                if unreal.EditorAssetLibrary.does_asset_exist(OUTLINE_MATERIAL) else new_material(OUTLINE_MATERIAL))
    library.delete_all_material_expressions(material)
    material.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)

    def node(kind, x: int, y: int):
        return library.create_material_expression(material, kind, x, y)

    def scene_texture(identifier, x: int, y: int):
        sampled = node(unreal.MaterialExpressionSceneTexture, x, y)
        sampled.set_editor_property("scene_texture_id", identifier)
        return sampled

    image = scene_texture(unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0, -400, -300)
    centre = scene_texture(unreal.SceneTextureId.PPI_CUSTOM_STENCIL, -1200, 0)
    here = node(unreal.MaterialExpressionScreenPosition, -1600, 300)
    around = None
    for index, (dx, dy) in enumerate(((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0))):
        row = 300 + index * 250
        step = node(unreal.MaterialExpressionConstant2Vector, -1600, row + 100)
        step.set_editor_property("r", dx * OUTLINE_PIXELS)
        step.set_editor_property("g", dy * OUTLINE_PIXELS)
        scaled = node(unreal.MaterialExpressionMultiply, -1400, row + 100)
        library.connect_material_expressions(step, "", scaled, "A")
        library.connect_material_expressions(centre, "InvSize", scaled, "B")
        moved = node(unreal.MaterialExpressionAdd, -1200, row)
        library.connect_material_expressions(here, "ViewportUV", moved, "A")
        library.connect_material_expressions(scaled, "", moved, "B")
        neighbour = scene_texture(unreal.SceneTextureId.PPI_CUSTOM_STENCIL, -1000, row)
        library.connect_material_expressions(moved, "", neighbour, "UVs")
        red = node(unreal.MaterialExpressionComponentMask, -800, row)
        for channel, kept in (("r", True), ("g", False), ("b", False), ("a", False)):
            red.set_editor_property(channel, kept)
        library.connect_material_expressions(neighbour, "Color", red, "")
        if around is None:
            around = red
        else:
            widest = node(unreal.MaterialExpressionMax, -600, row)
            library.connect_material_expressions(around, "", widest, "A")
            library.connect_material_expressions(red, "", widest, "B")
            around = widest
    inside = node(unreal.MaterialExpressionComponentMask, -800, 0)
    for channel, kept in (("r", True), ("g", False), ("b", False), ("a", False)):
        inside.set_editor_property(channel, kept)
    library.connect_material_expressions(centre, "Color", inside, "")
    edge = node(unreal.MaterialExpressionSubtract, -400, 300)
    library.connect_material_expressions(around, "", edge, "A")
    library.connect_material_expressions(inside, "", edge, "B")
    mask = node(unreal.MaterialExpressionSaturate, -250, 300)
    library.connect_material_expressions(edge, "", mask, "")
    tint = node(unreal.MaterialExpressionConstant3Vector, -400, 100)
    tint.set_editor_property("constant", unreal.LinearColor(*OUTLINE_COLOUR, 1.0))
    blend = node(unreal.MaterialExpressionLinearInterpolate, -100, 0)
    # L'image vient avec son alpha : le contour n'en mélange que la couleur.
    colour_only = node(unreal.MaterialExpressionComponentMask, -250, -300)
    for channel, kept in (("r", True), ("g", True), ("b", True), ("a", False)):
        colour_only.set_editor_property(channel, kept)
    library.connect_material_expressions(image, "Color", colour_only, "")
    library.connect_material_expressions(colour_only, "", blend, "A")
    library.connect_material_expressions(tint, "", blend, "B")
    library.connect_material_expressions(mask, "", blend, "Alpha")
    library.connect_material_property(blend, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    library.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(OUTLINE_MATERIAL)
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


# --- Le niveau --------------------------------------------------------------------------------

def game_class(name: str):
    cls = unreal.load_class(None, f"{GAME_CLASSES}.{name}")
    if cls is None:
        fail(f"classe {name} absente : construire le projet (powershell scripts/build.ps1 -Unreal)")
    return cls


class Level:
    """Le niveau en construction.

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

    def instances(self, mesh: unreal.StaticMesh, transforms: list[unreal.Transform], label: str,
                  folder: str) -> unreal.Actor:
        actor = unreal.JadgSceneBuild.spawn_instances(self.world, mesh, transforms)
        if actor is None:
            fail(f"{label} : les instances n'ont pas pu être créées")
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


def storey_z(doc: dict, storey: int) -> float:
    storeys = doc.get("storeys") or [{"z": 0.0}]
    return storeys[storey]["z"] if 0 <= storey < len(storeys) else 0.0


def place_light(level: Level, frame: Frame, doc: dict, emission: dict, foot: list[float], label: str, folder: str,
                grown: float = 1.0) -> None:
    """La lumière d'un objet : une source ponctuelle à sa hauteur, une lampe portant une ombre,
    un feu sans. Une source d'un préfabriqué agrandi s'agrandit avec lui : sa hauteur et sa portée
    suivent l'échelle, son intensité le carré de l'échelle (le même éclairement à la même place)."""
    lighting = doc.get("lighting", {})
    position = [foot[0], foot[1], foot[2] + emission.get("height", 0.0) * grown]
    always = emission.get("always", False)
    lamp = level.spawn(unreal.PointLight, frame.map_point(position), unreal.Rotator(0, 0, 0), f"{label}_lumiere",
                       f"{folder}/lumieres")
    component = lamp.point_light_component
    component.set_mobility(unreal.ComponentMobility.MOVABLE)
    component.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    component.set_editor_property("intensity", lighting.get("fireCandelas" if always else "lampCandelas", 20.0) * grown * grown)
    component.set_editor_property("light_color", colour(emission["color"]))
    component.set_editor_property("attenuation_radius", emission.get("radius", emission.get("range", 6.0)) * 100.0 * grown)
    # Un feu de l'arène éclaire sans ombre portée ; une lampe du parvis en porte.
    component.set_editor_property("cast_shadows", not always)
    if not always:
        lamp.tags = [LAMP_TAG]


def place_object(level: Level, frame: Frame, doc: dict, library: Library, item: dict, folder: str,
                 parent: tuple[list[float], float, float] | None = None) -> unreal.Actor:
    """Un objet : un maillage posé, sa lumière. `parent` : la place, le lacet et l'échelle du
    préfabriqué qui le porte (sa position est alors relative à lui)."""
    mesh = library.static_mesh(item["mesh"])
    position = list(item["position"])
    yaw = item.get("yaw", 0.0)
    size = item.get("scale", 1.0)
    grown = 1.0
    if parent is not None:
        origin, turn, grown = parent
        turned = apply(map_rotation(turn, 0.0, 0.0), [v * grown for v in position])
        position = [origin[k] + turned[k] for k in range(3)]
        yaw += turn
        size = [v * grown for v in size] if isinstance(size, list) else size * grown
    position[2] += storey_z(doc, item.get("storey", 0))
    location = frame.map_point(position)
    if "height" in item:
        box = mesh.get_bounding_box()
        size = item["height"] * 100.0 / (box.max.z - box.min.z) * grown
        location.z -= box.min.z * size
    scale = frame.mirror_scale(size) if item.get("mirrored") else frame.scale(size)
    rotation = frame.rotation(yaw, item.get("pitch", 0.0), item.get("roll", 0.0))
    label = item["id"].replace("/", "_")
    placed = level.spawn(mesh, location, rotation, label, item.get("folder", folder), scale)
    tags = [f"{OBJECT_TAG}{item['id']}"]
    if "entity" in item:
        # L'objet montre une entité de la carte de Core : le jeu le trouve à cette étiquette.
        tags.append(f"{ENTITY_TAG}{item['entity']}")
    placed.tags = tags
    if item.get("light") is not None:
        place_light(level, frame, doc, item["light"], position, label, item.get("folder", folder), grown)
    return placed


def cell_choice(i: int, j: int, count: int) -> int:
    """Le tirage d'une dalle pour la case (i, j) : le même à chaque construction."""
    return ((i * 73856093) ^ (j * 19349663)) % count


def place_fills(level: Level, frame: Frame, doc: dict, library: Library) -> int:
    """Les dallages, par instances : une dalle tirée par case, hors des ellipses exclues."""
    count = 0
    for fill in doc.get("fills", ()):
        cell = fill["cell"]
        ellipses = fill.get("excludeEllipses", ())
        by_mesh: dict[str, list[unreal.Transform]] = {}
        for x0, y0, x1, y1 in fill["areas"]:
            for i in range(round(x0 / cell), round(x1 / cell)):
                for j in range(round(y0 / cell), round(y1 / cell)):
                    x, y = (i + 0.5) * cell, (j + 0.5) * cell
                    if any(((x - cx) / a) ** 2 + ((y - cy) / b) ** 2 < 1.0 for cx, cy, a, b in ellipses):
                        continue
                    mesh = fill["meshes"][cell_choice(i, j, len(fill["meshes"]))]
                    by_mesh.setdefault(mesh, []).append(
                        unreal.Transform(frame.map_point([x, y, 0.0]), unreal.Rotator(0, 0, 0), unreal.Vector(1, 1, 1)))
        for mesh, transforms in sorted(by_mesh.items()):
            level.instances(library.static_mesh(mesh), transforms, f"{fill['id']}_{Path(mesh).stem}", fill["id"])
            count += len(transforms)
    return count


def place_layers(level: Level, frame: Frame, doc: dict, library: Library) -> tuple[int, dict[str, int]]:
    """Les couches de pièces de la v4 migrée : chaque pièce du kit du lieu sur sa case, posée au
    centre de son emprise, à la hauteur de sa couche ; une couche et une pièce par acteur."""
    placed = 0
    missing: dict[str, int] = {}
    place = doc.get("place", "")
    for layer in doc.get("layers", ()):
        z = layer.get("z", 0.0)
        by_piece: dict[str, list[unreal.Transform]] = {}
        for tile in layer.get("tiles", ()):
            piece = tile.get("piece")
            if not piece:
                continue
            resolved = jadg_map.resolve_piece(layer.get("scene") or place, piece, library.assets)
            if resolved is None:
                missing[piece] = missing.get(piece, 0) + 1
                continue
            mesh, (w, h) = resolved
            centre = [doc["origin"][0] + (tile["x"] + w / 2) * jadg_map.CELL,
                      doc["origin"][1] + (tile["y"] + h / 2) * jadg_map.CELL, z]
            by_piece.setdefault(mesh, []).append(
                unreal.Transform(frame.map_point(centre), unreal.Rotator(0, 0, 0), unreal.Vector(1, 1, 1)))
        for mesh, transforms in sorted(by_piece.items()):
            level.instances(library.static_mesh(mesh), transforms, f"couche_{layer['name']}_{Path(mesh).stem}",
                            f"couches/{layer['name']}")
            placed += len(transforms)
    return placed, missing


def place_prefabs(level: Level, frame: Frame, doc: dict, library: Library) -> int:
    """Les préfabriqués : un acteur composé, ses objets attachés à lui."""
    count = 0
    prefab_class = game_class("JadgPrefab")
    for item in doc.get("prefabs", ()):
        prefab = jadg_map.read_prefab(item["prefab"])
        grown = item.get("scale", 1.0)
        origin = list(item["position"])
        anchor = level.spawn(prefab_class, frame.map_point(origin), frame.rotation(item.get("yaw", 0.0)),
                             item["id"].replace("/", "_"), item["id"])
        anchor.set_editor_property("prefab_id", item["prefab"])
        anchor.set_editor_property("instance_id", item["id"])
        anchor.tags = [f"{OBJECT_TAG}{item['id']}"]
        for member in prefab.get("objects", ()):
            if "mesh" not in member:
                resolved = jadg_map.resolve_piece(prefab.get("place", doc.get("place", "")), member["piece"], library.assets)
                if resolved is None:
                    continue
                member = {**member, "mesh": resolved[0]}
            member = {**member, "id": f"{item['id']}/{member['id']}"}
            actor = place_object(level, frame, doc, library, member, item["id"], (origin, item.get("yaw", 0.0), grown))
            actor.tags = [t for t in actor.tags if not str(t).startswith(OBJECT_TAG)]
            actor.attach_to_actor(anchor, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                                  unreal.AttachmentRule.KEEP_WORLD, False)
            count += 1
    return count


# --- Le terrain -------------------------------------------------------------------------------

def inside(point: tuple[float, float], polygon: list[list[float]]) -> bool:
    x, y = point
    hit = False
    for (x0, y0), (x1, y1) in zip(polygon, polygon[1:] + polygon[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            hit = not hit
    return hit


def segment_distance(p: tuple[float, float], a: list[float], b: list[float]) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    length = dx * dx + dy * dy
    t = 0.0 if length == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / length))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def terrain_samples(doc: dict) -> tuple[int, int, list[float], dict[str, list[float]]]:
    """Les hauteurs (en mètres) et les poids de chaque couche (0 à 1) aux sommets du terrain."""
    terrain = doc["terrain"]
    x0, y0, x1, y1 = terrain["area"]
    step = terrain["resolution"]
    quads_x = max(1, math.ceil((x1 - x0) / step / LANDSCAPE_QUADS)) * LANDSCAPE_QUADS
    quads_y = max(1, math.ceil((y1 - y0) / step / LANDSCAPE_QUADS)) * LANDSCAPE_QUADS
    names = [layer["name"] for layer in terrain["layers"]]
    heights: list[float] = []
    weights: dict[str, list[float]] = {name: [] for name in names}
    outlines = doc.get("outlines", ())
    routes = doc.get("routes", ())
    for j in range(quads_y + 1):
        for i in range(quads_x + 1):
            p = (x0 + i * step, y0 + j * step)
            z = terrain.get("base", 0.0)
            for shape in terrain.get("shapes", ()):
                z += shape_height(shape, p)
            for outline in outlines:
                if "height" in outline and inside(p, outline["points"]):
                    z = outline["height"]
            painted = names[0]
            for outline in outlines:
                if "layer" in outline and inside(p, outline["points"]):
                    painted = outline["layer"]
            for route in routes:
                if any(segment_distance(p, a, b) <= route["width"] / 2
                       for a, b in zip(route["points"], route["points"][1:])):
                    painted = route["layer"]
            heights.append(z)
            for name in names:
                weights[name].append(1.0 if name == painted else 0.0)
    return quads_x, quads_y, heights, weights


def shape_height(shape: dict, p: tuple[float, float]) -> float:
    """La hauteur qu'une forme de relief ajoute en `p` : pleine dedans, nulle au-delà de sa pente."""
    falloff = shape.get("falloff", 0.0)
    if shape["shape"] == "disc":
        d = math.hypot(p[0] - shape["centre"][0], p[1] - shape["centre"][1]) - shape["radius"]
    elif shape["shape"] == "rect":
        x0, y0, x1, y1 = shape["area"]
        d = max(x0 - p[0], p[0] - x1, y0 - p[1], p[1] - y1)
    else:  # rampe : de `from` à `to`, la hauteur passe de heights[0] à heights[1]
        (ax, ay), (bx, by) = shape["from"], shape["to"]
        dx, dy = bx - ax, by - ay
        length2 = dx * dx + dy * dy
        t = ((p[0] - ax) * dx + (p[1] - ay) * dy) / length2
        across = abs((p[0] - ax) * dy - (p[1] - ay) * dx) / math.sqrt(length2)
        if not 0.0 <= t <= 1.0 or across > shape["width"] / 2:
            return 0.0
        low, high = shape["heights"]
        return low + (high - low) * t
    if d <= 0:
        return shape["height"]
    return shape["height"] * max(0.0, 1.0 - d / falloff) if falloff > 0 else 0.0


def png(path: Path, width: int, height: int, values: list[int], depth: int) -> None:
    """Une image en niveaux de gris, 8 ou 16 bits : la sortie lisible d'une carte de hauteurs."""
    raw = bytearray()
    for row in range(height):
        raw.append(0)
        for value in values[row * width:(row + 1) * width]:
            raw += value.to_bytes(depth // 8, "big")
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    header = struct.pack(">IIBBBBB", width, height, depth, 0, 0, 0, 0)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
                     + chunk(b"IEND", b""))


def place_terrain(level: Level, frame: Frame, doc: dict, map_id: str) -> int:
    """Le terrain : un `Landscape` régénéré depuis la description, et son eau."""
    terrain = doc.get("terrain")
    if terrain is None:
        return 0
    quads_x, quads_y, heights, weights = terrain_samples(doc)
    vertices = (quads_x + 1) * (quads_y + 1)
    # Les images régénérées, pour qu'on les relise : jamais peintes, jamais suivies.
    images = FOOTPRINTS / map_id
    units = [max(0, min(65535, round(32768 + z * 100.0 * 128.0 / LANDSCAPE_Z_SCALE))) for z in heights]
    png(images / "hauteurs.png", quads_x + 1, quads_y + 1, units, 16)
    weight_bytes: list[int] = []
    for layer in terrain["layers"]:
        values = [round(w * 255) for w in weights[layer["name"]]]
        png(images / f"couche-{layer['name']}.png", quads_x + 1, quads_y + 1, values, 8)
        weight_bytes += values
    folder = f"{LEVEL_MAPS}/{map_id}_Terrain"
    material = terrain_material(f"{folder}/M_Terrain", terrain["layers"])
    step = terrain["resolution"] * 100.0
    x0, y0 = terrain["area"][0], terrain["area"][1]
    corner = frame.map_point([x0, y0, 0.0])
    east = frame.map_direction([1.0, 0.0, 0.0])
    south = frame.map_direction([0.0, 1.0, 0.0])
    if (east.x, east.y, south.x, south.y) != (1.0, 0.0, 0.0, 1.0):
        fail(f"terrain : le repère de la carte n'est pas celui du moteur (est {east}, sud {south}) ; à écrire")
    landscape = unreal.JadgSceneBuild.spawn_landscape(
        level.world, corner, unreal.Vector(step, step, LANDSCAPE_Z_SCALE), quads_x, quads_y, units,
        [layer["name"] for layer in terrain["layers"]], weight_bytes, material, folder)
    if landscape is None:
        fail("terrain : le Landscape n'a pas pu être créé")
    Level.name(landscape, "Terrain", "terrain")
    unreal.EditorAssetLibrary.save_directory(folder, only_if_is_dirty=False, recursive=True)
    plane = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane")
    water = flat_material(WATER_MATERIAL, unreal.LinearColor(0.05, 0.16, 0.22, 1.0), 0.05)
    for outline in doc.get("outlines", ()):
        if "water" not in outline:
            continue
        xs = [p[0] for p in outline["points"]]
        ys = [p[1] for p in outline["points"]]
        centre = [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, outline["water"]]
        actor = level.spawn(plane, frame.map_point(centre), unreal.Rotator(0, 0, 0), f"eau_{outline['name']}", "terrain",
                            unreal.Vector((max(xs) - min(xs)), (max(ys) - min(ys)), 1.0))
        actor.static_mesh_component.set_material(0, water)
        actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    log(f"terrain : {quads_x} × {quads_y} quads de {terrain['resolution']} m, {len(terrain['layers'])} couche(s), "
        f"{vertices} sommets ; images sous {images.relative_to(PROJECT_DIR).as_posix()}")
    return vertices


# --- Le ciel, la navigation, les personnages, le cadre ----------------------------------------

def place_sky(level: Level, doc: dict, frame: Frame) -> None:
    origin, flat = unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
    sun = level.spawn(unreal.DirectionalLight, unreal.Vector(0, 0, 3000), unreal.Rotator(0, -48, 0), "Soleil", "ciel")
    sun.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sun.light_component.set_editor_property("atmosphere_sun_light", True)
    lighting = doc.get("lighting", {})
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

    ground = doc.get("ground")
    if ground is not None:
        # Le sol lointain : un plan uni sous le dallage, jusqu'à l'horizon.
        tint = colour(ground["colour"])
        plane = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane")
        side = ground["size"]
        actor = level.spawn(plane, frame.map_point([0.0, 0.0, ground.get("height", -0.02)]), flat, "SolLointain", "ciel",
                            unreal.Vector(side, side, 1.0))
        actor.static_mesh_component.set_material(0, flat_material(
            GROUND_MATERIAL, unreal.LinearColor(tint.r / 255.0, tint.g / 255.0, tint.b / 255.0, 1.0)))

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
    if doc.get("entities"):
        # Une carte qui a des entités a de quoi solliciter : le contour de ce que le meneur désigne.
        settings.set_editor_property("weighted_blendables", unreal.WeightedBlendables(
            array=[unreal.WeightedBlendable(weight=1.0, object=outline_material())]))
    exposure.set_editor_property("settings", settings)

    day = level.spawn(game_class("JadgDayLight"), origin, flat, "Jour", "ciel")
    day.set_editor_property("table_file", doc["daylight"])
    day.set_editor_property("sun", sun)
    day.set_editor_property("sky", sky)
    day.set_editor_property("sun_scale", lighting.get("sunScale", 1.0))
    day.set_editor_property("ambient_scale", lighting.get("ambientScale", 1.0))
    # Les lumières que la carte de Core pose comme entité `light` prennent les mêmes intensités.
    day.set_editor_property("lamp_candelas", lighting.get("lampCandelas", 20.0))
    day.set_editor_property("fire_candelas", lighting.get("fireCandelas", 20.0))
    day.set_editor_property("east", frame.map_direction([1.0, 0.0, 0.0]))
    day.set_editor_property("up", frame.map_direction([0.0, 0.0, 1.0]))
    day.set_editor_property("south", frame.map_direction([0.0, 1.0, 0.0]))


def place_navigation(level: Level, doc: dict, frame: Frame) -> None:
    if "navigation" not in doc:
        return  # une carte sans marche (le socle) n'a pas de volume de navigation
    x0, y0, x1, y1 = doc["navigation"]["area"]
    height = doc["navigation"]["height"]
    floor = doc["navigation"].get("floor", -1.0)
    centre = frame.map_point([(x0 + x1) / 2, (y0 + y1) / 2, (floor + height) / 2])
    east, south = frame.map_point([x1 - x0, 0, 0]), frame.map_point([0, y1 - y0, 0])
    size = unreal.Vector(abs(east.x) + abs(south.x), abs(east.y) + abs(south.y), (height - floor) * 100.0)
    level.box_volume(unreal.NavMeshBoundsVolume, centre, size, "Navigation", "navigation")


def place_walker(level: Level, frame: Frame, walker, identifier: str, appearance: str, position: list[float],
                 heading: float, walk_speed: float) -> unreal.Actor:
    """Un personnage décrit par sa fiche d'apparence (LOT-1015, D-63) : l'acteur reçoit l'identifiant
    de la fiche et se pose lui-même au lancement (`AJadgWalker::Appearance`, corps par le créateur,
    clips, taille, armes). Le niveau ne lui donne que sa capsule, prise sur le corps de la fiche."""
    sheet = json.loads((ELEMENTS / "Rpg" / "appearances" / f"{appearance}.json").read_text(encoding="utf-8"))
    creator = json.loads((ELEMENTS / "Assets" / "Characters" / f"{sheet['creator']}.json").read_text(encoding="utf-8"))
    body_path = creator["bodies"].get(sheet["body"])
    if body_path is None:
        fail(f"{identifier} : corps « {sheet['body']} » inconnu du créateur {sheet['creator']}")
    body = unreal.EditorAssetLibrary.load_asset(body_path)
    if body is None:
        fail(f"{identifier} : corps absent du poste : {body_path} (scripts/assetsGeneration/import_mannequin_unreal.py)")
    bounds = body.get_bounds()
    scale = sheet["height"] / creator["referenceHeight"]
    half = bounds.box_extent.z * scale
    radius = max(20.0, min(bounds.box_extent.x, bounds.box_extent.y, half))
    location = frame.map_point(position)
    location.z += half
    actor = level.spawn(walker, location, frame.look(heading), identifier, "personnages")
    actor.capsule_component.set_editor_property("capsule_half_height", bounds.box_extent.z)
    actor.capsule_component.set_editor_property("capsule_radius", radius / scale)
    actor.set_editor_property("appearance", appearance)
    actor.set_editor_property("walk_speed", walk_speed * 100.0)
    return actor


def place_rigged(level: Level, frame: Frame, walker, library: Library, item: dict) -> None:
    """Un personnage par son maillage lié d'un kit et ses clips de repos et de marche (le lion de
    la porte, jusqu'au LOT-1025), et sa ronde."""
    # Le devant d'un modèle de la chaîne est +Z du .glb (le sud) ; un personnage du moteur avance vers +X.
    front = frame.map_direction([0.0, 1.0, 0.0])
    mesh_yaw = -math.degrees(math.atan2(front.y, front.x))
    skeletal, skins, clips = library.character(item["mesh"])
    bounds = skeletal.get_bounds()
    half = bounds.box_extent.z
    radius = max(20.0, min(bounds.box_extent.x, bounds.box_extent.y, half))
    feet = bounds.origin.z - bounds.box_extent.z
    location = frame.map_point(item["position"])
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
    actor.set_editor_property("walk_speed", item.get("walkSpeed", 3.0) * 100.0)
    actor.set_editor_property("party_rank", -1)
    actor.set_editor_property("entity_id", "")
    patrol = []
    for point in item.get("patrol", ()):
        stop = frame.map_point(point)
        stop.z += half
        patrol.append(stop)
    actor.set_editor_property("patrol", patrol)


def place_characters(level: Level, doc: dict, frame: Frame, library: Library) -> int:
    """Le groupe à l'entrée, par rang ; un PNJ par entité qui nomme son apparence."""
    walker = game_class("JadgWalker")
    count = 0
    party = doc.get("party")
    entry = jadg_map.entry_of(doc)
    if party is not None and entry is not None:
        foot = jadg_map.cell_centre(*entry, doc.get("origin"))
        for rank, appearance in enumerate(party["appearances"]):
            actor = place_walker(level, frame, walker, f"groupe-{rank + 1}", appearance, foot, party.get("heading", 90.0),
                                 party.get("walkSpeed", 3.0))
            actor.set_editor_property("party_rank", rank)
            actor.set_editor_property("entity_id", "")
            if rank == 0:
                level.spawn(unreal.PlayerStart, actor.get_actor_location(), frame.look(0.0), "Depart", "personnages")
            count += 1
    for item in doc.get("characters", ()):
        place_rigged(level, frame, walker, library, item)
        count += 1
    for entity in doc.get("entities", ()):
        if entity["type"] != "npc" or "appearance" not in entity:
            continue
        foot = jadg_map.cell_centre(entity["x"], entity["y"], doc.get("origin"))
        foot[2] = storey_z(doc, entity.get("storey", 0))
        actor = place_walker(level, frame, walker, f"pnj-{entity['id']}", entity["appearance"], foot,
                             entity.get("heading", 0.0), entity.get("walkSpeed", 3.0))
        actor.set_editor_property("party_rank", -1)
        actor.set_editor_property("entity_id", entity["id"])
        count += 1
    return count


def place_entities(level: Level, doc: dict, frame: Frame) -> None:
    """Un repère par entité (que l'auteur déplace dans l'éditeur, que `read_level.py` relit), et
    une boîte par volume (zone de combat, marqueur de rencontre)."""
    for entity in doc.get("entities", ()):
        foot = jadg_map.cell_centre(entity["x"], entity["y"], doc.get("origin"))
        foot[2] = storey_z(doc, entity.get("storey", 0))
        marker = level.spawn(unreal.TargetPoint, frame.map_point(foot), unreal.Rotator(0, 0, 0),
                             f"entite_{entity['id']}_{entity['type']}", "entites")
        marker.tags = [f"{MARKER_TAG}{entity['id']}"]
        volume = entity.get("volume")
        if volume is None:
            continue
        low, high = volume["min"], volume["max"]
        centre = [(low[k] + high[k]) / 2 for k in range(3)]
        box = level.spawn(unreal.TriggerBox, frame.map_point(centre), unreal.Rotator(0, 0, 0),
                          f"volume_{entity['id']}_{entity['type']}", "volumes")
        extent = frame.map_point([(high[k] - low[k]) / 2 for k in range(3)])
        shape = box.get_component_by_class(unreal.BoxComponent)
        shape.set_box_extent(unreal.Vector(abs(extent.x), abs(extent.y), abs(extent.z)))
        # Une boîte de déclenchement ne compte pas pour le maillage de navigation (défaut d'une forme).
        shape.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
        box.tags = [f"{VOLUME_TAG}{entity['id']}"]


def place_frame(level: Level, doc: dict, frame: Frame, map_id: str, path: Path) -> None:
    """Ce qui relie le niveau à sa carte de Core (`AJadgMapFrame`, LOT-1016) : sa grille, ses étages."""
    x, y = doc.get("origin", [0.0, 0.0])
    actor = level.spawn(game_class("JadgMapFrame"), frame.map_point([x, y, 0.0]), unreal.Rotator(0, 0, 0), "Carte", "carte")
    actor.set_editor_property("level_id", map_id)
    actor.set_editor_property("levels_root", jadg_map.levels_root(path))
    actor.set_editor_property("cell_size", jadg_map.CELL * 100.0)
    actor.set_editor_property("east", frame.map_direction([1.0, 0.0, 0.0]))
    actor.set_editor_property("south", frame.map_direction([0.0, 1.0, 0.0]))
    if doc.get("storeys"):
        actor.set_editor_property("storey_heights", [s["z"] * 100.0 for s in doc["storeys"]])


def place_shots(level: Level, doc: dict, frame: Frame) -> None:
    shot_class = game_class("JadgShot")
    for order, item in enumerate(doc.get("shots", ())):
        actor = level.spawn(shot_class, frame.map_point(item["target"]), frame.look(item["heading"], item["pitch"]),
                            f"Cadrage_{item['id']}", "cadrages")
        actor.set_editor_property("shot_id", item["id"])
        actor.set_editor_property("order", order)
        actor.set_editor_property("distance", item["distance"] * 100.0)


# --- L'empreinte ------------------------------------------------------------------------------

def rounded(values, step: float) -> list[float]:
    return [round(v / step) * step + 0.0 for v in values]


def actor_print(actor: unreal.Actor) -> dict:
    """Ce qu'un acteur du niveau est : sa classe, sa place, son maillage, ses réglages."""
    transform = actor.get_actor_transform()
    rotation = transform.rotation.rotator()
    entry = {
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "folder": str(actor.get_folder_path()),
        "location": rounded([transform.translation.x, transform.translation.y, transform.translation.z], 0.1),
        "rotation": rounded([rotation.pitch, rotation.yaw, rotation.roll], 0.01),
        "scale": rounded([transform.scale3d.x, transform.scale3d.y, transform.scale3d.z], 0.0001),
        "tags": sorted(str(tag) for tag in actor.tags),
    }
    parent = actor.get_attach_parent_actor()
    if parent is not None:
        entry["parent"] = parent.get_actor_label()
    if isinstance(actor, unreal.StaticMeshActor):
        mesh = actor.static_mesh_component.static_mesh
        entry["mesh"] = mesh.get_path_name() if mesh else ""
    instances = actor.get_component_by_class(unreal.InstancedStaticMeshComponent) if not isinstance(
        actor, unreal.StaticMeshActor) else None
    if instances is not None:
        entry["mesh"] = instances.static_mesh.get_path_name() if instances.static_mesh else ""
        digest = hashlib.sha256()
        for index in range(instances.get_instance_count()):
            placed = instances.get_instance_transform(index, True)
            digest.update(json.dumps(rounded([placed.translation.x, placed.translation.y, placed.translation.z], 0.1)).encode())
        entry["instances"] = instances.get_instance_count()
        entry["instancesDigest"] = digest.hexdigest()[:16]
    for name in ("level_id", "levels_root", "storey_heights", "appearance", "entity_id", "party_rank", "shot_id",
                 "distance", "prefab_id", "instance_id"):
        try:
            value = actor.get_editor_property(name)
        except Exception:  # noqa: BLE001 - une propriété que la classe n'a pas
            continue
        entry[name] = list(value) if isinstance(value, unreal.Array) else (round(value, 3) if isinstance(value, float) else value)
    light = actor.get_component_by_class(unreal.PointLightComponent)
    if light is not None:
        entry["light"] = [round(light.intensity, 3), round(light.attenuation_radius, 1), light.cast_shadows]
    box = actor.get_component_by_class(unreal.BoxComponent)
    if box is not None:
        extent = box.get_unscaled_box_extent()
        entry["extent"] = rounded([extent.x, extent.y, extent.z], 0.1)
    return entry


def footprint(world: unreal.World) -> tuple[str, list[dict]]:
    """L'empreinte du niveau : ses acteurs, triés par dossier et étiquette, et leur somme."""
    actors = [actor_print(a) for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
              if a.get_actor_label() not in ("", "WorldSettings") and not isinstance(a, (unreal.WorldSettings,))]
    # Les acteurs que le moteur ajoute de lui-même (le maillage de navigation, le monde) n'en sont pas.
    actors = [a for a in actors if a["class"] not in ("RecastNavMesh", "AbstractNavData", "WorldSettings",
                                                      "LevelScriptActor", "Brush", "DefaultPhysicsVolume",
                                                      "GameplayDebuggerPlayerManager", "ChaosDebugDrawActor",
                                                      "LandscapeGizmoActiveActor")]
    actors.sort(key=lambda a: (a["folder"], a["label"], a["class"]))
    digest = hashlib.sha256(json.dumps(actors, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return digest, actors


def write_footprint(map_id: str, digest: str, actors: list[dict], measures: dict) -> Path:
    path = FOOTPRINTS / f"{map_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"map": map_id, "digest": digest, "actors": len(actors), **measures,
                                "detail": actors}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return path


# --- Le contrôle sur le maillage de navigation -------------------------------------------------

def check_navigation(world: unreal.World, doc: dict, frame: Frame, map_id: str) -> list[str]:
    """Chaque entité où l'on se tient, chaque point d'arrivée, atteint depuis l'entrée par le
    maillage de navigation du niveau construit."""
    entry = jadg_map.entry_of(doc)
    if entry is None or "navigation" not in doc:
        return []
    start = frame.map_point(jadg_map.cell_centre(*entry, doc.get("origin")))
    start.z += 50.0
    targets = []
    for entity in doc.get("entities", ()):
        if entity["type"] in jadg_map.AREAS:
            continue
        foot = jadg_map.cell_centre(entity["x"], entity["y"], doc.get("origin"))
        foot[2] = storey_z(doc, entity.get("storey", 0)) + 0.5
        targets.append((entity, frame.map_point(foot)))
    unreachable = unreal.JadgSceneBuild.unreachable_points(world, start, [t[1] for t in targets])
    if list(unreachable) == [-1]:
        return [f"{map_id} : l'entrée n'est pas sur le maillage de navigation"]
    errors = []
    for index in unreachable:
        entity = targets[index][0]
        # Ce qu'on sollicite peut se tenir dans le plein (un portail dans un mur, un PNJ derrière son
        # étal) : seuls le point d'arrivée et l'entrée d'arène doivent être sur le maillage.
        if entity["type"] in ("spawnPoint", "arenaEntry"):
            errors.append(f"{map_id}#{entity['id']} ({entity['type']}) : inatteignable sur le maillage de navigation")
        else:
            log(f"{map_id}#{entity['id']} ({entity['type']}) : hors du maillage de navigation (sollicité à portée)")
    return errors


# --- La construction --------------------------------------------------------------------------

def build(map_id: str, doc: dict, path: Path, package: str | None = None, check: bool = False) -> dict:
    """Construit le niveau de `doc` sous `package` (défaut : celui de la carte) ; rend les mesures."""
    started = time.perf_counter()
    package = package or jadg_map.package(map_id)
    errors = jadg_map.validate(doc)
    if errors:
        fail(f"{map_id} : " + " ; ".join(errors))
    library = Library(doc.get("assetsRoot"))
    fixtures = Library(FIXTURE_ASSETS.relative_to(PROJECT_DIR).as_posix())
    frame = Frame(FIXTURE_ASSETS / FRAME_REFERENCE, fixtures.static_mesh(FRAME_REFERENCE))

    world = unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    if world is None:
        fail("le niveau vide n'a pas pu être créé")
    level = Level(world)
    placing = time.perf_counter()
    vertices = place_terrain(level, frame, doc, map_id)
    layered, missing = place_layers(level, frame, doc, library)
    objects = 0
    for item in doc.get("objects", ()):
        place_object(level, frame, doc, library, item, item.get("folder", "objets"))
        objects += 1
    filled = place_fills(level, frame, doc, library)
    prefabbed = place_prefabs(level, frame, doc, library)
    place_sky(level, doc, frame)
    place_navigation(level, doc, frame)
    characters = place_characters(level, doc, frame, library)
    place_entities(level, doc, frame)
    place_frame(level, doc, frame, map_id, path)
    place_shots(level, doc, frame)
    world.get_world_settings().set_editor_property("default_game_mode", game_class("JadgGameMode"))
    placed_seconds = time.perf_counter() - placing

    # Le niveau doit porter tout ce que la description pose : un objet perdu arrête le script.
    meshes = len([a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
                  if any(str(t).startswith(OBJECT_TAG) for t in a.tags) or a.get_attach_parent_actor() is not None])
    if meshes != objects + prefabbed:
        fail(f"{meshes} objets dans le niveau, {objects + prefabbed} attendus")
    if missing:
        log(f"{sum(missing.values())} pièce(s) sans maillage dans les kits, non posées : "
            + ", ".join(f"{name} ({count})" for name, count in sorted(missing.items())))

    problems = check_navigation(world, doc, frame, map_id) if check else []

    if not unreal.EditorLoadingAndSavingUtils.save_map(world, package):
        fail(f"{package} : le niveau n'a pas pu être sauvé")
    digest, actors = footprint(world)
    measures = {
        "seconds": round(time.perf_counter() - started, 1),
        "placingSeconds": round(placed_seconds, 1),
        "imports": library.imported + fixtures.imported,
        "importSeconds": round(library.import_seconds + fixtures.import_seconds, 1),
        "layerPieces": layered,
        "objects": objects,
        "fillTiles": filled,
        "prefabObjects": prefabbed,
        "characters": characters,
        "terrainVertices": vertices,
        "missingPieces": sum(missing.values()),
    }
    written = write_footprint(map_id if package == jadg_map.package(map_id) else package.rsplit("/", 1)[1],
                              digest, actors, measures)
    log(f"terminé : {package}, {len(actors)} acteurs, empreinte {digest[:16]}, {measures['seconds']} s "
        f"(dont {measures['importSeconds']} s d'import, {measures['placingSeconds']} s de pose) ; "
        f"{layered} pièces de couche, {objects} objets, {filled} dalles, {prefabbed} objets de préfabriqués, "
        f"{characters} personnage(s) ; {written.relative_to(PROJECT_DIR).as_posix()}")
    for problem in problems:
        unreal.log_error(f"[Scene] {problem}")
    if problems:
        raise RuntimeError(f"{len(problems)} erreur(s) sur le maillage de navigation")
    return {"digest": digest, **measures}


def main() -> None:
    map_id = master_import.command_line_option("JadgMap")
    if not map_id:
        fail("-JadgMap=<carte> attendu")
    path = jadg_map.find(map_id)
    if path is None:
        fail(f"carte « {map_id} » introuvable sous {', '.join(str(r) for r in jadg_map.LEVEL_ROOTS)}")
    build(map_id, jadg_map.read(path), path, check=master_import.command_line_option("JadgCheck") is not None)


if __name__ == "__main__":
    main()
