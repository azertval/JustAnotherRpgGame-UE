#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Regenerate the complete Arena of Fate from its approved painted witness.

Normal Python --prepare writes the proposed map to Saved, without replacing gameplay.
The Unreal commandlet imports through build_level.Library, checks navigation, saves
seven always-loaded storeys and commits the canonical JSON only after success.
Outputs: /Game/Maps/Levels/central-empire/capital/arenarea/arena-of-fate*,
/Game/Kit/Built/arena-fate-modern, /Game/Kit/Built/arena-fate-props,
/Game/Bibliotheque/Commun/ArenaWickedWitness/Materials (approved 10 October painted finishes),
/Game/ArenaFateModern (map-local environment, imported scenery and atmosphere).
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import shutil
import struct
import sys
from copy import deepcopy
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "Source/Elements/Assets"
GEOMETRY = ASSETS / "Built/arena-fate-modern/manifest.json"
PROPS = ASSETS / "Built/arena-fate-props/manifest.json"
MAP_ID = "central-empire/capital/arenarea/arena-of-fate"
SOURCE = ROOT / "Source/Elements/Levels" / (MAP_ID + ".json")
PACKAGE = "/Game/Maps/Levels/" + MAP_ID
REPORTS = ROOT / "Saved/Jadg/arena-fate-modern"
PROPOSAL = REPORTS / "proposed-map.json"
ORIGINAL = REPORTS / "source-before-modern.json"
APPROVAL = (
    ROOT
    / "Planning/versions/v0.1.0/v0.0.4-lieux-de-la-demo/annexes/LOT-106/wicked-approval-20261010.json"
)
LEGACY_SCENE = "Regions/central-empire/capital/arenarea/arena-of-fate/Scene/"
GODS = (
    "breith",
    "bauron",
    "bas",
    "dorsi",
    "ba-ka",
    "fruitful",
    "aibidh",
    "fumetsu",
    "nature-spirits",
    "glorious-one",
    "tamera",
    "lumina",
    "duality",
    "oigridh",
)
EFFIGIES = ("cthraxis", "krynnethoth", "droggath", "zulvath")
RENDER_REVISION = "wicked-imperial-approved-20261010"
AMBIENT_CUBE = "/Game/ArenaFateModern/Lighting/T_AmbientGradient_v1"
INTERIOR_PROFILES = {
    "vestiaire": {"candelas": 240.0, "radius": 14.0},
    "prison": {"candelas": 200.0, "radius": 14.0},
    "salle-des-morts": {"candelas": 200.0, "radius": 14.0},
    "chapelle": {"candelas": 180.0, "radius": 14.0},
    "corridor": {"candelas": 160.0, "radius": 12.0},
}

sys.path.insert(0, str(ROOT / "scripts/maps"))
sys.path.insert(0, str(ROOT / "scripts/assetsGeneration"))
import jadg_map  # noqa: E402
from arena_fate_modern_gameplay import remap_gameplay, validate_remap  # noqa: E402
import arena_cavea as cavea  # noqa: E402
import arena_undercroft as undercroft  # noqa: E402


def read_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    for mesh in manifest["meshes"]:
        source = path.parent / mesh["file"]
        if not source.is_file():
            raise RuntimeError(f"Missing source mesh: {source}")
        if (
            mesh.get("sha256")
            and hashlib.sha256(source.read_bytes()).hexdigest() != mesh["sha256"]
        ):
            raise RuntimeError(f"Mesh differs from its QA manifest: {source}")
    return manifest


def source_document() -> dict:
    # The archive is a recovery copy, not the authority for later gameplay edits.
    # Remapping is idempotent once the internal portals have been removed.
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def floor_index(z: float, storeys: list[dict]) -> int:
    """Logical owner at/below absolute foot height, including non-sorted basements."""
    candidates = [i for i, floor in enumerate(storeys) if floor["z"] <= z + 0.01]
    return (
        max(candidates, key=lambda i: storeys[i]["z"])
        if candidates
        else min(range(len(storeys)), key=lambda i: storeys[i]["z"])
    )


def relative_object(item: dict, mesh: str, storeys: list[dict]) -> dict:
    absolute = list(item["position"])
    index = item.get("storey", floor_index(absolute[2], storeys))
    if isinstance(index, str):
        index = next(i for i, storey in enumerate(storeys) if storey["name"] == index)
    result = {
        "id": item["id"],
        "mesh": mesh,
        "storey": index,
        "position": [absolute[0], absolute[1], absolute[2] - storeys[index]["z"]],
        "yaw": item.get("yaw", 0.0),
        "folder": item.get("role", "architecture"),
    }
    for key in (
        "scale",
        "height",
        "pitch",
        "roll",
        "mirrored",
        "entity",
        "lightCandelas",
        "lightRadius",
        "lightingZone",
        "light",
        "flame",
    ):
        if key in item:
            result[key] = deepcopy(item[key])
    return result


def local_position(
    origin: list[float], yaw: float, offset: tuple[float, float, float]
) -> list[float]:
    angle = math.radians(yaw)
    c, s = math.cos(angle), math.sin(angle)
    return [
        origin[0] + c * offset[0] + s * offset[1],
        origin[1] - s * offset[0] + c * offset[1],
        origin[2] + offset[2],
    ]


