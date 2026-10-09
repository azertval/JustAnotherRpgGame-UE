# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""La fiche d'une pièce de décor et la matière qu'un `.glb` porte (LOT-1019).

Module **sans moteur** : `import_scenery_unreal.py` (dans l'éditeur) et `build_master_manifest.py`
(hors de lui) le partagent, et ses tests tournent sans Unreal.

**La fiche d'une pièce** est l'entrée qui la décrit dans le manifeste de son kit, et dit tout ce
que le moteur et le jeu doivent savoir d'elle, sans geste dans l'éditeur :

| Champ | Ce qu'il dit |
|---|---|
| `mesh` (ou `file`) | le `.glb`, au maître, relatif au manifeste ou à la racine des assets |
| `family` | la famille du standard 3D (`01` à `10`, §6) |
| `class` | `floor`, `wide`, `tall` ou `fx` : ce que le jeu fait de la pièce |
| `footprint` | l'emprise, en cases de 1,5 m : colonnes puis rangées |
| `tactical` | `open`, `difficult`, `cover`, `obstacle` ou `solid` |
| `light` | la lumière qu'elle porte : couleur `#rrggbb`, portée (`range` ou `radius`) et hauteur en mètres, `flicker`, `always` |
| `material` | sa matière, lue dans le `.glb` par `material_report` : les cartes présentes, leurs formats et tailles, l'alpha |
| `library` | pour une pièce d'une bibliothèque du moteur (D-55) : `provider` (`Fab`, `Megascans`), `identifier`, `licence`, `url` |

Une fiche incomplète ne s'installe pas : `validate` dit ce qui manque, champ par champ.

**La matière** d'un `.glb` se lit dans son en-tête et ses images : couleur de base, relief,
occlusion-rugosité-métal (glTF 2.0 : rugosité dans le vert, métal dans le bleu, occlusion dans le
rouge quand `occlusionTexture` cite la même image), facteurs, mode d'alpha. Rien n'est deviné : une
carte absente est dite absente.
"""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

FAMILIES = {
    "01": "Sols", "02": "Façades et murs", "03": "Colonnes", "04": "Accès", "05": "Balustrades",
    "06": "Pièces maîtresses", "07": "Végétal", "08": "Mobilier", "09": "Bâtiments", "10": "Seuils",
}
CLASSES = ("floor", "wide", "tall", "fx")
TACTICAL = ("open", "difficult", "cover", "obstacle", "solid")
PROVIDERS = ("Fab", "Megascans")
ROLES = ("baseColor", "normal", "orm")
GLB_MAGIC = 0x46546C67
JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942


class SceneryError(ValueError):
    """Une fiche ou un `.glb` qui ne se lit pas."""


def read_glb(path: Path, with_binary: bool = True) -> tuple[dict, bytes]:
    """Le document glTF d'un `.glb` et son bloc binaire (vide si `with_binary` est faux)."""
    with path.open("rb") as stream:
        header = stream.read(12)
        if len(header) < 12 or struct.unpack("<I", header[:4])[0] != GLB_MAGIC:
            raise SceneryError(f"{path.name} : pas un .glb")
        length, kind = struct.unpack("<II", stream.read(8))
        if kind != JSON_CHUNK:
            raise SceneryError(f"{path.name} : premier bloc non JSON")
        document = json.loads(stream.read(length))
        binary = b""
        if with_binary:
            head = stream.read(8)
            if len(head) == 8:
                size, kind = struct.unpack("<II", head)
                if kind == BIN_CHUNK:
                    binary = stream.read(size)
    return document, binary


def image_size(content: bytes) -> tuple[int, int] | None:
    """Largeur et hauteur d'une image PNG ou JPEG, lues dans son en-tête."""
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", content[16:24])
    if content[:2] == b"\xff\xd8":
        cursor = 2
        while cursor + 9 < len(content):
            if content[cursor] != 0xFF:
                return None
            marker = content[cursor + 1]
            length = struct.unpack(">H", content[cursor + 2:cursor + 4])[0]
            if marker in (0xC0, 0xC1, 0xC2):
                height, width = struct.unpack(">HH", content[cursor + 5:cursor + 9])
                return width, height
            cursor += 2 + length
    return None


def _image(document: dict, binary: bytes, texture_index: int) -> dict:
    texture = document["textures"][texture_index]
    source = document["images"][texture["source"]]
    if "bufferView" not in source:
        raise SceneryError("image externe au .glb : une pièce porte ses images")
    view = document["bufferViews"][source["bufferView"]]
    start = view.get("byteOffset", 0)
    content = binary[start:start + view["byteLength"]]
    return {
        "image": texture["source"],
        "mime": source.get("mimeType", ""),
        "size": list(image_size(content) or (0, 0)),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "content": content,
    }


def material_slots(document: dict, binary: bytes) -> list[dict]:
    """Chaque matière du `.glb`, dans l'ordre du document : son nom, ses images par rôle, ses
    facteurs, son alpha. Le contenu des images est gardé (`content`) pour l'import."""
    slots = []
    for index, material in enumerate(document.get("materials", [])):
        pbr = material.get("pbrMetallicRoughness", {})
        images = {}
        if "baseColorTexture" in pbr:
            images["baseColor"] = _image(document, binary, pbr["baseColorTexture"]["index"])
        if "normalTexture" in material:
            images["normal"] = _image(document, binary, material["normalTexture"]["index"])
        occlusion = False
        if "metallicRoughnessTexture" in pbr:
            images["orm"] = _image(document, binary, pbr["metallicRoughnessTexture"]["index"])
            if "occlusionTexture" in material:
                occluding = document["textures"][material["occlusionTexture"]["index"]]["source"]
                occlusion = occluding == images["orm"]["image"]
        for key, ref in (("baseColorTexture", pbr.get("baseColorTexture")), ("normalTexture", material.get("normalTexture"))):
            if ref is not None and ref.get("texCoord", 0) != 0:
                raise SceneryError(f"matière {index} : {key} sur un second jeu d'UV, non pris en charge")
        alpha = material.get("alphaMode", "OPAQUE")
        slots.append({
            "index": index,
            "name": material.get("name", ""),
            "images": images,
            "baseColorFactor": [float(v) for v in pbr.get("baseColorFactor", [1.0, 1.0, 1.0, 1.0])],
            "metallicFactor": float(pbr.get("metallicFactor", 1.0)),
            "roughnessFactor": float(pbr.get("roughnessFactor", 1.0)),
            "occlusionStrength": float(material.get("occlusionTexture", {}).get("strength", 1.0)) if occlusion else 0.0,
            "normalScale": float(material.get("normalTexture", {}).get("scale", 1.0)),
            "alpha": "masked" if alpha in ("MASK", "BLEND") else "opaque",
            "alphaCutoff": float(material.get("alphaCutoff", 0.5)),
            "doubleSided": bool(material.get("doubleSided", False)),
        })
    if not slots:
        raise SceneryError("aucune matière : une pièce porte sa matière")
    return slots


def triangles(document: dict) -> int:
    accessors = document.get("accessors", [])
    count = 0
    for mesh in document.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            if "indices" in primitive:
                count += accessors[primitive["indices"]]["count"] // 3
            else:
                count += accessors[primitive["attributes"]["POSITION"]]["count"] // 3
    return count


def material_report(path: Path) -> dict:
    """La matière d'un `.glb` telle qu'une fiche l'écrit : les cartes de chaque matière, leurs
    formats et leurs tailles, l'alpha ; et ce qui manque au standard (§4 : cartes complètes)."""
    document, binary = read_glb(path)
    slots = material_slots(document, binary)
    report = []
    missing = set()
    for slot in slots:
        maps = {role: {"mime": image["mime"], "size": image["size"]} for role, image in slot["images"].items()}
        missing.update(role for role in ROLES if role not in maps)
        report.append({"name": slot["name"], "maps": maps, "alpha": slot["alpha"],
                       "occlusion": slot["occlusionStrength"] > 0.0})
    return {"slots": report, "complete": not missing, "missing": sorted(missing)}


def validate(piece: dict, label: str = "") -> list[str]:
    """Ce qui manque ou se trompe dans la fiche d'une pièce, en phrases."""
    name = label or piece.get("id", "?")
    errors = []
    if not (piece.get("mesh") or piece.get("file")):
        errors.append(f"{name} : ni `mesh` ni `file`")
    family = piece.get("family")
    if family is not None and family not in FAMILIES:
        errors.append(f"{name} : famille « {family} » hors du standard (01 à 10)")
    if piece.get("class") is not None and piece["class"] not in CLASSES:
        errors.append(f"{name} : classe « {piece['class']} » inconnue ({', '.join(CLASSES)})")
    footprint = piece.get("footprint")
    if footprint is not None and (not isinstance(footprint, list) or len(footprint) != 2
                                  or not all(isinstance(v, int) and v > 0 for v in footprint)):
        errors.append(f"{name} : emprise en cases entières attendue, [colonnes, rangées]")
    if piece.get("tactical") is not None and piece["tactical"] not in TACTICAL:
        errors.append(f"{name} : type tactique « {piece['tactical']} » inconnu")
    light = piece.get("light")
    if light is not None:
        colour = str(light.get("color", ""))
        if len(colour) != 7 or not colour.startswith("#"):
            errors.append(f"{name} : lumière sans couleur #rrggbb")
        if not any(isinstance(light.get(k), (int, float)) for k in ("range", "radius")):
            errors.append(f"{name} : lumière sans portée (`range` ou `radius`, en mètres)")
        if not isinstance(light.get("height"), (int, float)):
            errors.append(f"{name} : lumière sans hauteur (`height`, en mètres)")
    library = piece.get("library")
    if library is not None:
        for key in ("provider", "identifier", "licence"):
            if not library.get(key):
                errors.append(f"{name} : pièce de bibliothèque sans `{key}`")
        if library.get("provider") and library["provider"] not in PROVIDERS:
            errors.append(f"{name} : bibliothèque « {library['provider']} » non admise par D-55 ({', '.join(PROVIDERS)})")
    return errors


def sheet_of(piece: dict) -> dict:
    """La fiche d'une pièce, quel que soit son manifeste : l'entrée elle-même pour un kit ou une
    bibliothèque ; pour un maître (manifeste de `build_master_manifest.py`, dont `family` est le
    dossier du kit : `Statues`, `Weapons`, `Scenery`), son objet `sheet` et son fichier."""
    if "meshy_id" in piece:
        return {"id": piece.get("id"), "file": piece.get("file"), **piece.get("sheet", {})}
    return piece


def library_manifest(path: Path) -> list[dict]:
    """Les fiches des pièces de bibliothèque (`Assets/Library/manifest.json`), contrôlées."""
    if not path.is_file():
        return []
    pieces = json.loads(path.read_text(encoding="utf-8")).get("pieces", [])
    errors = []
    for piece in pieces:
        errors += validate(piece)
        if "library" not in piece:
            errors.append(f"{piece.get('id', '?')} : une pièce de bibliothèque cite sa source (`library`)")
    if errors:
        raise SceneryError(" ; ".join(errors))
    return pieces
