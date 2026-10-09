#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Le mode Quêtes (LOT-144, LOT-1018) : une carte vue à une étape de quête, sur les mêmes JSON
que le jeu — les quêtes (`Source/Elements/World/quests/`), les dialogues
(`Source/Elements/World/dialogues/`) et la description de la carte (format v5).

Une quête change ce qu'une carte montre et ce qu'elle laisse passer : une entité paraît ou
disparaît sous un drapeau (`presenceFlag`, `presenceTest`, `presenceValue`, `EX-EXP-009`), un
portail attend un drapeau (`requiresFlag`), une zone en pose un (`triggerFlag`). Ce script répond,
pour une carte et des drapeaux donnés (ou l'étape d'une quête) :

- **ce qui est présent**, entité par entité, avec la condition qui en décide ;
- **les drapeaux** que la carte lit et pose, et ceux qu'aucune quête, aucun dialogue, aucune
  rencontre ne déclare (un drapeau mal orthographié ne s'ouvre jamais) ;

et, lancé dans l'éditeur du moteur sur le niveau construit (`build_level.py`), **cache** dans la
vue de l'éditeur les acteurs des entités absentes (`JadgEntity:<id>`, `JadgMarker:<id>`) : on voit
la carte telle qu'elle est à cette étape, sans rien changer au niveau ni au texte.

Usage :
    python scripts/maps/quest_mode.py essai/parvis                                  # les drapeaux de la carte
    python scripts/maps/quest_mode.py essai/parvis --step pommes/acceptee           # la carte à une étape
    python scripts/maps/quest_mode.py essai/parvis --flag quete.pommes=acceptee     # à des drapeaux
    python scripts/maps/quest_mode.py --check                                       # toutes les cartes
    UnrealEditor.exe … -run=pythonscript -script=…/quest_mode.py -JadgMap=essai/parvis -JadgStep=pommes/acceptee

La règle de présence est celle de Core (`core::isEntityPresent`, `Core/World/EntityPresence.cpp`) :
sans drapeau, présente ; `set` / `unset` ; `equals` / `notEquals` contre une liste de valeurs
séparées par `|` ; un drapeau à valeurs sans test vaut `equals`, un fait sans test vaut `set`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jadg_map  # noqa: E402

WORLD = jadg_map.ROOT / "Source" / "Elements" / "World"
ENCOUNTERS = jadg_map.ROOT / "Source" / "Elements" / "Rpg" / "encounters"
# Les drapeaux que le jeu fabrique de lui-même : un coffre ouvert, une rencontre gagnée, un jet raté.
MADE = (re.compile(r"^encounter/[^/]+/won$"), re.compile(r"^dialogue/[^/]+/[^/]+/failed$"),
        re.compile(r"^quest/[^/]+/step/[^/]+$"), re.compile(r"^.+#.+$"))


def quests() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((WORLD / "quests").glob("*.json"))]


def declared_flags() -> dict[str, list[str]]:
    """Les drapeaux déclarés : par une quête (ses valeurs), posés par un dialogue ou une étape."""
    flags: dict[str, list[str]] = {}
    for quest in quests():
        for flag in quest.get("flags", ()):
            flags[flag["id"]] = list(flag.get("values", ()))
        for step in quest.get("steps", ()):
            for effect in step.get("effects", ()):
                if effect.get("flag"):
                    flags.setdefault(effect["flag"], [])
            for condition in step.get("when", ()):
                flags.setdefault(condition["flag"], [])
    for path in sorted((WORLD / "dialogues").glob("*.json")):
        for match in re.finditer(r'"(?:flag|setFlag|requiresFlag)"\s*:\s*"([^"]+)"', path.read_text(encoding="utf-8")):
            flags.setdefault(match.group(1), [])
    return flags


def step_flags(step: str) -> dict[str, str]:
    """Les drapeaux qu'une étape de quête (`<quête>/<étape>`) suppose : ses conditions tenues, plus
    l'étape elle-même (`quest/<quête>/step/<étape>`)."""
    quest_id, _, step_id = step.partition("/")
    for quest in quests():
        if quest["id"] != quest_id:
            continue
        values = {flag["id"]: flag.get("initial", "") for flag in quest.get("flags", ())}
        for current in quest.get("steps", ()):
            for condition in current.get("when", ()):
                values[condition["flag"]] = condition.get("equals", "1")
            for effect in current.get("effects", ()):
                values[effect["flag"]] = effect.get("value", "1")
            values[f"quest/{quest_id}/step/{current['id']}"] = "1"
            if current["id"] == step_id:
                return values
    raise SystemExit(f"étape « {step} » inconnue")


def present(entity: dict, flags: dict[str, str]) -> tuple[bool, str]:
    """La présence d'une entité sous `flags`, et la condition qui en décide (règle de Core)."""
    flag = entity.get("presenceFlag", "")
    if not flag:
        return True, "toujours"
    values = [v for v in entity.get("presenceValue", "").split("|") if v]
    test = entity.get("presenceTest", "") or ("equals" if values else "set")
    value = flags.get(flag)
    if test == "set":
        return bool(value), f"{flag} posé"
    if test == "unset":
        return not value, f"{flag} non posé"
    if test == "equals":
        return value in values, f"{flag} ∈ {{{', '.join(values)}}}"
    if test == "notEquals":
        return value not in values, f"{flag} ∉ {{{', '.join(values)}}}"
    return False, f"test inconnu « {test} »"