def furnishings(metadata: dict) -> list[dict]:
    """Authored props beside routes and room centres, never random navigation blockers."""
    result = []
    props = {
        item["id"]: item
        for item in json.loads(PROPS.read_text(encoding="utf-8"))["meshes"]
    }
    replacements = {
        "afp-amphora-pair": "afp-service-amphora-pair",
        "afp-loge-chair": "afp-loge-chair-sculpted",
        "afp-loge-table": "afp-loge-table-sculpted",
    }
    reserved = list(zip(metadata.get("route", []), metadata.get("route", [])[1:]))
    reserved += [(p, p) for p in metadata.get("navigationTargets", [])]
    for loge in metadata.get("loges", []):
        reserved.append(
            (local_position(loge["position"], loge["yaw"], (0, 5, 0)), loge["position"])
        )

    def add(mesh: str, position: list, yaw: float = 0, label: str = "", **kwargs):
        alternative = replacements.get(mesh)
        if alternative in props and (
            mesh != "afp-loge-table" or label.startswith("loge-")
        ):
            mesh = alternative
        result.append(
            {
                "id": label or f"{mesh}-{len(result):03d}",
                "meshId": mesh,
                "position": position,
                "yaw": yaw,
                "role": "accessoires",
                **kwargs,
            }
        )

    def footprint(item, margin=0.0):
        low, high = props[item["meshId"]]["bounds"]
        return [
            local_position(item["position"], item["yaw"], (x, y, 0))[:2]
            for x, y in (
                (low[0] - margin, low[1] - margin),
                (high[0] + margin, low[1] - margin),
                (high[0] + margin, high[1] + margin),
                (low[0] - margin, high[1] + margin),
            )
        ]

    def separated(first, second):
        for polygon in (first, second):
            for i in (0, 1):
                a, b = polygon[i], polygon[i + 1]
                axis = (b[1] - a[1], a[0] - b[0])
                p = [sum(v[k] * axis[k] for k in (0, 1)) for v in first]
                q = [sum(v[k] * axis[k] for k in (0, 1)) for v in second]
                if max(p) < min(q) or max(q) < min(p):
                    return True
        return False

    def blocks_segment(item, first, last):
        # Sweep a 1.1 m horizontal route reserve and the measured player's height.
        low, high = props[item["meshId"]]["bounds"]
        angle = math.radians(-item["yaw"])
        c, s = math.cos(angle), math.sin(angle)
        points = []
        for p in (first, last):
            dx, dy, dz = [p[k] - item["position"][k] for k in range(3)]
            points.append((c * dx + s * dy, -s * dx + c * dy, dz))
        limits = [
            (low[0] - 1.1, high[0] + 1.1),
            (low[1] - 1.1, high[1] + 1.1),
            (low[2] - 1.96, high[2]),
        ]
        start, stop = 0.0, 1.0
        for k, (minimum, maximum) in enumerate(limits):
            delta = points[1][k] - points[0][k]
            if abs(delta) < 1e-9:
                if not minimum <= points[0][k] <= maximum:
                    return False
            else:
                a, b = sorted(
                    ((minimum - points[0][k]) / delta, (maximum - points[0][k]) / delta)
                )
                start, stop = max(start, a), min(stop, b)
                if start > stop:
                    return False
        return True

    def enrich(mesh, position, yaw, label, room=None, gallery=False):
        alternative = replacements.get(mesh)
        if alternative in props and (
            mesh != "afp-loge-table" or label.startswith("loge-")
        ):
            mesh = alternative
        item = {"meshId": mesh, "position": position, "yaw": yaw}
        polygon = footprint(item)
        if gallery:
            # Entire footprint stays on the real ring; north/south stair slots stay open.
            inner_a, inner_b = (85, 69) if position[2] == 0 else (87, 71)
            if any(
                (x / 93.5) ** 2 + (y / 77) ** 2 > 0.988
                or (x / inner_a) ** 2 + (y / inner_b) ** 2 < 1.01
                or abs(x) < 12
                for x, y in polygon
            ):
                return
        if room is not None:
            local = [(p[0] - room[0], p[1] - room[1]) for p in polygon]
            if any(abs(x) > 11.2 or abs(y) > 8.45 for x, y in local):
                return
            # Reserve the four real column bases, not just the room walls.
            for x in (-8, 8):
                for y in (-7, 7):
                    column = [
                        (room[0] + x + dx, room[1] + y + dy)
                        for dx, dy in (
                            (-0.48, -0.48),
                            (0.48, -0.48),
                            (0.48, 0.48),
                            (-0.48, 0.48),
                        )
                    ]
                    if not separated(footprint(item, 0.15), column):
                        return
        if any(blocks_segment(item, first, last) for first, last in reserved):
            return
        low, high = props[mesh]["bounds"]
        for other in result:
            other_low, other_high = props[other["meshId"]]["bounds"]
            if (
                position[2] + high[2] <= other["position"][2] + other_low[2]
                or other["position"][2] + other_high[2] <= position[2] + low[2]
            ):
                continue
            if not separated(footprint(item, 0.12), footprint(other)):
                return
        add(mesh, position, yaw, label)

    for zone in metadata.get("zones", []):
        name, p = zone["id"], zone["position"]
        if name.startswith("vestiaire") or name == "prison":
            # Aménagés par arena_undercroft.py et ludus_props (20 octobre 2026).
            continue
        if name.startswith("vestiaire"):
            for mesh, offset in (
                ("afp-weapon-rack", (-8, -6, 0)),
                ("afp-shield-pair", (-5, -6, 0)),
                ("afp-bench", (7, -5, 0)),
                ("afp-chest", (8, 5, 0)),
                ("afp-amphora-pair", (-8, 6, 0)),
                ("afp-practice-stand", (5, 5, 0)),
            ):
                add(mesh, local_position(p, 0, offset), label=name + "-" + mesh)
            if "afp-training-staves" in props:
                add(
                    "afp-training-staves",
                    local_position(p, 0, (-8, -6, 0)),
                    label=name + "-training-staves",
                )
            if "afp-folded-linen" in props:
                add(
                    "afp-folded-linen",
                    local_position(p, 0, (7, -5.04, 0.475)),
                    label=name + "-folded-linen",
                )
        elif name == "prison":
            for mesh, offset in (
                ("afp-chain-set", (7, 5, 0)),
                ("afp-pallet", (-8, 6, 0)),
                ("afp-barrel", (8, -6, 0)),
                ("afp-wall-lamp", (-6, -8.5, 1.7)),
            ):
                add(mesh, local_position(p, 0, offset), label=name + "-" + mesh)
        elif name == "salle-des-morts":
            for mesh, offset in (
                ("afp-neutral-sarcophagus", (6, -5, 0)),
                ("afp-maintenance-cart", (-7, 5, 0)),
                ("afp-rope-coil", (-6, -5, 0)),
                ("afp-crate-stack", (8, 5, 0)),
            ):
                add(mesh, local_position(p, 0, offset), label=name + "-" + mesh)
        elif name.startswith("chapelle"):
            add(
                "afp-brazier",
                local_position(p, 0, (-7, -5, 0)),
                label=name + "-brasero",
            )
            add(
                "afp-neutral-sarcophagus",
                local_position(p, 0, (7, 4, 0)),
                label=name + "-tombe",
            )
            add(
                "afp-chain-set",
                local_position(p, 0, (7, -5, 0)),
                label=name + "-chaines",
            )
    for loge in metadata.get("loges", []):
        p, yaw, name = loge["position"], loge["yaw"], loge["delegation"]
        # Keep the centre (also a navigation probe) and the rear entrance clear.
        # The loge's arena balustrade is local -Y; prop fronts were authored +Y.
        for mesh, offset in (
            ("afp-loge-chair", (-2.1, -1.0, 0)),
            ("afp-loge-chair", (2.1, -1.0, 0)),
            ("afp-loge-table", (-2.1, 0.9, 0)),
            ("afp-lectern", (2.5, 0.7, 0)),
        ):
            add(
                mesh,
                local_position(p, yaw, offset),
                yaw + 180 if mesh == "afp-loge-chair" else yaw,
                f"loge-{name}-{mesh}-{len(result)}",
            )
        if "afp-loge-lantern" in props:
            for side in (-1, 1):
                enrich(
                    "afp-loge-lantern",
                    local_position(p, yaw, (side * 3.05, 0.0, 0)),
                    yaw,
                    f"loge-{name}-lanterne-{side}",
                )

    # Functional reserves occupy the room sides, away from centre/door routes.
    for zone in metadata.get("zones", []):
        name, p = zone["id"], zone["position"]
        if name.startswith("vestiaire") or name == "prison":
            continue
        if name.startswith("vestiaire"):
            group = [
                ("afp-bench", (-5, 4, 0)),
                ("afp-shield-pair", (-4, 6.6, 0)),
                ("afp-weapon-rack", (3, -6, 0)),
                ("afp-chest", (4, 6, 0)),
                ("afp-crate-stack", (-9.8, 2.8, 0)),
                ("afp-barrel", (-9.8, 4.5, 0)),
                ("afp-amphora-pair", (9.8, -1.5, 0)),
                ("afp-rope-coil", (9.8, 0, 0)),
            ]
        elif name == "prison":
            group = [
                ("afp-pallet", (-8, 3, 0)),
                ("afp-pallet", (-5, 6.5, 0)),
                ("afp-pallet", (4, 6.5, 0)),
                ("afp-chest", (8, 4, 0)),
                ("afp-barrel", (9.5, 1, 0)),
                ("afp-amphora-pair", (-5, -6.3, 0)),
            ]
        elif name == "salle-des-morts":
            group = [
                ("afp-neutral-sarcophagus", (5, 5, 0)),
                ("afp-loge-table", (-8, -3, 0)),
                ("afp-chest", (9, -3, 0)),
                ("afp-barrel", (-9.5, 2.6, 0)),
                ("afp-amphora-pair", (5, 2.7, 0)),
                ("afp-lectern", (-5, 3, 0)),
            ]
        else:
            # Chapels retain tombs, bound effigies, chains and braziers. A
            # service-room storage station would obscure their distinct use.
            group = []
        for index, (mesh, offset) in enumerate(group):
            enrich(
                mesh,
                local_position(p, 0, offset),
                0,
                f"reserve-{name}-{index:02d}",
                room=p,
            )

    # Sparse, composed seating/urn stations on the outer gallery side.
    # Cardinal doors, stair courts and the loge level remain unencumbered.
    for z in (0, 24, 36):
        for index in range(24):
            angle = math.tau * (index + 0.5) / 24
            if min(abs(math.cos(angle)), abs(math.sin(angle))) < 0.25:
                continue
            p = [91.3 * math.cos(angle), 74.8 * math.sin(angle), z]
            yaw = 270 - math.degrees(
                math.atan2(math.sin(angle) / 77, math.cos(angle) / 93.5)
            )
            for mesh, dx in (("afp-bench", -1.1), ("afp-amphora-pair", 1.1)):
                enrich(
                    mesh,
                    local_position(p, yaw, (dx, 0, 0)),
                    yaw,
                    f"galerie-{z}-{index:02d}-{mesh}",
                    gallery=True,
                )

    # Working velum stations belong on the terrace's outer edge. The same
    # footprint/route reserves reject any part extending beyond its real floor.
    for index in range(4):
        angle = math.pi / 4 + index * math.pi / 2
        p = [91.3 * math.cos(angle), 74.8 * math.sin(angle), 46.8]
        yaw = 270 - math.degrees(
            math.atan2(math.sin(angle) / 77, math.cos(angle) / 93.5)
        )
        for mesh, dx in (("afp-velum-winch", -0.85), ("afp-velum-anchor", 0.85)):
            if mesh in props:
                enrich(
                    mesh,
                    local_position(p, yaw, (dx, 0, 0)),
                    yaw,
                    f"terrasse-velum-{index}-{mesh}",
                    gallery=True,
                )

    for sign in (-1, 1):
        for side in (-1, 1):
            p, yaw = [side * 13, sign * 73.5, 0], 180 if sign > 0 else 0
            for index, (mesh, offset) in enumerate(
                (
                    ("afp-maintenance-cart", (-2.3, 0, 0)),
                    ("afp-crate-stack", (0, 0, 0)),
                    ("afp-barrel", (2.1, 0, 0)),
                    ("afp-rope-coil", (0, 1.15, 0)),
                )
            ):
                enrich(
                    mesh,
                    local_position(p, yaw, offset),
                    yaw,
                    f"entretien-porte-{sign}-{side}-{index}",
                    gallery=True,
                )

    # Six room fixtures are seated on a solid wall face, never in an opening.
    for zone in metadata.get("zones", []):
        if zone["id"].startswith("chapelle") and zone["id"] not in (
            "chapelle-0",
            "chapelle-3",
        ):
            continue
        p = zone["position"]
        yaw = 180 if p[1] > 0 else 0
        position = local_position(p, yaw, (5, -8.55, 1.9))
        enrich("afp-wall-lamp", position, yaw, "applique-" + zone["id"])

    # The approved service witness is much smaller than these 24 x 18 m rooms.
    # Four real wall fixtures cover preparation/cell rooms; two behind each
    # effigy complement its existing offset brazier. Never occupy a doorway.
    for zone in metadata.get("zones", []):
        name, p = zone["id"], zone["position"]
        kind = next(
            (key for key in INTERIOR_PROFILES if name.startswith(key)), "corridor"
        )
        sides = [1 if p[1] > 0 else -1] if kind == "chapelle" else [-1, 1]
        for side in sides:
            for slot, x in enumerate((-5.0, 5.0)):
                position = local_position(p, 0, (x, side * 8.58, 1.9))
                # Reuse an applique already on this face instead of stacking
                # a second mesh and point light at the same bracket.
                if any(
                    item["meshId"] == "afp-wall-lamp"
                    and math.dist(item["position"][:2], position[:2]) < 1.3
                    and abs(item["position"][2] - position[2]) < 0.8
                    for item in result
                ):
                    continue
                add(
                    "afp-wall-lamp",
                    position,
                    180 if side > 0 else 0,
                    f"interior-applique-{name}-{side}-{slot}",
                    lightingZone=kind,
                )

    # Small motivated pools also mark the long axial approaches. These X spans
    # are solid wall segments between room doors, not the door/stair apertures.
    for z, prefix, xs in (
        (-6.0, "under", (-54.0, -44.0, -9.0, 9.0, 44.0, 54.0)),
        (-12.0, "cat", (-39.0, -8.0, 8.0, 39.0)),
    ):
        for x in xs:
            side = 1 if x > 0 else -1
            add(
                "afp-wall-lamp",
                [x, side * 4.58, z + 1.9],
                180 if side > 0 else 0,
                f"interior-applique-corridor-{prefix}-{x:g}",
                lightingZone="corridor",
            )

    # Six exterior fixtures attach to actual arcade pier transforms at three levels.
    geometry = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    arcades = [
        item
        for item in geometry["objects"]
        if item.get("role") == "arcade" and item["meshId"].startswith("afm-arcade")
    ]
    for z in (0, 12, 24):
        for angle in (math.pi / 4, 5 * math.pi / 4):
            target = [93.5 * math.cos(angle), 77 * math.sin(angle), z]
            choices = [item for item in arcades if item["position"][2] == z]
            pier = min(
                choices,
                key=lambda item: math.dist(
                    local_position(
                        item["position"], item["yaw"], (6 * item["scale"][0], 0, 0)
                    ),
                    target,
                ),
            )
            position = local_position(
                pier["position"], pier["yaw"], (3.45 * pier["scale"][0], -0.57, 2.1)
            )
            enrich(
                "afp-wall-lamp",
                position,
                pier["yaw"] + 180,
                f"applique-galerie-{z}-{angle:.3f}",
            )
    return result


