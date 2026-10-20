#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Remap the Arena of Fate's authored gameplay onto a new physical scene grid.

This module has no filesystem or engine side effects. It returns only the gameplay
patch for a rebuilt map; geometry, collision and navigation belong to the scene.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

CELL_METERS = 1.5
REQUIRED_STOREY_Z = (0.0, -6.0, -12.0, 12.0, 24.0, 36.0, 46.8)
COMBAT_VOLUME = {"min": [-33.0, -18.0, -0.5], "max": [33.0, 18.0, 4.0]}
INTERNAL_PORTAL_IDS = frozenset({"e2", "e3", "e20", "e25", "e27", "e33"})
ENCOUNTER_IDS = frozenset({"e6", "e7", "e8", "e9", "e10", "e11"})
ARENA_ENTRY_IDS = frozenset({"e28", "e29", "e30", "e31"})
SPAWN_NAMES = {
    "e1": "from-undercroft",
    "e12": "from-undercroft-dead",
    "e19": "from-arena-of-fate",
    "e21": "from-arenarea",
    "e24": "from-catacombs",
    "e26": "from-dead-gate",
    "e32": "catacombs-from-undercroft",
}
NARRATIVE_ENTITY_IDS = frozenset(
    {"e4", "e5", "e23", *ENCOUNTER_IDS, *ARENA_ENTRY_IDS, *SPAWN_NAMES}
)


def _field(value: Any, key: str) -> Any:
    if isinstance(value, Mapping):
        if key not in value:
            raise ValueError(f"metadata missing required field {key!r}")
        return value[key]
    try:
        return getattr(value, key)
    except AttributeError as error:
        raise ValueError(f"metadata missing required field {key!r}") from error


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite number")
    return result


def _xyz(value: Any, label: str) -> tuple[float, float, float]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != 3:
        raise ValueError(f"{label} must contain [x, y, z]")
    return tuple(_number(component, f"{label}[{index}]") for index, component in enumerate(value))  # type: ignore[return-value]


def _grid_position(
    position: tuple[float, float, float], origin: tuple[float, float], width: int, height: int, label: str
) -> tuple[int, int]:
    x = math.floor((position[0] - origin[0]) / CELL_METERS)
    y = math.floor((position[1] - origin[1]) / CELL_METERS)
    if not (0 <= x < width and 0 <= y < height):
        raise ValueError(f"{label} maps outside the grid at ({x}, {y})")
    return x, y


def _levels(metadata: Any) -> tuple[list[dict[str, Any]], list[float]]:
    raw_levels = _field(metadata, "levels")
    if not isinstance(raw_levels, Sequence) or isinstance(raw_levels, (str, bytes)):
        raise ValueError("metadata.levels must be a sequence")
    levels: list[dict[str, Any]] = []
    zs: list[float] = []
    for index, level in enumerate(raw_levels):
        name = _field(level, "name")
        z = _number(_field(level, "z"), f"metadata.levels[{index}].z")
        if not isinstance(name, str) or not name:
            raise ValueError(f"metadata.levels[{index}].name must be a nonempty string")
        levels.append({"name": name, "z": z})
        zs.append(z)
    if not levels or abs(zs[0]) > 1e-6 or len(set(zs)) != len(zs):
        raise ValueError("metadata.levels must start at z=0 and use unique heights")
    for expected in REQUIRED_STOREY_Z:
        if not any(abs(z - expected) <= 1e-4 for z in zs):
            raise ValueError(f"metadata.levels is missing required storey z={expected:g} m")
    return levels, zs


def _storey_index(z: float, levels: Sequence[float], label: str) -> int:
    index = min(range(len(levels)), key=lambda candidate: abs(levels[candidate] - z))
    if abs(levels[index] - z) > 1.5:
        raise ValueError(f"{label} at z={z:g} m is not near a declared floor")
    return index


def _old_anchor(entity: Mapping[str, Any], source_doc: Mapping[str, Any]) -> tuple[float, float, float]:
    storeys = source_doc.get("storeys", ())
    old_storey = int(entity.get("storey", 0))
    if not (0 <= old_storey < len(storeys)):
        raise ValueError(f"{entity.get('id', '<entity>')} refers to a missing source storey")
    z = _number(storeys[old_storey]["z"], "source storey z")
    # Volumes use world coordinates, including the map origin. This also keeps
    # repeated regeneration of the already migrated map from translating them again.
    origin = source_doc.get("origin", (0.0, 0.0))
    return (_number(origin[0], "source origin x") + (int(entity["x"]) + 0.5) * CELL_METERS,
            _number(origin[1], "source origin y") + (int(entity["y"]) + 0.5) * CELL_METERS, z)


def _translated_volume(
    volume: Mapping[str, Any], old_anchor: tuple[float, float, float], new_anchor: tuple[float, float, float]
) -> dict[str, list[float]]:
    delta = tuple(new_anchor[index] - old_anchor[index] for index in range(3))
    return {
        bound: [
            _number(component, f"volume.{bound}[{index}]") + delta[index]
            for index, component in enumerate(volume[bound])
        ]
        for bound in ("min", "max")
    }


