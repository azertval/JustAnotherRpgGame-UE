# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

"""Idempotency tests for the Arena gameplay remapper, without Saved inputs."""

from copy import deepcopy

from arena_fate_modern_gameplay import remap_gameplay, validate_remap


SOURCE_ORIGIN = [100.0, -40.0]
TARGET_ORIGIN = [-100.0, -40.0]


def _cell_center(column: int, row: int) -> tuple[float, float]:
    return (
        TARGET_ORIGIN[0] + (column + 0.5) * 1.5,
        TARGET_ORIGIN[1] + (row + 0.5) * 1.5,
    )


def _fixture() -> tuple[dict, dict]:
    storeys = [{"name": name, "z": z} for name, z in (("sand", 0), ("gallery", 12), ("crypt", -12))]

    def entity(identifier, kind, column, row, storey=0, **fields):
        return {
            "id": identifier,
            "type": kind,
            "x": column,
            "y": row,
            "storey": storey,
            **fields,
        }

    source_entities = [
        entity("e1", "spawnPoint", 6, 12, name="from-undercroft"),
        entity("e2", "portal", 4, 12, targetMap="arena/fixture", arrival="from-arena-of-fate"),
        entity("e4", "combatZone", 6, 5, name="sand", volume={"min": [9, 7.5, -0.5], "max": [42, 28.5, 4]}),
        entity("e5", "npc", 9, 11, appearance="pantin", dialogue="maitre-arene", presenceFlag="quest.before"),
        entity("e6", "encounter", 25, 11, volume={}, encounterId="arene-bandits", presenceFlag="quest.before", presenceTest="equals", presenceValue="condamne", respawns=False),
        entity("e7", "encounter", 24, 7, volume={}, encounterId="arene-gladiateurs", presenceFlag="reward.1", presenceTest="set", respawns=False),
        entity("e8", "encounter", 24, 9, volume={}, encounterId="arene-morts", presenceFlag="reward.2", presenceTest="set", respawns=False),
        entity("e9", "encounter", 24, 13, volume={}, encounterId="arene-veteran", presenceFlag="reward.3", presenceTest="set", respawns=False),
        entity("e10", "encounter", 24, 15, volume={}, encounterId="arene-capitaine", presenceFlag="reward.4", presenceTest="set", respawns=False),
        entity("e11", "encounter", 23, 11, volume={}, encounterId="arene-champion", presenceFlag="reward.5", presenceTest="set", respawns=False),
        entity("e12", "spawnPoint", 27, 12, name="from-undercroft-dead"),
        entity("e19", "spawnPoint", 6, 12, 1, name="from-arena-of-fate"),
        entity("e20", "portal", 4, 12, 1, targetMap="arena/fixture", arrival="from-undercroft"),
        entity("e21", "spawnPoint", 16, 19, 1, name="from-arenarea"),
        entity("e23", "portal", 16, 21, 1, targetMap="arena/outer", arrival="from-arena-of-fate"),
        entity("e24", "spawnPoint", 22, 3, 1, name="from-catacombs"),
        entity("e26", "spawnPoint", 27, 12, 1, name="from-dead-gate"),
        entity("e32", "spawnPoint", 22, 7, 2, name="catacombs-from-undercroft"),
        entity("e28", "arenaEntry", 9, 10, rank=0, side="allies"),
        entity("e29", "arenaEntry", 10, 10, rank=1, side="allies"),
        entity("e30", "arenaEntry", 11, 10, rank=2, side="allies"),
        entity("e31", "arenaEntry", 12, 10, rank=3, side="allies"),
    ]
    # Volumes surround their authored source-cell anchors, using a nonzero map origin.
    for item in source_entities:
        if item["type"] != "encounter":
            continue
        x = SOURCE_ORIGIN[0] + (item["x"] + 0.5) * 1.5
        y = SOURCE_ORIGIN[1] + (item["y"] + 0.5) * 1.5
        item["volume"] = {"min": [x - 0.75, y - 0.75, 0], "max": [x + 0.75, y + 0.75, 2]}

    positions = {
        "e1": [*_cell_center(66, 26), 0],
        "e4": [*_cell_center(66, 26), 0],
        "e5": [*_cell_center(58, 25), 0],
        "e6": [*_cell_center(77, 27), 0],
        "e7": [*_cell_center(76, 27), 0],
        "e8": [*_cell_center(76, 28), 0],
        "e9": [*_cell_center(76, 29), 0],
        "e10": [*_cell_center(76, 30), 0],
        "e11": [*_cell_center(75, 27), 0],
        "e12": [*_cell_center(67, 26), -6],
        "e19": [*_cell_center(68, 26), 12],
        "e21": [*_cell_center(69, 26), 24],
        "e23": [*_cell_center(26, 26), -6],
        "e24": [*_cell_center(70, 26), -12],
        "e26": [*_cell_center(71, 26), 36],
        "e32": [*_cell_center(72, 26), 46.8],
        "e28": [*_cell_center(62, 26), 0],
        "e29": [*_cell_center(63, 26), 0],
        "e30": [*_cell_center(64, 26), 0],
        "e31": [*_cell_center(65, 26), 0],
    }
    metadata = {
        "origin": TARGET_ORIGIN,
        "width": 136,
        "height": 112,
        "levels": [
            {"name": name, "z": z}
            for name, z in (
                ("sand", 0),
                ("locker", -6),
                ("crypt", -12),
                ("stands", 12),
                ("gallery", 24),
                ("attic", 36),
                ("roof", 46.8),
            )
        ],
        "entityPositions": positions,
        "entry": [*_cell_center(66, 26), 0],
    }
    source = {
        "place": "arena/fixture",
        "origin": SOURCE_ORIGIN,
        "width": 40,
        "height": 30,
        "storeys": storeys,
        "entities": source_entities,
    }
    return source, metadata


def test_remap_gameplay_is_idempotent_with_nonzero_origin_and_keeps_edited_narrative():
    source, metadata = _fixture()
    first = remap_gameplay(source, metadata)
    first_by_id = {item["id"]: item for item in first["entities"]}

    assert "e2" not in first_by_id and "e20" not in first_by_id
    assert first_by_id["e23"]["targetMap"] == "arena/outer"
    assert len([item for item in first["entities"] if item["type"] == "encounter"]) == 6
    assert len([item for item in first["entities"] if item["type"] == "arenaEntry"]) == 4
    assert validate_remap(source, first)["allChecksPassed"]

    expected_volumes = {
        identifier: deepcopy(first_by_id[identifier]["volume"])
        for identifier in ("e4", "e6", "e7", "e8", "e9", "e10", "e11")
    }
    first_by_id["e6"]["presenceFlag"] = "quest.updated-after-first-remap"

    second = remap_gameplay(first, metadata)
    second_by_id = {item["id"]: item for item in second["entities"]}

    assert second == first
    assert {identifier: second_by_id[identifier]["volume"] for identifier in expected_volumes} == expected_volumes
    assert second_by_id["e6"]["presenceFlag"] == "quest.updated-after-first-remap"
    assert second["tiles"] == first["tiles"]
    assert validate_remap(first, second)["allChecksPassed"]