def heritage(metadata: dict) -> list[dict]:
    result = []
    statues = metadata.get("statues", [])
    if len(statues) != len(GODS):
        raise RuntimeError(
            "The full architecture must provide fourteen statue foot anchors"
        )
    for god, anchor in zip(GODS, statues, strict=True):
        result.append(
            {
                "id": "dieu-" + god,
                "mesh": f"Master/Statues/statue-{god}.glb",
                "role": "divinites",
                **anchor,
            }
        )
    loges = {loge["delegation"]: loge for loge in metadata.get("loges", [])}
    if len(loges) != 13:
        raise RuntimeError("Thirteen delegation loges are required")
    for delegation, loge in loges.items():
        mesh = LEGACY_SCENE + f"banner-{delegation}.glb"
        raw = (ASSETS / mesh).read_bytes()
        length = int.from_bytes(raw[12:16], "little")
        gltf = json.loads(raw[20 : 20 + length])
        positions = [
            gltf["accessors"][primitive["attributes"]["POSITION"]]
            for item in gltf["meshes"]
            for primitive in item["primitives"]
        ]
        low = [min(accessor["min"][k] for accessor in positions) for k in range(3)]
        high = [max(accessor["max"][k] for accessor in positions) for k in range(3)]
        native_height = high[1] - low[1]  # glTF +Y is vertical.
        if native_height <= 0:
            raise RuntimeError(f"Banner has no measurable height: {mesh}")
        # Fix the original emblem to the front balustrade without crossing its
        # promenade floor. Rear entry (+Y) and the central anchor stay clear.
        height, top = 1.04, 1.20
        scale = height / native_height
        # The model turns 180 degrees relative to the loge. Seat its closest
        # depth face outside the front cornice, using its measured GLB bounds.
        x = (low[0] + high[0]) * 0.5 * scale
        y = -2.82 + low[2] * scale
        banner_anchor = metadata.get("bannerAnchors", {}).get(delegation)
        position = local_position(loge["position"], loge["yaw"], (x, y, top - height))
        if banner_anchor is not None:
            height = banner_anchor.get("height", height)
            position = local_position(
                loge["position"], loge["yaw"], tuple(banner_anchor["localPosition"])
            )
        result.append(
            {
                "id": "banniere-" + delegation,
                "mesh": mesh,
                "position": position,
                "yaw": loge["yaw"] + 180,
                "height": height,
                "storey": "tribunes",
                "role": "bannieres",
            }
        )
    for alliance, delegation in (
        ("tanarean-empire", "kolbjorn"),
        ("allied-forces", "sindile"),
        ("darkall", "storm-islands"),
        ("arcanum", "kepesh"),
    ):
        loge = loges[delegation]
        result.append(
            {
                "id": "alliance-" + alliance,
                "mesh": LEGACY_SCENE + f"banner-{alliance}.glb",
                "position": local_position(
                    loge["position"], loge["yaw"], (-3.87, 0, 0.4)
                ),
                "yaw": loge["yaw"] + 90,
                "height": 2.7,
                "role": "alliances",
            }
        )
    for index, x in enumerate((-6.5, 6.5)):
        result.append(
            {
                "id": f"lion-gardien-{index}",
                "mesh": "Master/Statues/portal-guardian-lion.glb",
                "position": [x, 74.5, 0],
                "height": 3.8,
                "yaw": 180,
                "mirrored": bool(index),
                "role": "gardiens",
            }
        )
    for name, zone in zip(
        EFFIGIES,
        [z for z in metadata["zones"] if z["id"].startswith("chapelle")],
        strict=True,
    ):
        positive_side = zone["position"][1] > 0
        result.append(
            {
                "id": "effigie-" + name,
                "mesh": f"Master/Statues/effigy-{name}.glb",
                "position": local_position(
                    zone["position"], 0, (0, 6 if positive_side else -6, 0)
                ),
                "height": 3.8,
                "yaw": 180 if positive_side else 0,
                "role": "effigies",
            }
        )
        result.append(
            {
                "id": "liens-effigie-" + name,
                "mesh": LEGACY_SCENE + f"af-effigy-chains-{name}.glb",
                "position": list(result[-1]["position"]),
                "yaw": result[-1]["yaw"],
                "role": "liens",
            }
        )
    return result


def required_completion(metadata: dict) -> list[dict]:
    """Small physical fixtures outside the preserved routes and room entrances."""
    result = []
    # Les cellules de la prison sont dans afm-prison (arena_undercroft.py, 20 octobre 2026).
    for zone in metadata["zones"]:
        if zone["id"].startswith("vestiaire"):
            result.append(
                {
                    "id": "fontaine-" + zone["id"],
                    "meshId": "afp-wash-fountain",
                    "position": [zone["position"][0] + 11.69, zone["position"][1], -6],
                    "yaw": 270,
                    "role": "accessoires",
                }
            )
    for god, anchor in zip(GODS, metadata["statues"], strict=True):
        foot = [
            anchor["position"][0],
            anchor["position"][1],
            anchor["position"][2] - 1.7,
        ]
        result.append(
            {
                "id": "inscription-" + god,
                "meshId": "afp-nameplate-" + god,
                "position": local_position(foot, anchor["yaw"], (0, 1.025, 0.455)),
                "yaw": anchor["yaw"],
                "role": "ornament",
            }
        )
        if god == "fumetsu":
            result.append(
                {
                    "id": "socle-distinct-fumetsu",
                    "meshId": "afp-fumetsu-plinth-collar",
                    "position": [foot[0], foot[1], foot[2] + 1.30],
                    "yaw": anchor["yaw"] + 180,
                    "role": "ornament",
                }
            )
    return result


AOF_PILOT = "Built/aof-pilot-001-048/"
AOF_EXTENSION = "Built/aof-extension-049-192/"
FIRE = {"color": "#ffb45c", "height": 1.25, "radius": 9.0, "always": True}
TORCH = {"color": "#ffb066", "height": 1.0, "radius": 7.0, "always": True}


def aof(number: int) -> str:
    """Une piece unitaire du catalogue de l'arene (aof-catalogue.json), deja au projet."""
    return (AOF_PILOT if number <= 48 else AOF_EXTENSION) + f"SM_AOF_{number:03d}.glb"


def aof_dressing() -> list[dict]:
    """Les pieces unitaires du catalogue (LOT-106, 192 types) qui garnissent l'arene : braseros
    de la coursive, mats du velum, torches des passages, abords du parvis."""
    result = []
    # Un brasero votif entre deux statues : les feux du pourtour du livre.
    for index, (position, yaw) in enumerate(cavea.podium_braziers()):
        result.append({"id": f"brasero-coursive-{index:02d}", "mesh": aof(79), "position": position, "yaw": yaw,
                       "role": "accessoires", "light": FIRE, "flame": 0.16})
    # Les mats du velum : embase, deux troncons de 5 m, tete a cordages, sur la terrasse.
    for index, t in enumerate(cavea.mast_positions()):
        x, y = cavea.xy(92.5, t)
        yaw = cavea.normal_yaw(92.5, t)
        for part, (number, z) in enumerate(((85, 46.8), (86, 47.45), (86, 52.45), (87, 57.3))):
            result.append({"id": f"mat-velum-{index:02d}-{part}", "mesh": aof(number), "position": [x, y, z],
                           "yaw": yaw, "role": "ornament"})
    # Torches murales sous le podium et les gradins, sur les parois des quatre passages, la
    # flamme vers le passage (la piece regarde son +Y local).
    for sign in (-1, 1):
        for along in (52, 64, 76):
            for side in (-1, 1):
                result.append({"id": f"torche-grand-axe-{sign}-{along}-{side}", "mesh": aof(157),
                               "position": [sign * along, side * 7.0, 1.2], "yaw": 180 if side > 0 else 0,
                               "role": "accessoires", "light": TORCH, "flame": 0.07})
        for along in (40, 54):
            for side in (-1, 1):
                result.append({"id": f"torche-petit-axe-{sign}-{along}-{side}", "mesh": aof(157),
                               "position": [side * 5.0, sign * along, 1.2], "yaw": 270 if side > 0 else 90,
                               "role": "accessoires", "light": TORCH, "flame": 0.07})
    # Une torche au palier de chaque escalier en U, une a mi-hauteur de chaque volee de 12 a 24 m.
    for core in cavea.core_points():
        for index, (position, yaw) in enumerate(core["torches"]):
            result.append({"id": f"torche-cage-{core['sector']:02d}-{index}", "mesh": aof(157), "position": position,
                           "yaw": yaw, "role": "accessoires", "light": TORCH, "flame": 0.07})
    # Les abords : bornes autour du parvis, luminaires et bancs aux quatre portes monumentales.
    for index in range(48):
        t = math.tau * (index + 0.5) / 48
        x, y = cavea.xy(99.0, t)
        result.append({"id": f"borne-parvis-{index:02d}", "mesh": aof(152), "position": [x, y, 0],
                       "yaw": cavea.normal_yaw(99.0, t), "role": "accessoires"})
    for door in range(4):
        t = math.pi * door / 2
        for side in (-1, 1):
            u = t + side * 0.075
            x, y = cavea.xy(97.0, u)
            yaw = cavea.normal_yaw(97.0, u)
            result.append({"id": f"luminaire-porte-{door}-{side}", "mesh": aof(156), "position": [x, y, 0],
                           "yaw": yaw, "role": "accessoires"})
            result.append({"id": f"brasero-porte-{door}-{side}", "mesh": aof(158), "position": [x, y, 1.08],
                           "yaw": yaw, "role": "accessoires", "light": FIRE, "flame": 0.14})
            u = t + side * 0.13
            x, y = cavea.xy(97.5, u)
            result.append({"id": f"banc-porte-{door}-{side}", "mesh": aof(155), "position": [x, y, 0],
                           "yaw": cavea.normal_yaw(97.5, u), "role": "accessoires"})
    return result


