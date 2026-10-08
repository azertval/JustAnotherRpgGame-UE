#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Donne à chaque modèle d'un dossier ses **cartes de matière** : le relief et la rugosité-métal.

Le standard 3D (`Planning/standards/style-3d.md`, §4) veut depuis le 4 octobre 2026 (D-46) une
matière complète : la couleur de base, une carte de **relief** (normales, repère tangent) et une
carte **occlusion-rugosité-métal** (rouge, vert, bleu), incorporées au `.glb`. Ce script les y
met, sans Blender et sans toucher à la géométrie ; une couleur de base **opaque** livrée en PNG
est remise en JPEG (qualité 93, sans sous-échantillonnage), les autres restent telles quelles :

- **un modèle reçu de Meshy** garde les cartes de son original : elles en sont relues, ramenées à
  `--size` pixels (1024) et remises dans la copie installée — ses coordonnées de texture n'ont pas
  changé, seule sa pose a été normalisée ; sa couleur de base est ramenée à la même taille ;
- **un modèle construit par script** n'en a pas : elles se **dérivent de sa couleur de base**. Le
  relief suit la clarté (un joint sombre est un creux), l'occlusion assombrit les creux, la
  rugosité et le métal viennent de la **table des matières** (`--matters`) : par case pour un atlas
  en grille, par nom de pièce sinon.

Le script est rejouable : un modèle qui porte déjà ses cartes est refait à l'identique. Deux
modèles qui partagent une couleur de base reçoivent les mêmes octets de cartes, et le moteur n'en
garde qu'une texture (`hmi::MeshBatch`).

Usage :
    python scripts/assetsGeneration/material_maps.py DOSSIER [--matters TABLE.json]
        [--originals RELEVE.json ...] [--size 1024] [--only NOM,NOM]

`RELEVE.json` est un relevé d'import (`sculptures-measurements.json`) : il nomme l'original de
chaque pièce. Dépendances : numpy, Pillow (outil de production, pas de CI).
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

import struct

GLB_MAGIC = b"glTF"
CHUNK_JSON = b"JSON"
CHUNK_BIN = b"BIN\x00"


def read_glb(data: bytes) -> tuple[dict, bytes]:
    """Le document JSON et le bloc binaire d'un `.glb` 2.0 (venu de `reduce_model.py`, retiré au LOT-1015)."""
    magic, version, length = struct.unpack_from("<4sII", data, 0)
    if magic != GLB_MAGIC or version != 2 or length > len(data):
        raise ValueError("pas un fichier .glb 2.0")
    json_length, json_kind = struct.unpack_from("<I4s", data, 12)
    if json_kind != CHUNK_JSON:
        raise ValueError("bloc JSON absent")
    document = json.loads(data[20:20 + json_length])
    binary = b""
    offset = 20 + json_length
    if offset + 8 <= length:
        binary_length, binary_kind = struct.unpack_from("<I4s", data, offset)
        if binary_kind == CHUNK_BIN:
            binary = data[offset + 8:offset + 8 + binary_length]
    return document, binary


def write_glb(document: dict, binary: bytes) -> bytes:
    """Un `.glb` de `document` et de `binary`, chaque bloc complété à quatre octets."""
    text = json.dumps(document, separators=(",", ":")).encode("utf-8")
    text += b" " * ((4 - len(text) % 4) % 4)
    binary += b"\x00" * ((4 - len(binary) % 4) % 4)
    body = (struct.pack("<I4s", len(text), CHUNK_JSON) + text
            + struct.pack("<I4s", len(binary), CHUNK_BIN) + binary)
    return struct.pack("<4sII", GLB_MAGIC, 2, 12 + len(body)) + body

MATTERS_DEFAUT = Path(__file__).resolve().parent / "arena_fate_matters.json"
JPEG_QUALITY = 90
# La qualité du JPEG d'une couleur de base opaque : sans sous-échantillonnage des couleurs.
COLOR_QUALITY = 93
# Ce que la clarté d'un pixel déplace sa normale, pour un relief de force 1.
RELIEF_SLOPE = 16.0
# Ce qu'un creux perd de lumière d'ambiance, au plus.
OCCLUSION_DEPTH = 0.6


# --- Les images ------------------------------------------------------------------------------------
def _blur_wrapped(values: np.ndarray, sigma: float) -> np.ndarray:
    """Un flou gaussien séparable qui se referme sur les bords : la matière se répète."""
    radius = max(1, int(sigma * 3))
    offsets = np.arange(-radius, radius + 1)
    kernel = np.exp(-(offsets ** 2) / (2 * sigma * sigma))
    kernel /= kernel.sum()
    out = values
    for axis in (0, 1):
        padded = np.concatenate([out.take(range(-radius, 0), axis=axis), out,
                                 out.take(range(radius), axis=axis)], axis=axis)
        out = np.apply_along_axis(lambda line: np.convolve(line, kernel, mode="valid"), axis, padded)
    return out