def map_flags(doc: dict) -> dict[str, list[str]]:
    """Les drapeaux qu'une carte lit (présence, portail) et pose (zone), par entité."""
    used: dict[str, list[str]] = {}
    for entity in doc.get("entities", ()):
        for key in ("presenceFlag", "requiresFlag", "triggerFlag"):
            if entity.get(key):
                used.setdefault(entity[key], []).append(f"{entity['id']}.{key}")
    return used


def undeclared(doc: dict, declared: dict[str, list[str]]) -> list[str]:
    return sorted(flag for flag in map_flags(doc)
                  if flag not in declared and not any(pattern.match(flag) for pattern in MADE))


def view(map_id: str, flags: dict[str, str]) -> list[tuple[dict, bool, str]]:
    path = jadg_map.find(map_id)
    if path is None:
        raise SystemExit(f"carte « {map_id} » introuvable")
    doc = jadg_map.read(path)
    return [(entity, *present(entity, flags)) for entity in doc.get("entities", ())]


def hide_in_editor(map_id: str, flags: dict[str, str]) -> None:
    """Dans l'éditeur : cache dans la vue les acteurs des entités absentes, montre les autres."""
    import unreal  # noqa: PLC0415 - seulement dans l'éditeur du moteur

    world = unreal.EditorLoadingAndSavingUtils.load_map(jadg_map.package(map_id))
    states = {entity["id"]: shown for entity, shown, _ in view(map_id, flags)}
    hidden = 0
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for tag in (str(t) for t in actor.tags):
            for prefix in ("JadgEntity:", "JadgMarker:"):
                if tag.startswith(prefix) and tag[len(prefix):] in states:
                    shown = states[tag[len(prefix):]]
                    actor.set_is_temporarily_hidden_in_editor(not shown)
                    hidden += 0 if shown else 1
    for walker in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.load_class(None, "/Script/JustAnotherRpgGame.JadgWalker")):
        identifier = walker.get_editor_property("entity_id")
        if identifier in states:
            walker.set_is_temporarily_hidden_in_editor(not states[identifier])
            hidden += 0 if states[identifier] else 1
    unreal.log(f"[Quetes] {map_id} : {hidden} acteur(s) caché(s) à cette étape")


def parse_flags(pairs: list[str]) -> dict[str, str]:
    flags = {}
    for pair in pairs:
        key, _, value = pair.partition("=")
        flags[key] = value or "1"
    return flags


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("map", nargs="?", help="la carte, par son identifiant")
    parser.add_argument("--step", help="l'étape de quête (<quête>/<étape>)")
    parser.add_argument("--flag", action="append", default=[], help="un drapeau, clé=valeur (ou clé seule)")
    parser.add_argument("--check", action="store_true", help="les drapeaux qu'aucune quête ne déclare, sur toutes les cartes")
    arguments = parser.parse_args(argv)

    declared = declared_flags()
    if arguments.check:
        problems = []
        for map_id, path in jadg_map.all_maps().items():
            problems += [f"{map_id} : drapeau « {flag} » que rien ne déclare" for flag in undeclared(jadg_map.read(path), declared)]
        for problem in problems:
            print(problem, file=sys.stderr)
        print(f"{len(jadg_map.all_maps())} carte(s), {len(problems)} drapeau(x) non déclaré(s)")
        return 1 if problems else 0
    if not arguments.map:
        parser.print_help()
        return 2
    flags = step_flags(arguments.step) if arguments.step else {}
    flags.update(parse_flags(arguments.flag))
    doc = jadg_map.read(jadg_map.find(arguments.map) or Path("/absente"))
    print(f"{arguments.map} — drapeaux lus et posés :")
    for flag, uses in sorted(map_flags(doc).items()):
        mark = "" if flag in declared or any(p.match(flag) for p in MADE) else "  (déclaré nulle part)"
        print(f"  {flag} : {', '.join(uses)}{mark}")
    if arguments.step or arguments.flag:
        print(f"à {arguments.step or 'ces drapeaux'} :")
        for entity, shown, why in view(arguments.map, flags):
            print(f"  {'présent' if shown else 'absent '}  {entity['id']} ({entity['type']}) — {why}")
    return 1 if undeclared(doc, declared) else 0


def editor_main() -> None:
    import import_master_unreal as master_import  # noqa: PLC0415

    map_id = master_import.command_line_option("JadgMap")
    step = master_import.command_line_option("JadgStep")
    hide_in_editor(map_id, step_flags(step) if step else {})


if __name__ == "__main__":
    try:
        import unreal  # noqa: F401
    except ImportError:
        sys.exit(main())
    sys.path.insert(0, str(jadg_map.ROOT / "scripts" / "assetsGeneration"))
    editor_main()