def glb_extent(mesh: str) -> tuple[list[float], list[float]]:
    """Les bornes d'un .glb (son +Y est le haut), lues sur ses accesseurs."""
    raw = (ASSETS / mesh).read_bytes()
    length = int.from_bytes(raw[12:16], "little")
    gltf = json.loads(raw[20 : 20 + length])
    positions = [gltf["accessors"][primitive["attributes"]["POSITION"]]
                 for item in gltf["meshes"] for primitive in item["primitives"]]
    low = [min(accessor["min"][k] for accessor in positions) for k in range(3)]
    high = [max(accessor["max"][k] for accessor in positions) for k in range(3)]
    return low, high


# La bannière d'une délégation pend à la traverse de son porte-bannière (SM_AOF_080 : poteau de
# 3,2 m, traverse de 1,7 m à 3 m) : sa tringle en prend la largeur.
STANDARD_ROD = 1.75
STANDARD_TOP = 3.05
# Le premier rang de la media cavea, de part et d'autre de l'encoche (LOGE_RECT, ±5 m) : le
# porte-bannière s'y pose au milieu du giron, à 6,3 m de l'axe de la loge.
STANDARD_ROW = 66.75
STANDARD_SIDE = 6.3


def loge_standards(metadata: dict) -> list[dict]:
    """Les bannières des délégations à côté de leur loge (demande de l'auteur du 19 octobre 2026) :
    un porte-bannière du catalogue de chaque côté de l'encoche, sur le premier rang de la media
    cavea, la bannière de la délégation tournée vers le sable."""
    row = next(r for r in cavea.rows() if abs(r["a"] - 66.0) < 1e-6)
    result = []
    for loge in metadata["loges"]:
        delegation = loge["delegation"]
        mesh = LEGACY_SCENE + f"banner-{delegation}.glb"
        low, high = glb_extent(mesh)
        height = (high[1] - low[1]) * STANDARD_ROD / (high[0] - low[0])
        angle = math.radians(loge["yaw"])
        c, s = math.cos(angle), math.sin(angle)
        for side in (-1, 1):
            # Le point du rang à la distance voulue de l'axe de la loge, dans son repère : x local
            # croît d'un bout à l'autre de ±0,25 rad, quel que soit son sens.
            def error(t, c=c, s=s, loge=loge, side=side):
                x, y = cavea.xy(STANDARD_ROW, t)
                return c * (x - loge["position"][0]) - s * (y - loge["position"][1]) - side * STANDARD_SIDE

            lo, hi = loge["angle"] - 0.25, loge["angle"] + 0.25
            if error(lo) * error(hi) > 0:
                raise RuntimeError(f"Porte-bannière hors du rang : {delegation} {side:+d}")
            for _ in range(60):
                mid = (lo + hi) / 2
                if error(mid) * error(lo) <= 0:
                    hi = mid
                else:
                    lo = mid
            t = (lo + hi) / 2
            x, y = cavea.xy(STANDARD_ROW, t)
            facing = cavea.normal_yaw(STANDARD_ROW, t)
            base = [x, y, row["top"]]
            result.append({"id": f"porte-banniere-{delegation}-{side:+d}", "mesh": aof(80), "position": base,
                           "yaw": facing + 180, "storey": "tribunes", "role": "bannieres"})
            # Un doigt devant le poteau, côté sable (la face -Y locale de `facing` le regarde).
            hung = local_position(base, facing, (0, -0.1, STANDARD_TOP - height))
            result.append({"id": f"banniere-{delegation}-{side:+d}", "mesh": mesh, "position": hung,
                           "yaw": facing + 180, "height": round(height, 3), "storey": "tribunes",
                           "role": "bannieres"})
    return result


def undercroft_dressing() -> list[dict]:
    """Les meubles qui complètent l'aménagement des vestiaires et de la prison
    (`arena_undercroft.py`, demande de l'auteur du 20 octobre 2026), hors du passage de la porte
    au centre de chaque salle : linges pliés dans les niches, amphores et coffres aux angles,
    mannequins et bâtons dans la fosse, bancs sous les manteaux, tabourets et linges aux tables
    de massage, tonneaux près de l'armurerie, un brasero (sa flamme et sa lumière par
    `arena_fate_atmosphere`, comme toute pièce des accessoires) ; à la prison, le poste du garde, un
    râtelier, un abreuvoir, un brasero près du pilori, des réserves, l'enclos garni."""
    result = []

    def add(ident, position, yaw=0.0, mesh=None, mesh_id=None, **extra):
        item = {"id": ident, "position": [position[0], position[1], -6 + position[2]], "yaw": yaw,
                "role": "accessoires", **extra}
        if mesh is not None:
            item["mesh"] = mesh
        else:
            item["meshId"] = mesh_id
        result.append(item)

    cx, west, east = undercroft.VESTIAIRE_X, undercroft.VESTIAIRE_X - 11.45, undercroft.VESTIAIRE_X + 11.45
    for name, sign in (("vestiaire-a", -1), ("vestiaire-b", 1)):
        def Y(d, sign=sign):
            return sign * (5.0 + d)

        x0, width, niches = cx - 3.9, 7.8, 11
        for k in range(niches):
            for row, z in enumerate((0.51, 1.26)):
                door = (k * 3 + row * 5) % 4 == 0 or (k + row) % 3 == 0
                if not door and (k + row) % 2 == 0:
                    add(f"{name}-linge-{k}-{row}", (x0 + width * (k + 0.5) / niches, Y(17.12), z),
                        mesh_id="afp-folded-linen")
        add(f"{name}-amphores-ouest", (west + 0.75, Y(16.7), 0), mesh_id="afp-service-amphora-pair")
        add(f"{name}-amphores-est", (east - 0.75, Y(16.7), 0), mesh_id="afp-service-amphora-pair")
        add(f"{name}-coffre-ouest", (cx - 5.6, Y(16.9), 0), 180 if sign < 0 else 0, mesh_id="afp-chest")
        add(f"{name}-coffre-est", (cx + 5.6, Y(16.9), 0), 180 if sign < 0 else 0, mesh_id="afp-chest")
        for side in (-1, 1):
            add(f"{name}-mannequin-{side:+d}", (cx + side * 3.5, Y(12.9), 0.06), mesh_id="afp-practice-stand")
            add(f"{name}-batons-{side:+d}", (cx + side * 5.0, Y(15.0), 0.06), mesh_id="afp-training-staves")
            add(f"{name}-banc-{side:+d}", (cx + side * 6.0, Y(1.15), 0), mesh=aof(109))
        for d in (5.0, 13.0):
            add(f"{name}-tabouret-{d:g}", (east - 2.7, Y(d), 0), mesh=aof(168))
            add(f"{name}-linge-table-{d:g}", (east - 1.85, Y(d - 0.3), 0.84), 90, mesh_id="afp-folded-linen")
        add(f"{name}-tonneau", (west + 0.6, Y(15.4), 0), mesh=aof(163))
        add(f"{name}-boucliers", (west + 0.85, Y(2.3), 0), 90, mesh_id="afp-shield-pair")
        add(f"{name}-brasero", (cx - 7.0, Y(11.0), 0), mesh_id="afp-brazier")

    # La prison (centre (24, 14), porte au milieu du mur du couloir, y = 5,55).
    add("prison-table-garde", (19.4, 7.4, 0), mesh=aof(113))
    add("prison-tabouret-garde", (19.4, 8.25, 0), mesh=aof(168))
    add("prison-caisse-garde", (21.1, 6.3, 0), mesh=aof(164))
    add("prison-ratelier", (35.1, 8.5, 0), 90, mesh=aof(112))
    add("prison-abreuvoir", (35.0, 18.0, 0), 90, mesh=aof(119))
    add("prison-brasero-pilori", (31.6, 10.6, 0), mesh_id="afp-brazier")
    add("prison-tonneau", (34.9, 6.3, 0), mesh=aof(163))
    add("prison-tonneau-nord", (34.9, 20.2, 0), mesh_id="afp-barrel")
    add("prison-coffre", (34.6, 21.9, 0), 180, mesh_id="afp-chest")
    add("prison-corde", (33.6, 15.2, 0), mesh_id="afp-rope-coil")
    add("prison-sac-cellule", (13.9, 10.6, 0), mesh=aof(165))
    add("prison-enclos-paillasse-0", (20.3, 21.4, 0), mesh_id="afp-pallet")
    add("prison-enclos-paillasse-1", (27.6, 21.4, 0), mesh_id="afp-pallet")
    add("prison-enclos-chaines", (24.0, 21.0, 0), mesh_id="afp-chain-set")
    return result


def parvis_stall() -> list[dict]:
    """L'étal de la mère, devant la porte sud (sa place est dans `capitale_demo.py`, MOTHER)."""
    return [
        {"id": "etal-mere-caisse-0", "mesh": aof(164), "position": [7.3, 85.8, 0], "yaw": 0, "role": "accessoires"},
        {"id": "etal-mere-caisse-1", "mesh": aof(164), "position": [7.3, 86.7, 0], "yaw": 0, "role": "accessoires"},
        {"id": "etal-mere-panier", "mesh": aof(166), "position": [7.3, 85.8, 0.75], "yaw": 0, "role": "accessoires"},
        {"id": "etal-mere-jarre", "mesh": aof(162), "position": [8.5, 86.2, 0], "yaw": 0, "role": "accessoires"},
    ]


