#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Écrit le groupe « Colisée » de la scène de la porte (LOT-1012) : l'anneau des pièces modulaires.

Le Colisée n'est plus une coque d'un seul tenant : `build_colosseum.py` en produit les pièces
(travées des trois ordres, attique, porte, quart de gradins, loge, sable, socle) à l'échelle du
Colisée de Rome, et ce script les **pose** — 80 travées par ordre sur l'ellipse, la porte plein
sud, les gradins quatre fois par symétrie — puis y ajoute ce qui vient d'ailleurs :

- les quatorze dieux **au maître** (`Master/Statues/`), dans les arcs du deuxième ordre de part et
  d'autre de la porte, chacun sur son socle, à 5,2 m de haut ; les deux lions gardiens sur les
  tours de la porte ;
- les bannières du kit de l'Arena of Fate, pendues à l'attique au-dessus des statues, l'empire
  au-dessus de la porte ; le culte des Sans-Dieux n'y flotte pas ;
- les feux : deux vasques à la porte, et sur le podium tout autour de l'arène, pour la nuit.

La sortie, `Source/Elements/Scenes/porte-1012/colisee.json`, est posée d'un bloc par
`build_scene_unreal.py` (`groups`). Repère : X vers l'est, **Y vers le haut**, Z vers le sud, en
mètres ; `yaw` en degrés autour de +Y ; origine au centre de l'arène, au niveau du sable. Le
repère de Blender des pièces (X est, Y nord, Z haut) s'y ramène par Z = −Y_blender.

Usage :
    python scripts/maps/build_gate_scene.py            # écrit colisee.json
    python scripts/maps/build_gate_scene.py --check    # code non nul si le fichier suivi diffère
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "assetsGeneration"))
import build_colosseum as colosseum  # noqa: E402

ELEMENTS = ROOT / "Source" / "Elements"
ASSETS = ELEMENTS / "Assets"
BUILT = "Built/colisee"
KIT = "Regions/central-empire/capital/arenarea/arena-of-fate/Scene"
MASTER_MANIFEST = ASSETS / "Master" / "manifest.json"
OUTPUT = ELEMENTS / "Scenes" / "porte-1012" / "colisee.json"

# Les dieux, dans l'ordre où ils se posent de part et d'autre de la porte (du plus proche au plus
# loin, à l'est puis à l'ouest) : les quatorze statues du kit de l'Arena of Fate, au maître.
GODS = ["statue-bauron", "statue-tamera", "statue-lumina", "statue-bas", "statue-duality", "statue-oigridh",
        "statue-dorsi", "statue-ba-ka", "statue-fruitful", "statue-aibidh", "statue-fumetsu",
        "statue-nature-spirits", "statue-glorious-one", "statue-breith"]
# Les bannières, de la porte vers les flancs ; l'empire au-dessus de la porte.
BANNERS = ["banner-empire", "banner-tanarean-empire", "banner-allied-forces", "banner-arcanum", "banner-darkall",
           "banner-freelands", "banner-bennet", "banner-kolbjorn", "banner-mage-tower", "banner-seashores",
           "banner-sindile", "banner-stravian", "banner-storm-islands", "banner-taii-maku", "banner-kepesh",
           "banner-tsvetan", "banner-yama"]
STATUE_HEIGHT = 5.2      # la hauteur d'un dieu dans son arc, en mètres
LION_HEIGHT = 5.0        # celle d'un lion sur sa tour
BANNER_SCALE = 2.1       # une bannière du kit fait 3,1 × 4 m ; pendue à l'attique, 6,6 × 8,4 m
PODIUM_FIRES = 10        # un feu sur le podium toutes les N travées
FIRE = {"color": "#ffb866", "radius": 13.0, "height": 2.2, "flicker": True, "always": True}


class GateSceneError(RuntimeError):
    """Une donnée d'entrée manque ou ne se relie pas."""