def derive_cell(color: np.ndarray, matter: dict) -> tuple[np.ndarray, np.ndarray]:
    """Le relief et l'occlusion-rugosité-métal d'une case de matière, de sa couleur (0 à 1)."""
    height, width = color.shape[:2]
    luminance = color[:, :, 0] * 0.299 + color[:, :, 1] * 0.587 + color[:, :, 2] * 0.114
    smooth = _blur_wrapped(luminance, 1.5)
    relief = float(matter["relief"])
    # L'image a ses lignes vers le bas, la carte son vert vers le haut : une clarté qui croît vers
    # la droite penche la normale à gauche, une clarté qui croît vers le bas la penche en haut.
    slope_x = (np.roll(smooth, -1, axis=1) - np.roll(smooth, 1, axis=1)) * 0.5
    slope_y = (np.roll(smooth, -1, axis=0) - np.roll(smooth, 1, axis=0)) * 0.5
    scale = RELIEF_SLOPE * relief * min(width, height) / 512.0
    normal = np.stack([-slope_x * scale, slope_y * scale, np.ones_like(smooth)], axis=2)
    normal /= np.linalg.norm(normal, axis=2, keepdims=True)
    hollow = np.clip(_blur_wrapped(luminance, 6.0) - smooth, 0.0, 1.0)
    occlusion = 1.0 - np.clip(hollow * 7.0 * relief, 0.0, OCCLUSION_DEPTH)
    roughness = np.clip(float(matter["roughness"]) + hollow * 0.6 * relief, 0.04, 1.0)
    metallic = np.full_like(smooth, float(matter["metallic"]))
    return normal * 0.5 + 0.5, np.stack([occlusion, roughness, metallic], axis=2)


def derive_maps(color: Image.Image, cells: list[list[dict]]) -> tuple[Image.Image, Image.Image]:
    """Les deux cartes d'une image de couleur découpée en `cells` (lignes du haut vers le bas)."""
    pixels = np.asarray(color.convert("RGB"), dtype=np.float32) / 255.0
    rows, columns = len(cells), len(cells[0])
    height, width = pixels.shape[0] // rows, pixels.shape[1] // columns
    normal = np.zeros_like(pixels)
    material = np.zeros_like(pixels)
    for row in range(rows):
        for column in range(columns):
            window = (slice(row * height, (row + 1) * height),
                      slice(column * width, (column + 1) * width))
            normal[window], material[window] = derive_cell(pixels[window], cells[row][column])
    def as_image(values):
        return Image.fromarray(np.rint(values * 255.0).astype(np.uint8), "RGB")

    return as_image(normal), as_image(material)