def make_document(manifest: dict, props: dict, original: dict) -> tuple[dict, dict]:
    metadata = manifest["metadata"]
    patch = remap_gameplay(original, metadata)
    checks = validate_remap(original, patch)
    if not checks["allChecksPassed"]:
        raise RuntimeError(f"Gameplay preservation failed: {checks}")
    storeys = patch["storeys"]
    shots = list(metadata["shots"])
    names = {shot.get("id", shot.get("name")) for shot in shots}
    for shot in (
        {
            "name": "galerie-haute",
            "target": [88.5 / math.sqrt(2), 72.5 / math.sqrt(2), 25.5],
            "yaw": 225,
            "pitch": 35,
            "distance": 18,
        },
        {
            "name": "terrasse",
            "target": [24, 69, 47.3],
            "yaw": 100,
            "pitch": 42,
            "distance": 21,
        },
        {
            "name": "parvis",
            "target": [0, 73, 1.7],
            "yaw": 0,
            "pitch": 38,
            "distance": 24,
        },
    ):
        if shot["name"] not in names:
            shots.append(shot)
    if "fumetsu" not in {shot["name"] for shot in shots}:
        anchor = metadata["statues"][GODS.index("fumetsu")]
        shots.append(
            {
                "name": "fumetsu",
                "target": [*anchor["position"][:2], 2.1],
                "yaw": -anchor["yaw"],
                "pitch": 25,
                "distance": 9,
            }
        )
    registry = {
        mesh["id"]: "Built/arena-fate-modern/" + mesh["file"]
        for mesh in manifest["meshes"]
    }
    registry.update(
        {
            mesh["id"]: "Built/arena-fate-props/" + mesh["file"]
            for mesh in props["meshes"]
        }
    )
    raw = (
        list(manifest["objects"])
        + furnishings(metadata)
        + heritage(metadata)
        + required_completion(metadata)
        + aof_dressing()
        + loge_standards(metadata)
        + undercroft_dressing()
        + parvis_stall()
    )
    objects, occluders = [], []
    for item in raw:
        mesh = item.get("mesh") or registry[item["meshId"]]
        if not (ASSETS / mesh).is_file():
            raise RuntimeError(f"Missing scenery source: {mesh}")
        objects.append(relative_object(item, mesh, storeys))
        if item.get("occluder", False):
            occluders.append(item["id"])
    doc = {
        "format": jadg_map.FORMAT,
        "version": jadg_map.VERSION,
        "name": original["name"],
        "place": original.get("place", ""),
        "comment": "Arena complete, temoin imperial sculpte et peint valide le 10 octobre; gameplay et trajets physiques preserves.",
        "nextEntityId": original.get("nextEntityId", 34),
        **patch,
        "objects": objects,
        "party": deepcopy(
            original.get("party", {"appearances": ["heros-brawler"], "walkSpeed": 3.0})
        ),
        "lighting": {
            "lampCandelas": 9.0,
            "fireCandelas": 9.0,
            "sunScale": 1.65,
            "interiorProfiles": deepcopy(
                original.get("lighting", {}).get("interiorProfiles", INTERIOR_PROFILES)
            ),
            "fixtureOverrides": deepcopy(
                original.get("lighting", {}).get("fixtureOverrides", {})
            ),
            "ambientScale": 0.30,
            "skyLuminance": 1.8,
            "exposureBias": 0.0,
            "post": {
                "bloom_intensity": 0.25,
                "vignette_intensity": 0.12,
                "motion_blur_amount": 0.0,
                "film_grain_intensity": 0.0,
            },
        },
        "daylight": jadg_map.DAYLIGHT,
        "ground": {"colour": "#454849", "size": 2000.0, "height": -12.5},
        "navigation": {"area": [-102, -84, 102, 84], "floor": -13.0, "height": 51.0},
        "shots": [
            {
                "id": shot.get("id", shot.get("name")),
                "target": shot["target"],
                "heading": shot.get("heading", shot.get("yaw", 0)) % 360,
                "pitch": shot["pitch"],
                "distance": shot["distance"],
                **({"storey": shot["storey"]} if shot.get("storey", -1) >= 0 else {}),
            }
            for shot in shots
        ],
        "hours": ["12:00", "22:00"],
    }
    errors = jadg_map.validate(doc)
    if errors:
        raise RuntimeError("; ".join(errors))
    return doc, {
        "gameplay": checks,
        "occluderIds": occluders,
        "renderRevision": RENDER_REVISION,
        "approvalRecord": str(APPROVAL),
        "propCount": sum(
            obj["mesh"].startswith("Built/arena-fate-props/") for obj in objects
        ),
    }