def glb_bounds(path: Path) -> tuple[list[float], list[float]]:
    """La boîte englobante d'un .glb, lue dans ses accesseurs."""
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
    return low, high


def scene_point(x: float, y: float, z: float) -> list[float]:
    """Un point de Blender (x est, y nord, z haut) dans le repère de la scène (X est, Y haut, Z sud)."""
    return [round(x, 4), round(z, 4), round(-y, 4)]


def piece(name: str) -> str:
    return f"{BUILT}/{name}.glb"


def placed(identifier: str, mesh: str, x: float, y: float, z: float, yaw: float = 0.0, scale: float = 1.0,
           **extra) -> dict:
    item = {"id": identifier, "mesh": mesh, "position": scene_point(x, y, z), "yaw": round(yaw % 360.0, 4),
            "scale": round(scale, 5)}
    item.update(extra)
    return item


def build(assets: Path = ASSETS) -> dict:
    spec = colosseum.SPEC
    bays = colosseum.ring_bays(spec)
    width = colosseum.bay_width(spec)
    n = spec["bays"]
    master = {p["id"]: p for p in json.loads((assets / "Master" / "manifest.json").read_text(encoding="utf-8"))["pieces"]}
    gate_bays = {k % n for k in range(-(spec["gateBays"] // 2), spec["gateBays"] // 2 + 1)}
    objects: list[dict] = []

    # Les travées : trois ordres puis l'attique, la porte à la place des travées du sud.
    floors = [0.0]
    for height in spec["orders"]:
        floors.append(floors[-1] + height)
    for bay in bays:
        k = bay["index"]
        cx, cy = bay["centre"]
        for order in range(3):
            if k in gate_bays:
                continue
            objects.append(placed(f"ordre-{order + 1}/travee-{k:02d}", piece(f"col-arcade-{order + 1}"),
                                  cx, cy, floors[order], bay["yaw"]))
        objects.append(placed(f"attique/travee-{k:02d}", piece("col-attic"), cx, cy, floors[3], bay["yaw"]))
    objects.append(placed("porte/porte", piece("col-gate"), 0.0, -spec["b"], 0.0, 0.0))

    # Les gradins, quatre fois par symétrie ; la loge au nord ; le sable.
    for identifier, yaw, mirrored in (("nord-est", 0.0, False), ("nord-ouest", 0.0, True),
                                      ("sud-ouest", 180.0, False), ("sud-est", 180.0, True)):
        item = placed(f"gradins/{identifier}", piece("col-cavea"), 0.0, 0.0, 0.0, yaw)
        if mirrored:
            item["mirrored"] = True
        objects.append(item)
    objects.append(placed("loge/loge", piece("col-loge"), 0.0, spec["innerB"], 0.0, 0.0))
    objects.append(placed("sol/sable", piece("col-sand"), 0.0, 0.0, 0.0, 0.0))

    # Les dieux dans les arcs du deuxième ordre, de part et d'autre de la porte.
    inward = spec["depth"] / 2 + 0.9
    half = len(GODS) // 2
    slots = [k for pair in zip(range(2, 2 + half), range(n - 2, n - 2 - half, -1)) for k in pair]
    for god, k in zip(GODS, slots):
        reference = master.get(f"Statues/{god}")
        if reference is None:
            raise GateSceneError(f"{god} : absent du manifeste du maître")
        low, high = glb_bounds(assets / reference["file"])
        scale = STATUE_HEIGHT / (high[1] - low[1])
        bay = bays[k]
        nx, ny = bay["normal"]
        x, y = bay["centre"][0] - nx * inward, bay["centre"][1] - ny * inward
        floor = floors[1]
        objects.append(placed(f"dieux/socle-{god}", piece("col-plinth"), x, y, floor, bay["yaw"]))
        objects.append(placed(f"dieux/{god}", reference["file"], x, y, floor + 0.94 - low[1] * scale, bay["yaw"], scale,
                              master=reference["id"], meshy=f"{reference['meshy_name']}_{reference['meshy_id']}"))

    # Les lions gardiens sur les tours de la porte.
    lion = master.get("Statues/portal-guardian-lion")
    if lion is None:
        raise GateSceneError("Statues/portal-guardian-lion : absent du manifeste du maître")
    low, high = glb_bounds(assets / lion["file"])
    scale = LION_HEIGHT / (high[1] - low[1])
    gate_width = width * spec["gateBays"]
    tower = (gate_width - spec["tunnelWidth"]) / 2
    tower_top = sum(spec["orders"]) + 1.42
    tower_y = -spec["b"] + (spec["depth"] - spec["gateProtrusion"]) / 2
    for side, sign in (("ouest", -1), ("est", 1)):
        objects.append(placed(f"gardiens/lion-{side}", lion["file"], sign * (gate_width - tower) / 2, tower_y,
                              tower_top - low[1] * scale, 0.0, scale, master=lion["id"],
                              meshy=f"{lion['meshy_name']}_{lion['meshy_id']}"))

    # Les bannières à l'attique : l'empire au-dessus de la porte, les autres de part et d'autre.
    slots = [0] + [k for pair in zip(range(1, 1 + len(BANNERS) // 2), range(n - 1, n - 1 - len(BANNERS) // 2, -1))
                   for k in pair]
    for banner, k in zip(BANNERS, slots):
        bay = bays[k]
        nx, ny = bay["normal"]
        x, y = bay["centre"][0] + nx * 0.55, bay["centre"][1] + ny * 0.55
        objects.append(placed(f"bannieres/{banner}", f"{KIT}/{banner}.glb", x, y, floors[3] + 3.4, bay["yaw"],
                              BANNER_SCALE))

    # Les feux : deux vasques devant la porte, et sur le podium tout autour.
    for side, sign in (("ouest", -1), ("est", 1)):
        objects.append(placed(f"feux/porte-{side}", f"{KIT}/af-pyre.glb", sign * (gate_width / 2 + 1.6),
                              -spec["b"] - spec["gateProtrusion"] - 1.2, 0.0, 0.0, 2.2, light=FIRE))
    for k in range(0, n, PODIUM_FIRES):
        angle = math.radians(270.0 + k * 360.0 / n)
        if k % n in gate_bays or (k + n // 2) % n in gate_bays:
            continue
        objects.append(placed(f"feux/podium-{k:02d}", f"{KIT}/af-pyre.glb",
                              (spec["innerA"] + 2.0) * math.cos(angle), (spec["innerB"] + 2.0) * math.sin(angle),
                              spec["podium"] + spec["rise"], 0.0, 1.5, light=FIRE))
    return {
        "version": 2,
        "comment": "Sortie de scripts/maps/build_gate_scene.py (LOT-1012) : ne pas modifier à la main. Repère : "
                   "X est, Y haut, Z sud, en mètres ; yaw en degrés autour de +Y ; origine au centre de l'arène, "
                   "au niveau du sable. Le Colisée de Rome : 189 × 156 m, 48 m, 80 travées.",
        "pieces": "Assets/Built/colisee/manifest.json",
        "spec": spec,
        "bayWidth": round(width, 4),
        "objects": objects,
    }


def render(scene: dict) -> str:
    return json.dumps(scene, ensure_ascii=False, indent=1) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="comparer au fichier suivi sans l'écrire")
    args = parser.parse_args(argv)
    try:
        text = render(build())
    except (GateSceneError, OSError, KeyError) as error:
        print(f"build_gate_scene : {error}", file=sys.stderr)
        return 1
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != text:
            print(f"build_gate_scene : {OUTPUT.relative_to(ROOT)} n'est pas à jour", file=sys.stderr)
            return 1
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"{OUTPUT.relative_to(ROOT)} : {len(json.loads(text)['objects'])} objets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