def _internal_portal(entity: Mapping[str, Any], source_doc: Mapping[str, Any]) -> bool:
    return entity.get("type") == "portal" and entity.get("targetMap") == source_doc.get("place")


def remap_gameplay(source_doc: Mapping[str, Any], metadata: Any) -> dict[str, Any]:
    """Return the gameplay portion of the modern Arena map.

    `metadata.entityPositions` gives absolute meter anchors by stable source entity
    id. `metadata.entry`, when present, is the preferred absolute [x, y, z] start;
    otherwise the start reuses e21's remapped location. Source decoration/collision
    tiles are intentionally omitted: the new physical scene owns both.
    """
    if not isinstance(source_doc, Mapping):
        raise ValueError("source_doc must be a mapping")
    source_entities = source_doc.get("entities")
    if not isinstance(source_entities, Sequence):
        raise ValueError("source_doc.entities must be a sequence")

    levels, level_zs = _levels(metadata)
    origin_raw = _field(metadata, "origin")
    if not isinstance(origin_raw, Sequence) or isinstance(origin_raw, (str, bytes)) or len(origin_raw) != 2:
        raise ValueError("metadata.origin must contain [x, y]")
    origin = (_number(origin_raw[0], "metadata.origin[0]"), _number(origin_raw[1], "metadata.origin[1]"))
    width_raw, height_raw = _field(metadata, "width"), _field(metadata, "height")
    if isinstance(width_raw, bool) or not isinstance(width_raw, int) or width_raw <= 0:
        raise ValueError("metadata.width must be a positive integer")
    if isinstance(height_raw, bool) or not isinstance(height_raw, int) or height_raw <= 0:
        raise ValueError("metadata.height must be a positive integer")
    width, height = width_raw, height_raw

    positions = _field(metadata, "entityPositions")
    if not isinstance(positions, Mapping):
        raise ValueError("metadata.entityPositions must be an id-to-position mapping")
    source_by_id = {entity.get("id"): entity for entity in source_entities}
    if len(source_by_id) != len(source_entities):
        raise ValueError("source_doc contains duplicate or missing entity IDs")
    missing_narrative = NARRATIVE_ENTITY_IDS - source_by_id.keys()
    if missing_narrative:
        raise ValueError(f"source map is missing gameplay IDs: {sorted(missing_narrative)}")

    result_entities: list[dict[str, Any]] = []
    for original in source_entities:
        if _internal_portal(original, source_doc):
            continue
        identifier = original.get("id")
        if identifier not in positions:
            raise ValueError(f"metadata.entityPositions is missing surviving entity {identifier!r}")
        world_position = _xyz(positions[identifier], f"entityPositions[{identifier!r}]")
        x, y = _grid_position(world_position, origin, width, height, f"entity {identifier}")
        entity = deepcopy(original)
        entity["x"], entity["y"] = x, y
        entity["storey"] = _storey_index(world_position[2], level_zs, f"entity {identifier}")
        if "volume" in entity:
            if identifier == "e4":
                entity["volume"] = deepcopy(COMBAT_VOLUME)
            else:
                old_anchor = _old_anchor(original, source_doc)
                new_anchor = (origin[0] + (x + 0.5) * CELL_METERS,
                              origin[1] + (y + 0.5) * CELL_METERS,
                              world_position[2])
                entity["volume"] = _translated_volume(entity["volume"], old_anchor, new_anchor)
        result_entities.append(entity)

    result_by_id = {entity["id"]: entity for entity in result_entities}
    expected_survivors = set(source_by_id) - INTERNAL_PORTAL_IDS
    if result_by_id.keys() != expected_survivors:
        raise ValueError("entity IDs changed beyond removal of internal self-target portals")
    remaining_portals = [entity["id"] for entity in result_entities if entity.get("type") == "portal"]
    if remaining_portals != ["e23"]:
        raise ValueError(f"only the exterior portal e23 may remain; found {remaining_portals}")
    if {entity["id"] for entity in result_entities if entity.get("type") == "encounter"} != ENCOUNTER_IDS:
        raise ValueError("the six Arena encounter markers were not preserved")
    if any("volume" not in result_by_id[identifier] for identifier in ENCOUNTER_IDS):
        raise ValueError("all six Arena encounter markers must retain their volumes")
    if {entity["id"] for entity in result_entities if entity.get("type") == "arenaEntry"} != ARENA_ENTRY_IDS:
        raise ValueError("the four arenaEntry markers were not preserved")
    if any(result_by_id[identifier]["storey"] != result_by_id["e4"]["storey"]
           for identifier in ENCOUNTER_IDS | ARENA_ENTRY_IDS):
        raise ValueError("combat markers and arenaEntry markers must stay on the sand storey")
    for identifier, expected_name in SPAWN_NAMES.items():
        if result_by_id[identifier].get("name") != expected_name:
            raise ValueError(f"spawnPoint name changed for {identifier}")
    if abs(level_zs[result_by_id["e4"]["storey"]]) > 1e-4:
        raise ValueError("the combat zone e4 must remain on the z=0 sand storey")

    for original in source_entities:
        identifier = original.get("id")
        if identifier in INTERNAL_PORTAL_IDS:
            if not _internal_portal(original, source_doc):
                raise ValueError(f"refusing to remove non-self-target portal {identifier}")
            continue
        updated = result_by_id[identifier]
        for key, value in original.items():
            if key not in {"x", "y", "storey", "volume"} and updated.get(key) != value:
                raise ValueError(f"gameplay semantics changed on {identifier}.{key}")

    entry_raw = metadata.get("entry") if isinstance(metadata, Mapping) else getattr(metadata, "entry", None)
    if entry_raw is None:
        entry_position = _xyz(positions["e21"], "entityPositions['e21']")
    else:
        entry_position = _xyz(entry_raw, "metadata.entry")
    entry_x, entry_y = _grid_position(entry_position, origin, width, height, "entry")

    return {
        "width": width,
        "height": height,
        "origin": [origin[0], origin[1]],
        "storeys": levels,
        "storeyLevels": True,
        "tiles": [{"x": entry_x, "y": entry_y, "type": "entry"}],
        "layers": [],
        "entities": result_entities,
    }