def prepare() -> tuple[dict, dict, dict]:
    manifest, props = read_manifest(GEOMETRY), read_manifest(PROPS)
    doc, evidence = make_document(manifest, props, source_document())
    REPORTS.mkdir(parents=True, exist_ok=True)
    PROPOSAL.write_text(jadg_map.dumps(doc), encoding="utf-8")
    (REPORTS / "preparation.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
    write_gallery(doc)
    return doc, evidence, manifest


def write_gallery(doc: dict) -> Path:
    """A local review of real captures; absent images remain explicit placeholders."""
    captions = {
        "ensemble": "Vue d'ensemble",
        "sable": "Au niveau du sable",
        "gradins": "Gradins et accès",
        "loge": "Loge des délégations",
        "vestiaire": "Vestiaire",
        "prison": "Prison",
        "catacombes": "Catacombes",
        "escalier": "Escaliers des galeries",
        "facade": "Façade extérieure",
        "galerie-haute": "Galerie haute",
        "terrasse": "Terrasse et velum",
        "parvis": "Parvis",
    }
    cards = []
    for shot in doc["shots"]:
        title = captions.get(shot["id"], shot["id"])
        for time, label in (("1200", "Midi"), ("2200", "22 h")):
            filename = html.escape(f"{shot['id']}-{time}.png", quote=True)
            caption = html.escape(f"{title} — {label}")
            cards.append(
                f'<figure class="missing"><a href="{filename}" target="_blank" aria-label="{caption}, image entière">'
                f'<img src="{filename}" alt="{caption}" onload="loaded(this)" onerror="missing(this)">'
                '<span class="placeholder">Capture manquante</span></a>'
                f'<figcaption><span>{caption}</span><button type="button" onclick="fullscreen(this)">Plein écran</button></figcaption></figure>'
            )
    text = (
        """<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Arena of Fate — revue du décor</title><style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#18181d;color:#efebdf}body{max-width:1500px;margin:30px auto;padding:0 22px}
h1{font-size:26px;font-weight:550;margin-bottom:8px}p{color:#b8b5bd;line-height:1.5}button{border:1px solid #625b65;background:#302c34;color:#eee6db;border-radius:5px;padding:7px 12px;cursor:pointer}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;margin-top:25px}figure{margin:0;background:#242129;border:1px solid #3f3943;border-radius:7px;overflow:hidden}
figure>a{display:block;aspect-ratio:16/9;background:#141318;text-decoration:none;position:relative}img{display:block;width:100%;height:100%;object-fit:contain}
.placeholder{display:none;position:absolute;inset:0;place-items:center;color:#b4aebb}.missing .placeholder{display:grid}.missing img{visibility:hidden}
figcaption{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 15px;font-size:14px}figure:fullscreen{background:#111;width:100vw;height:100vh;display:flex;flex-direction:column;justify-content:center}figure:fullscreen>a{aspect-ratio:auto;flex:1;min-height:0}figure:fullscreen img{object-fit:contain}
@media(max-width:800px){.grid{grid-template-columns:1fr}body{padding:0 14px}} </style>
<h1>Arena of Fate — revue du décor</h1><p>Le décor complet reprend le style fantasy peint validé : sept niveaux reliés par des escaliers, loges meublées et salles souterraines. Ces vues de jour et de nuit sont présentées pour la revue artistique de l'arène complète. La foule viendra dans une étape suivante.</p>
<button type="button" onclick="refreshImages()">Actualiser les captures</button><section class="grid">"""
        + "\n".join(cards)
        + """</section>
<script>
function loaded(img){img.closest('figure').classList.remove('missing')}
function missing(img){img.closest('figure').classList.add('missing')}
function refreshImages(){for(const img of document.querySelectorAll('img')){img.src=img.getAttribute('src').split('?')[0]+'?t='+Date.now()}}
function fullscreen(button){const figure=button.closest('figure');if(!figure.classList.contains('missing')){if(figure.requestFullscreen)figure.requestFullscreen();else window.open(figure.querySelector('a').href,'_blank')}}
</script></html>"""
    )
    path = ROOT / "Saved/Captures/arena-fate-modern/index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def archive_original() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    if not ORIGINAL.is_file():
        shutil.copy2(SOURCE, ORIGINAL)
    content_dir = ROOT / "Content/Maps/Levels" / Path(MAP_ID).parent
    archive = REPORTS / "maps-before-modern"
    archive.mkdir(exist_ok=True)
    for path in content_dir.glob("arena-of-fate*.umap"):
        destination = archive / path.name
        if not destination.exists():
            shutil.copy2(path, destination)
    propagation_archive = REPORTS / "before-wicked-20261010"
    propagation_archive.mkdir(exist_ok=True)
    source_snapshot = propagation_archive / "arena-of-fate.json"
    if not source_snapshot.exists():
        shutil.copy2(SOURCE, source_snapshot)
    for path in content_dir.glob("arena-of-fate*.umap"):
        destination = propagation_archive / path.name
        if not destination.exists():
            shutil.copy2(path, destination)


def set_materials(actor, materials: dict, item: dict, metadata: dict) -> None:
    """Apply approved finishes by use; retain every original named GLB slot.

    Optional materialOverrides address an object ID or a mesh stem. Keeping
    these in the geometry manifest avoids adding renderer fields to gameplay.
    """
    comp = actor.static_mesh_component
    stem = Path(item["mesh"]).stem
    role = item["folder"]
    if stem.startswith("af-effigy-chains-"):
        for index in range(max(1, comp.get_num_materials())):
            comp.set_material(index, materials["dark_metal"])
        return
    overrides = metadata.get("materialOverrides", {})
    overrides = {**overrides.get(stem, {}), **overrides.get(item["id"], {})}
    for index, slot in enumerate(
        comp.static_mesh.get_editor_property("static_materials")
    ):
        names = [
            str(slot.get_editor_property(key))
            for key in ("imported_material_slot_name", "material_slot_name")
        ]
        name = next((name for name in names if name in materials), None)
        if name is None:
            raise RuntimeError(
                f"Unknown painted material slot {actor.get_actor_label()}: {names}"
            )
        replacement = name
        if "amphora" in stem and name in ("stone_cream", "marble_white", "burgundy"):
            replacement = "pottery"
        elif stem == "afp-wash-fountain" and name == "mortar":
            replacement = "wash_water"
        elif ("linen" in stem or "training-staves" in stem) and name in (
            "burgundy",
            "mortar",
        ):
            replacement = "linen"
        elif "loge" in stem and role == "roof" and name == "dark_metal":
            replacement = "roof_terracotta"
        elif "room-floor" in stem and name in ("stone_cream", "marble_white"):
            replacement = "chamber_floor"
        elif (
            metadata["levels"][item["storey"]]["z"] < 0 or "room" in stem
        ) and name == "stone_cream":
            replacement = "chamber_floor" if role == "floor" else "chamber_stone"
        replacement = overrides.get(name, replacement)
        if replacement not in materials:
            raise RuntimeError(
                f"Unknown approved finish {replacement!r} on {item['id']}/{name}"
            )
        comp.set_material(index, materials[replacement])


def sculpted_ambient_cube():
    """Regenerate the approved analytic sky gradient in this map's namespace."""
    import unreal

    if unreal.EditorAssetLibrary.does_asset_exist(AMBIENT_CUBE):
        cube = unreal.EditorAssetLibrary.load_asset(AMBIENT_CUBE)
        if not isinstance(cube, unreal.TextureCube):
            raise RuntimeError(f"Expected a TextureCube at {AMBIENT_CUBE}")
        return cube
    width, height = 256, 128
    pixels = bytearray()
    for y in range(height):
        elevation = math.cos(math.pi * (y + 0.5) / height)
        luminance = (
            0.42 + 0.90 * elevation**0.65
            if elevation >= 0.0
            else 0.08 + 0.34 * (1.0 + elevation) ** 3
        )
        mantissa, exponent = math.frexp(luminance)
        channel = min(255, int(mantissa * 256))
        pixels.extend(bytes((channel, channel, channel, exponent + 128)) * width)
    source = ROOT / "Intermediate/Jadg/arena-fate-modern/T_AmbientGradient_v1.hdr"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(
        f"#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y {height} +X {width}\n".encode()
        + pixels
    )
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path, task.destination_name = AMBIENT_CUBE.rsplit("/", 1)
    task.automated = True
    task.replace_existing = True
    task.save = True
    task.set_editor_property("async_", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.EditorAssetLibrary.load_asset(AMBIENT_CUBE)
    if not isinstance(texture, unreal.TextureCube):
        raise RuntimeError(
            "The approved Arena gradient did not import as a TextureCube"
        )
    return texture


@contextmanager
def isolated_render_environment(scene, atmosphere):
    """Temporary helper redirects; never rewrite common map materials or audio."""
    changes = {
        "GROUND_MATERIAL": "/Game/ArenaFateModern/Materials/M_Ground",
        "CONTOUR_MATERIAL": "/Game/ArenaFateModern/Materials/M_Contour",
        "OUTLINE_MATERIAL": "/Game/ArenaFateModern/Materials/M_Outline",
        "ambient_cube": sculpted_ambient_cube,
    }
    previous = {name: getattr(scene, name) for name in changes}
    previous_content = atmosphere.CONTENT
    try:
        for name, value in changes.items():
            setattr(scene, name, value)
        atmosphere.CONTENT = "/Game/ArenaFateModern/Atmosphere"
        yield
    finally:
        for name, value in previous.items():
            setattr(scene, name, value)
        atmosphere.CONTENT = previous_content


def chain_geometry_source(source: Path) -> Path:
    """Strip only obsolete material/image references; preserve all geometry bytes.

    The original authored GLB remains unchanged. Interchange receives a private
    intermediate with no old textures/materials, and the actor uses approved iron.
    """
    raw = source.read_bytes()
    json_length = int.from_bytes(raw[12:16], "little")
    document = json.loads(raw[20 : 20 + json_length])
    for mesh in document["meshes"]:
        for primitive in mesh["primitives"]:
            primitive.pop("material", None)
    for key in ("materials", "textures", "images", "samplers"):
        document.pop(key, None)
    payload = json.dumps(document, separators=(",", ":")).encode("utf-8")
    payload += b" " * (-len(payload) % 4)
    remainder = raw[20 + json_length :]
    output = (
        struct.pack("<4sII", b"glTF", 2, 20 + len(payload) + len(remainder))
        + struct.pack("<I4s", len(payload), b"JSON")
        + payload
        + remainder
    )
    destination = ROOT / "Intermediate/Jadg/arena-chain-geometry" / source.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.is_file() or destination.read_bytes() != output:
        destination.write_bytes(output)
    return destination


def arena_library(scene):
    """Map-owned kit imports; immutable statue masters are loaded without writes."""
    import unreal

    class ArenaLibrary(scene.Library):
        def static_mesh(self, mesh):
            if mesh in self.static:
                return self.static[mesh]
            if mesh.startswith(LEGACY_SCENE + "af-effigy-chains-"):
                source = self.assets / mesh
                digest = scene.scenery.sha256_of(source) + ":geometry-only-v1"
                asset_path = self.asset_path(mesh)
                if self.imports.get(
                    asset_path
                ) != digest or not unreal.EditorAssetLibrary.does_asset_exist(
                    asset_path
                ):
                    piece_folder = asset_path.rsplit("/", 2)[0]
                    result = scene.scenery.import_glb(
                        chain_geometry_source(source),
                        piece_folder.rsplit("/", 1)[0],
                        piece_folder,
                        asset_path,
                    )
                    self.imported += 1
                    self.imports[asset_path] = digest
                    self.imports_file.parent.mkdir(parents=True, exist_ok=True)
                    self.imports_file.write_text(
                        json.dumps(self.imports, indent=1), encoding="utf-8"
                    )
                else:
                    result = unreal.EditorAssetLibrary.load_asset(asset_path)
                scene.scenery.finish(result)
                if not unreal.EditorAssetLibrary.save_loaded_asset(result):
                    raise RuntimeError(
                        f"Could not save original chain geometry: {mesh}"
                    )
                self.static[mesh] = result
                return result
            piece = self.master.get(mesh)
            if piece is None:
                return super().static_mesh(mesh)
            source = self.assets / mesh
            if scene.scenery.sha256_of(source) != piece["sha256"]:
                raise RuntimeError(f"Statue master differs from its manifest: {source}")
            result = unreal.EditorAssetLibrary.load_asset(piece["asset"])
            if not isinstance(result, unreal.StaticMesh):
                raise RuntimeError(
                    f"Import the immutable master first: {piece['asset']}"
                )
            self.static[mesh] = result
            return result

    library = ArenaLibrary()
    library.content_root = "/Game/ArenaFateModern/Kit"
    library.imports_file = ROOT / "Intermediate/Jadg/arena-fate-modern-imports.json"
    library.imports = (
        json.loads(library.imports_file.read_text(encoding="utf-8"))
        if library.imports_file.exists()
        else {}
    )
    return library


def preserve_walkable_collision(library, doc: dict) -> list[dict]:
    """Keep authored floors/stairs in the Nanite fallback used by character physics.

    Automatic relative simplification bowed the large ground ring by 14.5 cm.
    The three richly sculpted rings use closed architectural collision meshes
    with their exact 192-chord contours, slots and floor heights. Their visual
    Nanite/fallback geometry remains intact; other floors and stairs retain the
    original full-source policy. No additional actors are placed.
    """
    import unreal

    sources = sorted(
        {
            item["mesh"]
            for item in doc["objects"]
            if (
                item["mesh"].startswith("Built/arena-fate-modern/")
                and item["folder"] in ("floor", "stairs", "seating")
            )
            or item["mesh"].startswith(LEGACY_SCENE + "af-effigy-chains-")
        }
    )
    result = []
    ring_names = {"afm-ring-ground", "afm-ring-upper", "afm-ring-gallery"}
    proxies = {}
    for source in sources:
        if Path(source).stem not in ring_names:
            continue
        proxy_source = (
            Path(source).with_name(Path(source).stem + "-collision.glb").as_posix()
        )
        proxy = library.static_mesh(proxy_source)
        proxy_settings = proxy.get_editor_property("nanite_settings").copy()
        proxy_changed = False
        if proxy_settings.enabled:
            # Collision reads the authored LOD0 directly, without a Nanite
            # fallback that could bow the exact floor or round its openings.
            proxy_settings.enabled = False
            proxy.set_editor_property("nanite_settings", proxy_settings)
            proxy_changed = True
        if not proxy.get_editor_property("allow_cpu_access"):
            proxy.set_editor_property("allow_cpu_access", True)
            proxy_changed = True
        body = proxy.get_editor_property("body_setup")
        if body is None:
            raise RuntimeError(
                f"Architectural collision proxy has no BodySetup: {proxy_source}"
            )
        if (
            body.get_editor_property("collision_trace_flag")
            != unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
        ):
            body.set_editor_property(
                "collision_trace_flag",
                unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE,
            )
            proxy_changed = True
        if proxy_changed and not unreal.EditorAssetLibrary.save_loaded_asset(proxy):
            raise RuntimeError(
                f"Could not save architectural collision proxy: {proxy_source}"
            )
        if proxy.get_editor_property("nanite_settings").enabled:
            raise RuntimeError(
                f"Collision proxy must retain authored non-Nanite LOD0: {proxy_source}"
            )
        proxies[source] = (proxy_source, proxy)
    for source in sources:
        mesh = library.static_mesh(source)
        changed = False
        settings = mesh.get_editor_property("nanite_settings").copy()
        if (
            settings.fallback_target != unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
            or settings.fallback_percent_triangles != 1.0
            or settings.fallback_relative_error != 0.0
        ):
            settings.fallback_target = unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
            settings.fallback_percent_triangles = 1.0
            settings.fallback_relative_error = 0.0
            mesh.set_editor_property("nanite_settings", settings)
            changed = True
        proxy_evidence = {}
        if source in proxies:
            proxy_source, proxy = proxies[source]
            body = mesh.get_editor_property("body_setup")
            if (
                body is None
                or body.get_editor_property("collision_trace_flag")
                != unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
            ):
                raise RuntimeError(
                    f"Ring collision must use complex as simple: {source}"
                )
            # Always notify: the proxy GLB may have been reimported at the same
            # asset path. UE recooks BodySetup and rebuilds its NavCollision
            # cache; Recast exports those cooked triangles.
            mesh.set_editor_property("complex_collision_mesh", proxy)
            changed = True
            if mesh.get_editor_property("complex_collision_mesh") != proxy:
                raise RuntimeError(
                    f"Ring rejected architectural collision proxy: {source}"
                )
            proxy_evidence = {
                "collisionSource": proxy_source,
                "collisionAsset": proxy.get_path_name(),
                "collisionTriangles": proxy.get_num_triangles(0),
                "collisionNanite": False,
                "collisionTraceFlag": "CTF_USE_COMPLEX_AS_SIMPLE",
                "navigationGeometry": "architectural-proxy-body-setup",
            }
        if changed and not unreal.EditorAssetLibrary.save_loaded_asset(mesh):
            raise RuntimeError(f"Could not save faithful collision for {source}")
        result.append(
            {
                "source": source,
                "fallbackTriangles": mesh.get_num_triangles(0),
                "naniteTriangles": mesh.get_num_nanite_triangles(),
                **proxy_evidence,
            }
        )
    return result


def wall_fixture_supports(doc):
    """Couple a wall bracket and its fire to the actual wall and backing."""
    objects = doc["objects"]
    by_id = {item["id"]: item for item in objects}
    result = {}
    for item in objects:
        if Path(item["mesh"]).stem != "afp-wall-lamp":
            continue
        floor = doc["storeys"][item["storey"]]["z"]
        if floor >= 0:
            continue
        rooms = [
            wall
            for wall in objects
            if wall["storey"] == item["storey"]
            and Path(wall["mesh"]).stem in ("afm-room-walls", "afm-room-walls-service")
            and abs(wall["position"][0] - item["position"][0]) < 12
            and abs(wall["position"][1] - item["position"][1]) < 9
        ]
        if rooms:
            wall = min(
                rooms,
                key=lambda candidate: sum(
                    (candidate["position"][axis] - item["position"][axis]) ** 2
                    for axis in (0, 1)
                ),
            )
            parents = [wall["id"]]
            backing = "fond-" + wall["id"]
        else:
            prefix = "cat" if floor <= -11 else "under"
            walls = [
                wall
                for wall in objects
                if wall["storey"] == item["storey"]
                and Path(wall["mesh"]).stem == f"afm-{prefix}-walls"
            ]
            if len(walls) != 1:
                raise RuntimeError(f"No unique physical wall for fixture {item['id']}")
            parents = [walls[0]["id"]]
            backing = f"fond-murs-{prefix}"
        if backing in by_id:
            parents.append(backing)
        result[item["id"]] = parents
    return result


def effective_cutaway_supports(doc: dict, metadata: dict) -> dict:
    """Roof ribs follow their roof shell, including its continuous backing.

    This also upgrades the previous manifest without needing to regenerate an
    unchanged mesh. Corridors currently have one combined rib mesh per floor.
    """
    explicit = deepcopy(metadata.get("supportOverrides", {}))
    by_id = {item["id"]: item for item in doc["objects"]}
    for item in doc["objects"]:
        stem = Path(item["mesh"]).stem
        if stem not in ("afm-room-ribs", "afm-under-ribs", "afm-cat-ribs"):
            continue
        candidates = []
        for roof in doc["objects"]:
            roof_stem = Path(roof["mesh"]).stem
            if roof["storey"] != item["storey"]:
                continue
            if stem == "afm-room-ribs":
                matched = (
                    roof_stem == "afm-room-vault"
                    and math.dist(roof["position"], item["position"]) < 0.01
                )
            else:
                prefix = "under" if stem == "afm-under-ribs" else "cat"
                matched = roof_stem in ("afm-axial-vault", f"afm-{prefix}-branch-roofs")
            if matched:
                candidates.append(roof["id"])
                if "fond-" + roof["id"] in by_id:
                    candidates.append("fond-" + roof["id"])
        if not candidates:
            raise RuntimeError(f"Roof ribs have no corresponding vault: {item['id']}")
        if stem in ("afm-under-ribs", "afm-cat-ribs"):
            prefix = "under" if stem == "afm-under-ribs" else "cat"
            if f"fond-voutes-{prefix}" in by_id:
                candidates.append(f"fond-voutes-{prefix}")
        explicit[item["id"]] = list(dict.fromkeys(candidates))
    explicit.update(wall_fixture_supports(doc))
    for item in doc["objects"]:
        stem = Path(item["mesh"]).stem
        if stem.startswith("afp-prison-cell-"):
            floor = next(
                obj
                for obj in doc["objects"]
                if Path(obj["mesh"]).stem.startswith("afm-room-floor")
                and obj["storey"] == item["storey"]
                and obj["position"][:2] == [24, 14]
            )
            explicit[item["id"]] = [floor["id"]]
            if stem == "afp-prison-cell-door-open":
                explicit[item["id"]].append(item["id"].replace("-door-", "-front-"))
        elif stem == "afp-wash-fountain":
            room = min(
                (
                    obj
                    for obj in doc["objects"]
                    if Path(obj["mesh"]).stem == "afm-room-walls"
                    and obj["storey"] == item["storey"]
                ),
                key=lambda obj: math.dist(obj["position"][:2], item["position"][:2]),
            )
            explicit[item["id"]] = [room["id"], "fond-" + room["id"]]
        elif stem.startswith("af-effigy-chains-"):
            effigy = by_id["effigie-" + stem.removeprefix("af-effigy-chains-")]
            floor = next(
                obj
                for obj in doc["objects"]
                if Path(obj["mesh"]).stem.startswith("afm-room-floor")
                and obj["storey"] == item["storey"]
                and math.dist(obj["position"][:2], effigy["position"][:2]) < 6.01
            )
            explicit[item["id"]] = [effigy["id"], floor["id"]]
        elif stem.startswith("afp-nameplate-") or stem == "afp-fumetsu-plinth-collar":
            bases = [
                obj
                for obj in doc["objects"]
                if Path(obj["mesh"]).stem == "afm-statue-plinth"
            ]
            base = min(
                bases,
                key=lambda obj: math.dist(obj["position"][:2], item["position"][:2]),
            )
            explicit[item["id"]] = [base["id"]]
    return explicit


def link_cutaway_supports(frame, doc: dict, placed: list[dict], metadata: dict) -> dict:
    """Couple visibility to the actual floor below each object before saving it.

    A component trace avoids mistaking the empty centre of an annular floor's
    bounding box for a supporting surface. No collision or light is removed.
    """
    import unreal

    floors = [
        item for item in placed if item["folder"] in ("floor", "stairs", "seating")
    ]
    by_id = {item["id"]: item for item in placed}
    known_ids = {item["id"] for item in doc["objects"]}
    explicit = effective_cutaway_supports(doc, metadata)
    required_surfaces = {
        value
        for values in explicit.values()
        for value in ([values] if isinstance(values, str) else values)
    }
    for item in placed:
        if item["id"] in required_surfaces:
            actor = item["actor"]
            actor.tags = list(actor.tags) + ["JadgWitnessSurface:" + item["id"]]
    for item in floors:
        actor = item["actor"]
        actor.tags = list(actor.tags) + ["JadgWitnessSurface:" + item["id"]]
    linked, unsupported = {}, []
    for item in placed:
        if item["folder"] == "floor":
            continue
        actor = item["actor"]
        requested = explicit.get(item["id"])
        if requested is not None:
            supports = [requested] if isinstance(requested, str) else requested
            if (
                not isinstance(supports, list)
                or not supports
                or any(
                    value not in known_ids or value == item["id"] for value in supports
                )
            ):
                raise RuntimeError(
                    f"Invalid cutaway support on {item['id']}: {requested!r}"
                )
            for support in supports:
                if support not in by_id:
                    continue  # Surface will be tagged in its own streamed storey.
                parent = by_id[support]["actor"]
                tag = "JadgWitnessSurface:" + support
                if tag not in [str(value) for value in parent.tags]:
                    parent.tags = list(parent.tags) + [tag]
            actor.tags = list(actor.tags) + [
                "JadgWitnessSupport:" + support for support in supports
            ]
            linked[item["id"]] = supports
            continue
        centre, extent = actor.get_actor_bounds(False)
        base = frame.map_point([0, 0, doc["storeys"][item["storey"]]["z"]]).z
        start = unreal.Vector(
            centre.x, centre.y, max(base + 25, centre.z - extent.z + 25)
        )
        end = unreal.Vector(centre.x, centre.y, base - 50)
        hits = []
        for floor in floors:
            if floor["id"] == item["id"]:
                continue
            ground = floor["actor"]
            middle, half = ground.get_actor_bounds(False)
            if abs(centre.x - middle.x) > half.x or abs(centre.y - middle.y) > half.y:
                continue
            hit = ground.static_mesh_component.line_trace_component(
                start, end, True, False, False
            )
            if hit is not None:
                # Permit a component which is itself supported, but never attach
                # a lower floor to a surface above the object's actual foot.
                if hit[0].z <= start.z + 1.0:
                    hits.append((hit[0].z, floor["id"]))
        if hits:
            support = max(hits)[1]
            actor.tags = list(actor.tags) + ["JadgWitnessSupport:" + support]
            linked[item["id"]] = support
        else:
            unsupported.append(item["id"])
    return {"linked": linked, "withoutFloorBelow": unsupported}


def place_lights(
    level, frame, metadata: dict, doc: dict, index: int, placed: list[dict]
) -> dict:
    """Only physical fixture anchors light the scene; old bare fill points are omitted."""
    import unreal

    by_id = {item["id"]: item for item in placed}
    lights = metadata.get("lightFixtures", [])
    props = {
        item["id"]: item
        for item in json.loads(PROPS.read_text(encoding="utf-8"))["meshes"]
    }
    result = []
    for number, light in enumerate(lights):
        if floor_index(light["position"][2], doc["storeys"]) != index:
            continue
        fixture = light.get("fixtureId")
        if fixture not in by_id:
            raise RuntimeError(
                f"Light {light.get('id', number)} has no physical fixture: {fixture!r}"
            )
        if props.get(Path(by_id[fixture]["mesh"]).stem, {}).get("light"):
            raise RuntimeError(
                f"Light {light.get('id', number)} duplicates atmosphere prop.light on {fixture}"
            )
        actor = level.spawn(
            unreal.PointLight,
            frame.map_point(light["position"]),
            unreal.Rotator(),
            "ArenaLamp_" + str(light.get("id", number)),
            "lumieres",
        )
        comp = actor.light_component
        comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        comp.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
        comp.set_editor_property("intensity", light.get("candelas", 9.0))
        comp.set_editor_property("attenuation_radius", light.get("radius", 5.0) * 100)
        comp.set_light_color(
            unreal.LinearColor(*light.get("colour", [1.0, 0.80, 0.62]), 1.0)
        )
        comp.set_editor_property("source_radius", light.get("sourceRadiusCm", 12.0))
        comp.set_editor_property("cast_shadows", light.get("castShadows", True))
        if not light.get("always", light["position"][2] < 0):
            actor.tags = ["JadgLamp"]
        result.append(
            {
                "id": light.get("id", str(number)),
                "fixtureId": fixture,
                "position": light["position"],
                "candelas": light.get("candelas", 9.0),
                "radiusMetres": light.get("radius", 5.0),
            }
        )
    return {
        "fixtures": result,
        "bareFillPointsOmitted": len(metadata.get("lights", [])),
    }


def _build_editor() -> None:
    import unreal

    import arena_wicked_materials
    import arena_fate_atmosphere
    import build_level as scene

    doc, evidence, manifest = prepare()
    metadata = manifest["metadata"]
    archive_original()
    materials = arena_wicked_materials.build_materials("painted")
    materials["wash_water"] = scene.flat_material(
        "/Game/ArenaFateModern/Materials/M_WashWater",
        unreal.LinearColor(0.035, 0.095, 0.115, 1.0),
        roughness=0.22,
    )
    library = arena_library(scene)
    walkable_collision = preserve_walkable_collision(library, doc)
    fixtures = scene.Library(scene.FIXTURE_ASSETS.relative_to(ROOT).as_posix())
    frame = scene.Frame(
        scene.FIXTURE_ASSETS / scene.FRAME_REFERENCE,
        fixtures.static_mesh(scene.FRAME_REFERENCE),
    )
    packages = []
    atmosphere = []
    cutaway_supports = []
    fixture_lights = []
    occluders = set(evidence["occluderIds"])
    for index, storey in enumerate(doc["storeys"]):
        world = unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
        if world is None:
            raise RuntimeError("Could not create arena storey")
        level = scene.Level(world)
        prop_objects = []
        placed_objects = []
        for item in doc["objects"]:
            if item["storey"] != index:
                continue
            actor = scene.place_object(level, frame, doc, library, item, item["folder"])
            if item["mesh"].startswith(
                (
                    "Built/arena-fate-modern/",
                    "Built/arena-fate-props/",
                    LEGACY_SCENE + "af-effigy-chains-",
                )
            ):
                set_materials(actor, materials, item, metadata)
            if (
                Path(item["mesh"]).stem.startswith("afp-nameplate-")
                or Path(item["mesh"]).stem == "afp-fumetsu-plinth-collar"
            ):
                actor.static_mesh_component.set_collision_enabled(
                    unreal.CollisionEnabled.NO_COLLISION
                )
            if item["id"] in occluders:
                actor.tags = list(actor.tags) + ["JadgWitnessOccluder"]
            placed_objects.append({**item, "actor": actor})
            if item["mesh"].startswith("Built/arena-fate-props/"):
                prop_objects.append({**item, "actor": actor})
        cutaway_supports.append(
            link_cutaway_supports(frame, doc, placed_objects, metadata)
        )
        atmosphere.append(
            arena_fate_atmosphere.install(
                level, frame, doc, library, metadata, prop_objects
            )
        )
        fixture_lights.append(
            place_lights(level, frame, metadata, doc, index, placed_objects)
        )
        package = scene.storey_package(PACKAGE, storey)
        if not unreal.EditorLoadingAndSavingUtils.save_map(world, package):
            raise RuntimeError(f"Could not save {package}")
        packages.append(package)
        scene.log(
            f"Arena storey {storey['name']}: {sum(item['storey'] == index for item in doc['objects'])} objects"
        )
    world = unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    if world is None:
        raise RuntimeError("Could not create persistent arena")
    level = scene.Level(world)
    scene.place_sky(level, doc, frame)
    atmosphere.append(
        arena_fate_atmosphere.install(
            level, frame, doc, library, {**metadata, "atmospherePersistent": True}, []
        )
    )
    for actor in unreal.get_editor_subsystem(
        unreal.EditorActorSubsystem
    ).get_all_level_actors():
        if actor.get_actor_label() == "SolLointain":
            actor.static_mesh_component.set_collision_enabled(
                unreal.CollisionEnabled.NO_COLLISION
            )
        if isinstance(actor, unreal.SkyLight):
            actor.light_component.set_editor_property(
                "cubemap", sculpted_ambient_cube()
            )
            actor.light_component.set_editor_property(
                "lower_hemisphere_is_black", False
            )
    scene.place_navigation(level, doc, frame)
    scene.place_characters(level, doc, frame, library)
    scene.place_entities(level, doc, frame)
    scene.place_frame(level, doc, frame, MAP_ID, SOURCE, packages)
    scene.place_shots(level, doc, frame)
    persistent_level = world.get_world_settings().get_level()
    persistent_name = world.get_path_name().split(".", 1)[0].rsplit("/", 1)[-1]
    for package in packages:
        if (
            unreal.EditorLevelUtils.add_level_to_world(
                world, package, unreal.LevelStreamingAlwaysLoaded
            )
            is None
        ):
            raise RuntimeError(f"Could not attach {package}")
    # Adding a sublevel makes it the editor's spawn target. Restore the persistent
    # level before creating the controller and Recast data, otherwise save_map on
    # the main world omits them and runtime silently loses navigation and cutaway.
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if (
        not level_editor.set_current_level_by_name(persistent_name)
        or level_editor.get_current_level() != persistent_level
    ):
        raise RuntimeError("Could not restore the persistent arena as actor owner")
    review = level.spawn(
        scene.game_class("JadgWitnessReview"),
        unreal.Vector(),
        unreal.Rotator(),
        "ArenaPhysicalReview",
        "controle",
    )
    if review.get_level() != persistent_level:
        raise RuntimeError(
            "Arena review controller must belong to the persistent level"
        )
    route = metadata["route"]
    if len(route) < 2:
        raise RuntimeError(
            "Full arena route requires floor points on all physical storeys"
        )
    review.set_editor_property(
        "route_points", [frame.map_point(point) for point in route]
    )
    review.set_editor_property("point_tolerance", 35.0)
    review.set_editor_property("height_tolerance", 10.0)
    review.set_editor_property("fine_navigation", True)
    review.set_editor_property("navigation_cell_size", 5.0)
    review.set_editor_property("navigation_cell_height", 2.0)
    review.set_editor_property("navigation_elevation_ratio", 1.0)
    review.set_editor_property("navigation_tile_size", 300.0)
    review.set_editor_property("navigation_average_layers", 12.0)
    review.set_editor_property("navigation_max_simplification_error", 1.3)
    review.set_editor_property("navigation_max_search_nodes", 32768)
    review.set_editor_property("startup_timeout", 600.0)
    world.get_world_settings().set_editor_property(
        "default_game_mode", scene.game_class("JadgGameMode")
    )
    start = frame.map_point([route[0][0], route[0][1], route[0][2] + 0.25])
    # Create/unlock this world's navigation, then apply the same local profile
    # in the editor and on runtime reload. Report values read back from Recast.
    unreal.JadgSceneBuild.unreachable_points(world, start, [])
    if not review.prepare_fine_navigation():
        raise RuntimeError("Arena local navigation profile could not be applied")
    navigation = json.loads(review.get_navigation_settings_json())
    targets = metadata.get("navigationTargets", [])
    points = [
        frame.map_point([point[0], point[1], point[2] + 0.25])
        for point in route[1:] + targets
    ]
    disconnected = list(unreal.JadgSceneBuild.unreachable_points(world, start, points))
    unreachable = [index for index in disconnected if index < len(route) - 1]
    unreachable_targets = [
        index - len(route) + 1 for index in disconnected if index >= len(route) - 1
    ]
    projections = []
    # The generic helper permits broad Z projection. A full-height arena must also
    # reject a path projected onto another floor; use the physical walk's 10 cm.
    for index, point in enumerate(route + targets):
        requested = frame.map_point(point)
        projected = unreal.NavigationSystemV1.project_point_to_navigation(
            world, requested, None, None, unreal.Vector(50, 50, 10)
        )
        projections.append(
            {
                "index": index,
                "source": point,
                "projected": frame.map_of_point(projected)
                if projected is not None
                else None,
            }
        )
    bad_heights = [
        probe["index"] for probe in projections if probe["projected"] is None
    ]
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, PACKAGE):
        raise RuntimeError(f"Could not save {PACKAGE}")
    report = {
        "package": PACKAGE,
        "source": str(SOURCE),
        "objects": len(doc["objects"]),
        "storeyPackages": packages,
        "route": route,
        "shots": doc["shots"],
        "unreachableRouteIndices": unreachable,
        "unreachableTargetIndices": unreachable_targets,
        "navigationSettings": navigation,
        "strictNavigationProjections": projections,
        "missingNavigationAtFloor": bad_heights,
        "geometryManifest": str(GEOMETRY),
        "propsManifest": str(PROPS),
        **evidence,
        "walkableCollision": walkable_collision,
        "cutawaySupports": cutaway_supports,
        "reviewActor": review.get_path_name(),
        "atmosphere": atmosphere,
        "fixtureLights": fixture_lights,
        "renderRevision": RENDER_REVISION,
        "approvedWitness": "arena-wicked-witness/painted",
        "sourceCommitted": False,
        "artisticApproval": "full-arena-pending",
    }
    (REPORTS / "build.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if disconnected or bad_heights:
        raise RuntimeError(
            f"Arena navigation invalid; canonical JSON preserved. Disconnected route: {unreachable}; targets: {unreachable_targets}; floor projection: {bad_heights}"
        )
    SOURCE.write_text(jadg_map.dumps(doc), encoding="utf-8")
    report["sourceCommitted"] = True
    (REPORTS / "build.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    scene.log(
        f"Arena complete: {len(doc['objects'])} objects, {len(route)} connected route points; {PACKAGE}"
    )


def build_editor() -> None:
    import arena_fate_atmosphere
    import build_level as scene

    with isolated_render_environment(scene, arena_fate_atmosphere):
        _build_editor()


def main() -> None:
    if "unreal" in sys.modules:
        build_editor()
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--prepare", action="store_true", required=True)
        parser.parse_args()
        prepare()
        print(PROPOSAL)


if __name__ == "__main__":
    main()
