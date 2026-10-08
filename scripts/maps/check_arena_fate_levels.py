#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Contrôle la cohérence des trois niveaux de l'Arena of Fate, en lecture seule.

Ce que `LevelEditor --check` ne regarde pas, et que la décision de l'auteur du 4 octobre 2026
demande : les trois cartes ont la **même emprise**, un escalier est **aux mêmes cases** à l'étage
qu'il quitte et à celui qu'il rejoint, chaque sous-sol porte son enceinte, et rien d'impérial ne
descend sous le sable (LOT-106, LOT-107, LOT-157). Complète `check_arena_fate.py`, qui contrôle
l'iconographie de l'arène.

Usage :
    python scripts/maps/check_arena_fate_levels.py      # code de sortie non nul sur un écart
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLACE = "central-empire/capital/arenarea/arena-of-fate"
LEVELS = {"arène": PLACE, "niveau −1": PLACE + "/undercroft", "catacombes": PLACE + "/catacombs"}
# Un escalier tient deux cases sur trois : le portail du haut et celui du bas sont dans cette emprise.
STAIR_REACH = 2
ENCLOSURES = {"niveau −1": "af-undercroft-shell", "catacombes": "af-catacomb-shell"}
EFFIGIES = {f"meshy-effigy-{name}" for name in ("cthraxis", "droggath", "krynnethoth", "zulvath")}
IMPERIAL = ("banner-empire", "banner-tanarean-empire", "portal-guardian-lion")


def pieces(level: dict) -> list[str]:
    placed = [tile["piece"] for layer in level["layers"] for tile in layer.get("tiles", [])
              if "piece" in tile]
    return placed + [entity["piece"] for entity in level["entities"] if entity.get("piece")]


def check() -> list[str]:
    levels = {name: json.loads((ROOT / "Source/Elements/Levels" / f"{path}.json")
                               .read_text(encoding="utf-8")) for name, path in LEVELS.items()}
    names = {path: name for name, path in LEVELS.items()}
    errors = []
    sizes = {(level["width"], level["height"]) for level in levels.values()}
    if len(sizes) != 1:
        errors.append("les trois niveaux n'ont pas la même emprise : " + ", ".join(
            f"{name} {level['width']} × {level['height']}" for name, level in levels.items()))
    for name, level in levels.items():
        spawns = {entity["name"]: (entity["x"], entity["y"]) for entity in level["entities"]
                  if entity["type"] == "spawnPoint"}
        for portal in (entity for entity in level["entities"] if entity["type"] == "portal"):
            target = names.get(portal["targetMap"])
            if target is None:
                continue  # le parvis d'Arenarea : hors du monument
            back = [other for other in levels[target]["entities"]
                    if other["type"] == "portal" and other["targetMap"] == LEVELS[name]]
            here = (portal["x"], portal["y"])
            nearest = min((max(abs(other["x"] - here[0]), abs(other["y"] - here[1]))
                           for other in back), default=None)
            if nearest is None:
                errors.append(f"{name} {here} : aucun escalier ne remonte depuis « {target} »")
            elif nearest > STAIR_REACH:
                errors.append(f"{name} {here} : l'escalier de « {target} » le plus proche est à "
                              f"{nearest} cases — les deux étages ne se superposent pas")
            arrival = next((other for other in levels[target]["entities"]
                            if other["type"] == "spawnPoint" and other["name"] == portal["arrival"]),
                           None)
            if arrival is not None and max(abs(arrival["x"] - here[0]),
                                           abs(arrival["y"] - here[1])) > STAIR_REACH + 2:
                errors.append(f"{name} {here} : on arrive en ({arrival['x']}, {arrival['y']}) de "
                              f"« {target} », loin du pied de l'escalier")
        if not spawns:
            errors.append(f"{name} : aucun point d'arrivée")
        placed = pieces(level)
        if name in ENCLOSURES:
            if ENCLOSURES[name] not in placed:
                errors.append(f"{name} : l'enceinte {ENCLOSURES[name]} n'est pas posée")
            for piece in placed:
                if any(mark in piece for mark in IMPERIAL):
                    errors.append(f"{name} : symbole impérial sous le sable ({piece})")
        effigies = [piece for piece in placed if piece in EFFIGIES]
        if name == "catacombes" and sorted(effigies) != sorted(EFFIGIES):
            errors.append(f"catacombes : les quatre Ungods enchaînés, une fois chacun — {effigies}")
        if name != "catacombes" and (effigies or "banner-cult" in placed):
            errors.append(f"{name} : le Culte et ses Ungods ne sont qu'aux catacombes")
    return errors


def main() -> int:
    errors = check()
    for error in errors:
        print(f"erreur : {error}", file=sys.stderr)
    if not errors:
        print("Arena of Fate : trois niveaux de même emprise, escaliers superposés.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