def validate_remap(source_doc: Mapping[str, Any], patch: Mapping[str, Any]) -> dict[str, Any]:
    """Return compact evidence for key preservation invariants (no filesystem writes)."""
    source_ids = {entity.get("id") for entity in source_doc.get("entities", ())}
    entities = patch.get("entities", ())
    by_id = {entity["id"]: entity for entity in entities}
    portals = [entity["id"] for entity in entities if entity.get("type") == "portal"]
    outside = [
        entity["id"]
        for entity in entities
        if not (0 <= entity["x"] < patch["width"] and 0 <= entity["y"] < patch["height"])
    ]
    zone = by_id.get("e4", {}).get("volume", {})
    encounter_volumes_inside_zone = all(
        all(zone["min"][axis] <= entity["volume"]["min"][axis]
            and entity["volume"]["max"][axis] <= zone["max"][axis] for axis in range(3))
        for entity in entities
        if entity.get("type") == "encounter" and "volume" in entity and zone
    ) and sum(entity.get("type") == "encounter" and "volume" in entity for entity in entities) == 6
    storeys = patch.get("storeys", ())
    arena_entries_inside_zone = all(
        zone["min"][axis]
        <= patch["origin"][axis] + ((entity["x"] if axis == 0 else entity["y"]) + 0.5) * CELL_METERS
        <= zone["max"][axis]
        for entity in entities
        if entity.get("type") == "arenaEntry"
        for axis in range(2)
    ) and all(
        zone["min"][2] <= storeys[entity["storey"]]["z"] <= zone["max"][2]
        for entity in entities
        if entity.get("type") == "arenaEntry"
        and 0 <= entity.get("storey", -1) < len(storeys)
    ) if zone else False
    combat_markers_share_storey = all(
        by_id.get(identifier, {}).get("storey") == by_id.get("e4", {}).get("storey")
        for identifier in ENCOUNTER_IDS | ARENA_ENTRY_IDS
    )
    expected_ids = source_ids - INTERNAL_PORTAL_IDS
    return {
        "sourceEntityCount": len(source_ids),
        "resultEntityCount": len(by_id),
        "removedInternalPortals": sorted(source_ids - set(by_id)),
        "preservedExpectedEntityIds": set(by_id) == expected_ids,
        "remainingPortalIds": portals,
        "onlyExteriorPortalRetained": portals == ["e23"],
        "encounterIds": sorted(entity["encounterId"] for entity in entities if entity.get("type") == "encounter"),
        "arenaEntryCount": sum(entity.get("type") == "arenaEntry" for entity in entities),
        "spawnNamesPreserved": all(by_id[key].get("name") == name for key, name in SPAWN_NAMES.items()),
        "entitiesOutOfBounds": outside,
        "entryTileCount": sum(tile.get("type") == "entry" for tile in patch.get("tiles", ())),
        "combatVolume": by_id.get("e4", {}).get("volume"),
        "encounterVolumesInsideCombatZone": encounter_volumes_inside_zone,
        "arenaEntriesInsideCombatZoneXY": arena_entries_inside_zone,
        "combatMarkersShareStorey": combat_markers_share_storey,
        "allChecksPassed": (
            set(by_id) == expected_ids
            and portals == ["e23"]
            and not outside
            and sum(tile.get("type") == "entry" for tile in patch.get("tiles", ())) == 1
            and by_id.get("e4", {}).get("volume") == COMBAT_VOLUME
            and encounter_volumes_inside_zone
            and arena_entries_inside_zone
            and combat_markers_share_storey
        ),
    }