def resized_normal(image: Image.Image, size: int) -> Image.Image:
    """Une carte de relief ramenée à `size`, ses normales remises à la longueur 1."""
    if max(image.size) > size:
        image = image.resize((size, size * image.size[1] // image.size[0]), Image.LANCZOS)
    vectors = np.asarray(image.convert("RGB"), dtype=np.float32) / 127.5 - 1.0
    vectors /= np.maximum(np.linalg.norm(vectors, axis=2, keepdims=True), 1e-6)
    return Image.fromarray(np.rint((vectors * 0.5 + 0.5) * 255.0).astype(np.uint8), "RGB")


def encode(image: Image.Image) -> bytes:
    """Le JPEG d'une carte, sans sous-échantillonnage des couleurs : ce sont des données."""
    out = io.BytesIO()
    image.save(out, "JPEG", quality=JPEG_QUALITY, subsampling=0)
    return out.getvalue()


# --- Le conteneur ----------------------------------------------------------------------------------
def _view(document: dict, binary: bytes, index: int) -> bytes:
    view = document["bufferViews"][index]
    start = view.get("byteOffset", 0)
    return binary[start:start + view["byteLength"]]


def _image_of(document: dict, binary: bytes, reference: dict | None) -> bytes | None:
    if reference is None:
        return None
    image = document["images"][document["textures"][reference["index"]]["source"]]
    return _view(document, binary, image["bufferView"]) if "bufferView" in image else None


def material_images(document: dict, binary: bytes) -> dict:
    """Les octets des images de la première matière : `color`, `normal`, `material`, et si le
    rouge de `material` est son occlusion."""
    material = document["materials"][0]
    pbr = material.get("pbrMetallicRoughness", {})
    rough = pbr.get("metallicRoughnessTexture")
    occlusion = material.get("occlusionTexture")
    return {
        "color": _image_of(document, binary, pbr.get("baseColorTexture")),
        "normal": _image_of(document, binary, material.get("normalTexture")),
        "material": _image_of(document, binary, rough),
        "occluded": (rough is not None and occlusion is not None and
                     document["textures"][occlusion["index"]]["source"] ==
                     document["textures"][rough["index"]]["source"]),
    }


def compact_color(pixels: bytes, cache: dict, largest: int = 0) -> tuple[bytes, str]:
    """La couleur de base, en JPEG si elle est opaque : un PNG opaque pèse cinq à dix fois plus,
    et le même atlas est incorporé à des dizaines de pièces. Une image à transparence — la foule,
    une bannière — reste telle quelle, comme une image déjà en JPEG."""
    key = ("color", hash(pixels), len(pixels), largest)
    if key not in cache:
        image = Image.open(io.BytesIO(pixels))
        smaller = 0 < largest < max(image.size)
        if pixels[:3] == b"\xff\xd8\xff" and not smaller:
            cache[key] = (pixels, "image/jpeg")
            return cache[key]
        if smaller:
            image = image.resize((largest * image.size[0] // max(image.size),
                                  largest * image.size[1] // max(image.size)), Image.LANCZOS)
        opaque = image.mode in ("RGB", "L") or (
            image.mode == "RGBA" and image.getchannel("A").getextrema()[0] == 255)
        if opaque:
            out = io.BytesIO()
            image.convert("RGB").save(out, "JPEG", quality=COLOR_QUALITY, subsampling=0)
            cache[key] = (out.getvalue(), "image/jpeg")
        elif smaller:
            out = io.BytesIO()
            image.save(out, "PNG")
            cache[key] = (out.getvalue(), "image/png")
        else:
            cache[key] = (pixels, "image/png")
    return cache[key]


def with_maps(document: dict, binary: bytes, normal: bytes, material: bytes,
              color: tuple[bytes, str] | None = None) -> tuple[dict, bytes]:
    """Le modèle avec ces deux cartes pour seules images en plus de sa couleur de base, que
    `color` (octets, type) remplace s'il est donné."""
    matter = document["materials"][0]
    pbr = matter.setdefault("pbrMetallicRoughness", {})
    base = document["textures"][pbr["baseColorTexture"]["index"]]
    color_image = document["images"][base["source"]]
    color_bytes, color_mime = color or (_view(document, binary, color_image["bufferView"]),
                                        color_image.get("mimeType", "image/png"))
    image_views = {image["bufferView"] for image in document["images"] if "bufferView" in image}
    # Les vues de géométrie restent, à leur rang ; celles des images sont refaites à la suite.
    kept = [index for index in range(len(document["bufferViews"])) if index not in image_views]
    renumbered = {old: new for new, old in enumerate(kept)}
    rebuilt = bytearray()
    views = []

    def append(content: bytes, source: dict | None) -> int:
        nonlocal rebuilt
        rebuilt += b"\x00" * ((4 - len(rebuilt) % 4) % 4)
        view = {key: value for key, value in (source or {}).items()
                if key not in ("byteOffset", "byteLength")}
        view.update({"buffer": 0, "byteOffset": len(rebuilt), "byteLength": len(content)})
        rebuilt += content
        views.append(view)
        return len(views) - 1

    for index in kept:
        append(_view(document, binary, index), document["bufferViews"][index])
    for accessor in document.get("accessors", []):
        if "bufferView" in accessor:
            accessor["bufferView"] = renumbered[accessor["bufferView"]]
    sampler = base.get("sampler")
    document["images"] = [
        {"bufferView": append(color_bytes, None), "mimeType": color_mime},
        {"bufferView": append(normal, None), "mimeType": "image/jpeg"},
        {"bufferView": append(material, None), "mimeType": "image/jpeg"},
    ]
    document["textures"] = [{"source": index} | ({} if sampler is None else {"sampler": sampler})
                            for index in range(3)]
    pbr["baseColorTexture"] = {"index": 0}
    pbr["metallicRoughnessTexture"] = {"index": 2}
    pbr["metallicFactor"] = 1.0
    pbr["roughnessFactor"] = 1.0
    matter["normalTexture"] = {"index": 1}
    matter["occlusionTexture"] = {"index": 2}
    document["bufferViews"] = views
    document["buffers"] = [{"byteLength": len(rebuilt) + ((4 - len(rebuilt) % 4) % 4)}]
    return document, bytes(rebuilt)


# --- La table des matières -------------------------------------------------------------------------
def cells_for(name: str, size: tuple[int, int], table: dict) -> list[list[dict]]:
    """Les matières de l'image de couleur de `name` : par nom de pièce, par atlas, ou la défaut."""
    matters = table["matters"]
    for prefix, matter in table.get("pieces", {}).items():
        if name.startswith(prefix):
            return [[matters[matter]]]
    for atlas in table.get("atlases", []):
        if list(size) == atlas["size"]:
            rows, columns = atlas["rows"], atlas["columns"]
            grid = [[matters[atlas["cells"][row * columns + column]] for column in range(columns)]
                    for row in range(rows)]
            return grid[::-1]  # la table compte ses rangées du bas, l'image du haut
    return [[matters["default"]]]


def enrich(path: Path, table: dict, originals: dict[str, Path], size: int, cache: dict) -> str:
    """Met ses cartes au modèle `path` ; retourne d'où elles viennent."""
    document, binary = read_glb(path.read_bytes())
    images = material_images(document, binary)
    if images["color"] is None:
        return "sans couleur de base, laissé"
    # Les cartes dérivées le sont de la couleur telle que le modèle la portera : un second passage
    # redonne les mêmes octets.
    original = originals.get(path.stem)
    # Une sculpture de l'auteur a sa couleur à la taille de ses autres cartes : à l'échelle du jeu
    # elle tient trois cents pixels, et une texture de 2048 px pèse quatre fois plus en mémoire.
    compact = compact_color(images["color"], cache, size if original is not None else 0)
    if original is not None:
        source_document, source_binary = read_glb(original.read_bytes())
        source = material_images(source_document, source_binary)
        if source["normal"] is None or source["material"] is None:
            raise ValueError(f"{original} : l'original n'a pas ses cartes de matière")
        normal = encode(resized_normal(Image.open(io.BytesIO(source["normal"])), size))
        rough = Image.open(io.BytesIO(source["material"])).convert("RGB")
        if max(rough.size) > size:
            rough = rough.resize((size, size * rough.size[1] // rough.size[0]), Image.LANCZOS)
        if not source["occluded"]:
            channels = list(rough.split())
            channels[0] = Image.new("L", rough.size, 255)
            rough = Image.merge("RGB", channels)
        maps, origin = (normal, encode(rough)), f"de l'original {original.name}"
    else:
        color = Image.open(io.BytesIO(compact[0]))
        cells = cells_for(path.stem, color.size, table)
        if len(cells) == 1 and len(cells[0]) == 1 and cells[0][0].get("flat"):
            # Une matière sans relief ni reflet — un tissu, une foule — n'a pas à payer deux
            # cartes à sa taille : une petite carte neutre, que toutes ces pièces partagent.
            color = Image.new("RGB", (64, 64), (128, 128, 128))
        key = (hash(compact[0]), len(compact[0]), json.dumps(cells, sort_keys=True))
        if key not in cache:
            derived_normal, derived_material = derive_maps(color, cells)
            cache[key] = (encode(derived_normal), encode(derived_material))
        maps, origin = cache[key], f"dérivées ({len(cells) * len(cells[0])} matière(s))"
    document, binary = with_maps(document, binary, *maps, color=compact)
    path.write_bytes(write_glb(document, binary))
    return origin


def originals_of(reports: list[Path]) -> dict[str, Path]:
    """L'original de chaque pièce, d'après les relevés d'import."""
    found: dict[str, Path] = {}
    for report in reports:
        for measure in json.loads(report.read_text(encoding="utf-8"))["measurements"]:
            found[measure["piece"]] = Path(measure["source"])
    return found


def enrich_folder(folder: Path, matters: Path = MATTERS_DEFAUT, reports: list[Path] | None = None,
                  size: int = 1024, only: set[str] | None = None) -> dict[str, str]:
    """Met leurs cartes à tous les `.glb` de `folder` ; retourne, par modèle, leur provenance."""
    table = json.loads(matters.read_text(encoding="utf-8"))
    originals = originals_of(reports or [])
    cache: dict = {}
    done = {}
    for path in sorted(folder.glob("*.glb")):
        if only and path.stem not in only:
            continue
        done[path.name] = enrich(path, table, originals, size, cache)
    return done


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("folder", type=Path)
    parser.add_argument("--matters", type=Path, default=MATTERS_DEFAUT)
    parser.add_argument("--originals", type=Path, nargs="*", default=[])
    parser.add_argument("--size", type=int, default=1024)
    parser.add_argument("--only", default="")
    arguments = parser.parse_args()
    only = {name for name in arguments.only.split(",") if name}
    for name, origin in enrich_folder(arguments.folder, arguments.matters, arguments.originals,
                                      arguments.size, only or None).items():
        print(f"{name} : cartes {origin}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
