#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Écrit la carte de contrôle d'une pièce de décor : la pièce seule, vue de ses quatre côtés (LOT-1019).

Sous une caméra qui tourne (D-49, D-56), une pièce n'a plus de dos caché : un retour Meshy au dos
pauvre se voit. Le gabarit de commande d'une zone (`Planning/standards/gabarit-commande-zone.md`)
demande donc, pour chaque pièce reçue, **quatre captures de contrôle** — la face, la droite, le
dos, la gauche —, à midi et à 22 h, avant qu'elle n'entre dans une carte.

Pour chaque pièce dont la fiche donne une famille du standard (`sheet` du manifeste des maîtres,
fiches du manifeste des bibliothèques), ce script écrit une carte v5,
`Source/Test/Fixtures/Exploration/Levels/controle/<pièce>.json` : un sol uni, la pièce posée au
centre à la hauteur de sa fiche (`height`, en mètres ; à défaut, telle que livrée), le ciel et la
table du jour de la porte, et quatre cadrages autour d'elle. `build.ps1` la construit et la capture :

    python scripts/maps/build_piece_check.py
    powershell scripts/build.ps1 -Unreal -Map controle/arenarea-palazzo-terracotta -Capture

Le devant d'une pièce est le sud de la carte (+Z du `.glb`, `build_level.py`) : la face se voit
d'un cadrage tourné vers le nord.

Usage :
    python scripts/maps/build_piece_check.py           # écrit les cartes de contrôle
    python scripts/maps/build_piece_check.py --check   # code non nul si une carte suivie diffère
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "maps"))
import build_gate_scene  # noqa: E402
import jadg_map  # noqa: E402

ASSETS = ROOT / "Source" / "Elements" / "Assets"
MANIFESTS = (ASSETS / "Master" / "manifest.json", ASSETS / "Library" / "manifest.json")
OUTPUT = jadg_map.TRIAL_LEVELS / "controle"
# Les quatre côtés : le cadrage regarde vers ce cap (0 : le nord), et voit donc le côté opposé.
SIDES = (("face", 0.0), ("droite", 90.0), ("dos", 180.0), ("gauche", 270.0))
GRID = 24  # la grille de Core : 36 m de côté, l'entrée dans un coin


def glb_size(path: Path) -> list[float]:
    """Largeur, hauteur, profondeur d'un .glb (repère glTF, Y vers le haut), lues dans ses accesseurs."""
    with path.open("rb") as stream:
        stream.read(12)
        length, _ = struct.unpack("<II", stream.read(8))
        document = json.loads(stream.read(length))
    low, high = [math.inf] * 3, [-math.inf] * 3
    for mesh in document["meshes"]:
        for primitive in mesh["primitives"]:
            accessor = document["accessors"][primitive["attributes"]["POSITION"]]
            low = [min(low[k], accessor["min"][k]) for k in range(3)]
            high = [max(high[k], accessor["max"][k]) for k in range(3)]
    return [high[k] - low[k] for k in range(3)]


def pieces(assets: Path = ASSETS) -> list[dict]:
    """Les pièces à contrôler : celles dont la fiche nomme une famille du standard 3D."""
    found = []
    for manifest in (assets / m.relative_to(ASSETS) for m in MANIFESTS):
        if not manifest.is_file():
            continue
        for piece in json.loads(manifest.read_text(encoding="utf-8")).get("pieces", []):
            sheet = piece.get("sheet", piece)
            if sheet.get("family"):
                found.append({"id": piece["id"], "file": piece["file"], "height": sheet.get("height")})
    return found


def control_map(piece: dict, assets: Path = ASSETS) -> dict:
    """La carte de contrôle d'une pièce."""
    width, height, depth = glb_size(assets / piece["file"])
    scale = piece["height"] / height if piece.get("height") else 1.0
    tall = height * scale
    reach = max(width, depth) * scale
    distance = round(max(12.0, reach * 2.4), 1)
    slug = Path(piece["file"]).stem
    item = {"id": slug, "mesh": piece["file"], "position": [0.0, 0.0, 0.0], "yaw": 0.0}
    if piece.get("height"):
        item["height"] = piece["height"]
    else:
        item["scale"] = 1.0
    half = GRID * jadg_map.CELL / 2
    return {
        "format": jadg_map.FORMAT,
        "version": jadg_map.VERSION,
        "name": f"Controle-{slug}",
        "comment": (f"La carte de contrôle de {piece['id']} (LOT-1019) : la pièce seule, vue de ses quatre côtés à midi "
                    f"et à 22 h, avant d'entrer dans une carte. Sortie de scripts/maps/build_piece_check.py, jamais à la "
                    f"main ; le ciel et la lumière sont ceux de la porte."),
        "width": GRID,
        "height": GRID,
        "origin": [-half, -half],
        "nextEntityId": 1,
        "tiles": [{"x": 0, "y": GRID - 1, "type": "entry"}],
        "entities": [],
        "objects": [item],
        "lighting": build_gate_scene.LIGHTING,
        "daylight": jadg_map.DAYLIGHT,
        "ground": {"comment": "Le sol de la porte.", "colour": build_gate_scene.GROUND["colour"], "size": 4000.0, "height": -0.02},
        "shots": [{"id": side, "target": [0.0, 0.0, round(tall * 0.45, 2)], "heading": heading, "pitch": 8.0,
                   "distance": distance} for side, heading in SIDES],
        "hours": ["12:00", "22:00"],
    }


def files(assets: Path = ASSETS) -> dict[Path, str]:
    out = {}
    for piece in pieces(assets):
        if not (assets / piece["file"]).is_file():
            continue  # le .glb est hors Git : sans lui, la carte ne se mesure pas
        out[OUTPUT / f"{Path(piece['file']).stem}.json"] = jadg_map.dumps(control_map(piece, assets))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="comparer aux fichiers suivis sans les écrire")
    args = parser.parse_args(argv)
    stale = False
    for path, text in files().items():
        errors = jadg_map.validate(json.loads(text))
        if errors:
            print(f"build_piece_check : {path.name} : {' ; '.join(errors)}", file=sys.stderr)
            return 1
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                print(f"build_piece_check : {path.relative_to(ROOT)} n'est pas à jour", file=sys.stderr)
                stale = True
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"{path.relative_to(ROOT).as_posix()} : {len(json.loads(text)['shots'])} cadrages")
    return 1 if stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
