#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Le plan des deux sous-sols de l'Arena of Fate, écrit en gestes de l'éditeur.

Les trois niveaux du Colisée tiennent dans la **même emprise** de 34 × 24 cases (décision de
l'auteur du 4 octobre 2026) : l'ovale de la coque de l'arène, repris par l'enceinte de chaque
sous-sol (`scripts/assetsGeneration/arena_fate_enclosures.py`). Un escalier occupe les mêmes cases
à l'étage qu'il quitte et à celui qu'il rejoint :

| Escalier | Cases | En haut | En bas |
|---|---|---|---|
| porte du triomphe (ouest) | (2-4, 11-12) | arène | niveau −1 |
| porte des morts (est) | (29-31, 11-12) | arène | niveau −1 |
| parvis d'Arenarea (sud, sous le portail) | (16-17, 20-22) | parvis | niveau −1 |
| descente des catacombes (fond de la prison) | (22-23, 4-6) | niveau −1 | catacombes |

Le niveau −1 suit le référentiel de la Capitale et le LOT-107 : les **vestiaires** à l'ouest, la
**prison** à l'est, qui ne communiquent que par la galerie axiale menant à l'escalier du triomphe.
Les catacombes suivent le LOT-157 : quatre chapelles en croix, une par Ungod enchaîné, autour du
sanctuaire du Culte ; aucun symbole impérial sous le sable.

Usage :
    python scripts/maps/arena_fate_levels.py [--preview] [--output DOSSIER]

Le script n'écrit aucune carte : il écrit `undercroft.json` et `catacombs.json`, des gestes que
`LevelEditor --apply` rejoue sur une carte de 34 × 24 (voir le guide des données), et
`arena-of-fate.json`, qui n'ajoute à la carte du sable que les feux de son pourtour.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLACE = "central-empire/capital/arenarea/arena-of-fate"
OUTPUT = ROOT / "Tools/Assets3D/Regions" / PLACE / "Production/V4/Gestures"
WIDTH, HEIGHT = 34, 24
# Le nu intérieur de l'enceinte et son épaisseur, en mètres (`arena_fate_enclosures.py`).
INNER_X, INNER_Y, THICK = 23.4, 15.9, 1.45
NORTH, SOUTH, EAST, WEST = (0, -1), (0, 1), (1, 0), (-1, 0)
# La case du marqueur de chaque rencontre de la série de l'arène, sur la carte du sable.
ARENA_ENCOUNTERS = {
    "arene-bandits": (25, 11), "arene-gladiateurs": (24, 7), "arene-morts": (24, 9),
    "arene-veteran": (24, 13), "arene-capitaine": (24, 15), "arene-champion": (23, 11),
}


def _ellipse(column: int, row: int, rx: float, ry: float) -> float:
    x = (column + 0.5) * 1.5 - WIDTH * 0.75
    y = HEIGHT * 0.75 - (row + 0.5) * 1.5
    return (x / rx) ** 2 + (y / ry) ** 2


def inside(column: int, row: int) -> bool:
    """Vrai si la case est dans l'enceinte : son centre à 0,45 m au moins en deçà du nu."""
    return _ellipse(column, row, INNER_X - 0.45, INNER_Y - 0.45) <= 1.0


def in_ring(column: int, row: int) -> bool:
    """Vrai si la case est prise dans l'épaisseur de l'enceinte : un mur peut s'y achever."""
    return not inside(column, row) and _ellipse(column, row, INNER_X + THICK, INNER_Y + THICK) <= 1.0


class Plan:
    """Un niveau : ses murs, ses pièces, son praticable, et les gestes qui les écrivent."""

    def __init__(self, suffix: str, family: str, floor: str, shell: str):
        self.map = PLACE + suffix
        self.family = family
        self.floor = floor
        self.shell = shell
        self.blocked: set[tuple[int, int]] = set()
        # Les cases de mur : vrai si le mur porte une torche.
        self.walls: dict[tuple[int, int], bool] = {}
        # Les cases d'une baie : un arc y prolonge le mur, on y passe.
        self.openings: set[tuple[int, int]] = set()
        self.pieces: list[tuple[str, str, int, int]] = []
        self.entities: list[tuple[str, list[int], dict]] = []
        self.notes: list[tuple[int, int, str]] = []
        self.bare: set[tuple[int, int]] = set()

    # --- Les murs ---------------------------------------------------------------------------------
    def wall(self, cells, torches=()):
        for cell in cells:
            if inside(*cell) or in_ring(*cell):
                self.walls[cell] = cell in torches
                self.blocked.add(cell)

    def hwall(self, row, first, last, torches=()):
        self.wall([(x, row) for x in range(first, last + 1)], {(x, row) for x in torches})

    def vwall(self, column, first, last, torches=()):
        self.wall([(column, y) for y in range(first, last + 1)], {(column, y) for y in torches})

    def arch(self, column, row, axis):
        """Une baie de deux cases dans un mur : l'arc remplace le mur, on y passe."""
        cells = [(column, row), (column + 1, row)] if axis == "x" else [(column, row), (column, row + 1)]
        for cell in cells:
            self.walls.pop(cell, None)
            self.blocked.discard(cell)
            self.openings.add(cell)
        self.pieces.append(("relief", f"af-arch-{self.family}-{axis}", column, row))

    # --- Les pièces -------------------------------------------------------------------------------
    def put(self, piece, column, row, footprint=(1, 1), solid=True, layer="relief", into_wall=False):
        """Pose une pièce ; une pièce pleine prend ses cases au praticable, qui doivent être libres."""
        cells = [(column + dx, row + dy) for dx in range(footprint[0]) for dy in range(footprint[1])]
        for cell in cells:
            if into_wall:
                self.walls.pop(cell, None)
            elif solid and (cell in self.blocked or not (inside(*cell) or in_ring(*cell))):
                raise ValueError(f"{self.map} : {piece} en {cell} tombe sur une case prise")
        if solid:
            self.blocked.update(cells)
        self.pieces.append((layer, piece, column, row))

    def free(self, cells):
        """Rend praticables des cases d'une pièce pleine : les marches d'un escalier."""
        self.blocked.difference_update(cells)

    def entity(self, kind, at, **properties):
        self.entities.append((kind, list(at), properties))

    # --- Ce qui s'en déduit -----------------------------------------------------------------------
    def walkable(self) -> set[tuple[int, int]]:
        return {(x, y) for x in range(WIDTH) for y in range(HEIGHT)
                if inside(x, y) and (x, y) not in self.blocked}

    def reachable(self, start) -> set[tuple[int, int]]:
        walk = self.walkable()
        seen = {start}
        queue = deque(seen)
        while queue:
            x, y = queue.popleft()
            for dx, dy in (NORTH, SOUTH, EAST, WEST):
                cell = (x + dx, y + dy)
                if cell in walk and cell not in seen:
                    seen.add(cell)
                    queue.append(cell)
        return seen

    def seal_pockets(self, entry, largest=4):
        """Condamne les recoins qu'un meuble a coupés du reste ; refuse une salle injoignable."""
        walk = self.reachable(entry)
        stray = self.walkable() - walk
        while stray:
            pocket = {next(iter(stray))}
            queue = deque(pocket)
            while queue:
                x, y = queue.popleft()
                for dx, dy in (NORTH, SOUTH, EAST, WEST):
                    cell = (x + dx, y + dy)
                    if cell in stray and cell not in pocket:
                        pocket.add(cell)
                        queue.append(cell)
            if len(pocket) > largest:
                raise ValueError(f"{self.map} : {len(pocket)} cases injoignables autour de "
                                 f"{sorted(pocket)[0]}")
            self.blocked |= pocket
            stray -= pocket

    def wall_pieces(self) -> list[tuple[str, str, int, int]]:
        """La pièce de chaque case de mur, d'après ses voisines : droite, angle, ou croisement."""
        linked = set(self.walls) | self.openings
        placed = []
        for (x, y), torch in sorted(self.walls.items(), key=lambda item: (item[0][1], item[0][0])):
            arms = {name for name, (dx, dy) in (("n", NORTH), ("s", SOUTH), ("e", EAST), ("w", WEST))
                    if (x + dx, y + dy) in linked}
            across, along = bool(arms & {"e", "w"}), bool(arms & {"n", "s"})
            # Les cloisons restent basses : sous cette caméra un mur de trois mètres cache près de
            # quatre cases derrière lui. La hauteur vient de l'enceinte, des arcs et des voûtes ;
            # seul un mur à torche monte, là où le plan le demande.
            low = not torch
            suffix = "-low" if low else ""
            stem = f"af-wall-{self.family}"
            corner = {frozenset("ws"): "", frozenset("es"): "-nw",
                      frozenset("en"): "-sw", frozenset("wn"): "-se"}
            if across and along and len(arms) == 2:
                placed.append(("relief", f"{stem}-corner{corner[frozenset(arms)]}{suffix}", x, y))
                continue
            axis = "y" if along and not across else "x" if across and not along else \
                "x" if {"e", "w"} <= arms else "y"
            torched = torch and not low and f"{axis}" in ("x", "y")
            placed.append(("relief", f"af-wall-torch-{self.family}-{axis}" if torched
                           else f"{stem}-{axis}{suffix}", x, y))
            if across and along:
                # Un croisement : la branche qui manque à la pièce droite, sur une seconde couche.
                if axis == "x":
                    extra = f"{stem}-y{suffix}" if {"n", "s"} <= arms else \
                        f"{stem}-corner{'' if 's' in arms else '-se'}{suffix}"
                else:
                    extra = f"{stem}-corner{'-nw' if 'e' in arms else ''}{suffix}"
                placed.append(("jonctions", extra, x, y))
        return placed

    def gestures(self, entry) -> dict:
        self.seal_pockets(entry)
        walk = self.reachable(entry)
        every = [[x, y] for y in range(HEIGHT) for x in range(WIDTH)]
        gestures: list[dict] = [{"layer": name, "tool": "eraser", "path": every}
                                for name in ("sol", "relief")]
        # Les entités de la carte telle qu'elle est : le plan repose les siennes.
        level = ROOT / "Source/Elements/Levels" / f"{self.map}.json"
        known = [entity["id"] for entity in
                 json.loads(level.read_text(encoding="utf-8")).get("entities", [])] if level.is_file() else []
        if known:
            gestures.append({"select": known, "tool": "entity", "then": "delete"})
        layers = ["enceinte", "jonctions", "sculptures", "voutes"] + (["cadres", "liens"] if self.family == "catacomb" else [])
        for name in layers:
            gestures.append({"tool": "layer", "name": name, "kind": "decor", "floor": 0})
            gestures.append({"layer": name, "tool": "eraser", "path": every})
        if self.family == "catacomb":
            gestures.append({"tool": "layer", "name": "culte", "kind": "decor", "floor": 1})
            gestures.append({"layer": "culte", "tool": "eraser", "path": every})
        ground = sorted(((x, y) for x in range(WIDTH) for y in range(HEIGHT)
                         if inside(x, y) and (x, y) not in self.bare), key=lambda c: (c[1], c[0]))
        for variant in range(3):
            cells = [[x, y] for x, y in ground if (x + 2 * y) % 3 == variant]
            gestures.append({"layer": "sol", "tool": "paint", "piece": self.floor + "abc"[variant],
                             "path": cells})
        # L'enceinte a sa couche : sur celle du relief, la première pièce posée dans son emprise
        # la remplacerait.
        gestures.append({"layer": "enceinte", "tool": "paint", "piece": self.shell, "path": [[0, 0]]})
        for layer, piece, x, y in self.wall_pieces() + self.pieces:
            gestures.append({"layer": layer, "tool": "paint", "piece": piece, "path": [[x, y]]})
        gestures.append({"layer": "collision", "tool": "rectangle", "type": "wall",
                         "from": [0, 0], "to": [WIDTH - 1, HEIGHT - 1]})
        gestures.append({"layer": "collision", "tool": "paint", "type": "empty",
                         "path": [list(cell) for cell in sorted(walk, key=lambda c: (c[1], c[0]))]})
        gestures.append({"layer": "collision", "tool": "paint", "type": "entry", "path": [list(entry)]})
        for kind, at, properties in self.entities:
            gestures.append({"tool": "entity", "kind": kind, "at": at, "set": properties})
        for x, y, text in self.notes:
            gestures.append({"tool": "note", "at": [x, y], "text": text})
        gestures.append({"mapProperties": {"hour": "22:00"}})
        return {"format": "jadg-editor-gestures", "version": 1, "map": self.map, "gestures": gestures}

    def preview(self, entry) -> str:
        walk = self.reachable(entry)
        every = self.walkable()
        marks = {tuple(at): {"portal": "P", "spawnPoint": "s", "prop": "="}.get(kind, "e")
                 for kind, at, _ in self.entities}
        rows = []
        for y in range(HEIGHT):
            row = ""
            for x in range(WIDTH):
                cell = (x, y)
                row += marks.get(cell) or ("#" if cell in self.walls else "n" if cell in self.openings
                                           else "." if cell in walk
                                           else "?" if cell in every else "o" if inside(*cell)
                                           else "~" if in_ring(*cell) else " ")
            rows.append(f"{y:2d} {row}")
        return "\n".join(["   " + "".join(str(x % 10) for x in range(WIDTH))] + rows)


def sculpture(plan: Plan, support: str, piece: str, column: int, row: int, footprint=(1, 1),
              into_wall=False):
    """Une sculpture reçue de l'auteur, sur le support modelé pour elle."""
    plan.put(support, column, row, footprint, into_wall=into_wall)
    plan.put(piece, column, row, footprint, solid=False, layer="sculptures")


def undercroft() -> tuple[Plan, tuple[int, int]]:
    p = Plan("/undercroft", "stone", "af-v3-paving-", "af-undercroft-shell")
    # La galerie axiale, sous le grand axe du sable : de la prison à l'escalier du triomphe.
    p.hwall(10, 8, 32)
    p.hwall(13, 8, 32)
    p.arch(20, 10, "x")
    p.arch(20, 13, "x")
    # La salle du triomphe, à l'ouest : les deux vestiaires y débouchent, chacun par sa baie.
    p.hwall(8, 1, 8)
    p.hwall(15, 1, 8)
    p.wall([(8, 9), (8, 14)])
    p.arch(5, 8, "x")
    p.arch(5, 15, "x")
    # La moitié ouest aux gladiateurs, la moitié est à la prison : un mur plein les sépare.
    p.vwall(17, 0, 9)
    p.vwall(14, 14, 23)
    p.hwall(16, 14, 19)
    p.vwall(19, 16, 23)
    p.arch(14, 18, "y")
    # Les cachots : deux au nord, deux au sud, leurs grilles sur le couloir de garde.
    for column in (24, 27, 30):
        p.vwall(column, 7, 9)
    for column in (22, 25):
        p.vwall(column, 17, 21)
    p.wall([(19, 17), (28, 17), (28, 18), (28, 19)])

    # Les quatre escaliers, aux cases qu'ils ont à l'étage qu'ils rejoignent.
    p.put("af-stair-w", 2, 11, (3, 2))
    p.free([(4, 11), (4, 12)])
    p.put("af-stair-e", 29, 11, (3, 2))
    p.free([(29, 11), (29, 12)])
    p.put("af-stair-s", 16, 20, (2, 3))
    p.free([(16, 20), (17, 20), (16, 21)])
    p.put("af-stairwell", 22, 4, (2, 3))
    p.free([(22, 4), (23, 4)])
    p.bare.update((x, y) for x in (22, 23) for y in (4, 5, 6))

    # Les grilles des cachots, et ce qu'on y laisse.
    for column in (25, 28):
        p.put("af-prison-bars", column, 7, (2, 1))
    p.put("af-prison-bars", 20, 17, (2, 1))
    p.put("af-prison-door", 23, 17, (2, 1))
    for column, row in ((25, 9), (28, 9), (20, 20), (23, 20)):
        p.put("af-pallet", column, row, (2, 1))
    for column, row in ((25, 8), (29, 8), (21, 18), (24, 18)):
        p.put("af-chains", column, row)
    for column, row in ((26, 8), (20, 18), (23, 18)):
        p.put("af-bucket", column, row)
    for cell in ((28, 8), (20, 19), (21, 19), (23, 19), (24, 19), (31, 9), (30, 14), (31, 14)):
        p.blocked.add(cell)  # le fond d'un cachot : on le voit, on n'y entre pas

    # Le vestiaire A (nord-ouest) : bancs, râteliers, une voûte sur ses quatre piles.
    p.put("af-vault", 10, 4, (3, 3), solid=False, layer="voutes")
    p.blocked.update({(10, 4), (12, 4), (10, 6), (12, 6)})
    for column, row in ((6, 5), (14, 4), (14, 7), (10, 8)):
        p.put("af-bench", column, row, (2, 1))
    for column, row in ((9, 9), (13, 9)):
        p.put("af-rack", column, row, (2, 1))
    for cell in ((4, 6), (3, 7), (16, 3), (16, 9)):
        p.put("af-barrel", *cell)
    p.put("af-chest", 12, 9)
    p.put("af-bucket", 8, 5)
    for cell in ((8, 7), (15, 6)):
        p.put("af-brazier", *cell)
    # Le vestiaire B (sud-ouest) : la fontaine, l'armurerie, la porte du parvis.
    sculpture(p, "af-fountain-body", "meshy-fountain-mask", 11, 14, (2, 1))
    p.put("af-vault", 9, 16, (3, 3), solid=False, layer="voutes")
    p.blocked.update({(9, 16), (11, 16), (9, 18), (11, 18)})
    for column, row in ((5, 17), (10, 20)):
        p.put("af-bench", column, row, (2, 1))
    for column, row in ((3, 16), (11, 21)):
        p.put("af-rack", column, row, (2, 1))
    for cell in ((9, 14), (13, 21), (8, 20)):
        p.put("af-barrel", *cell)
    for cell in ((13, 14), (4, 17)):
        p.put("af-chest", *cell)
    p.put("af-bucket", 13, 15)
    for cell in ((7, 18), (13, 19)):
        p.put("af-brazier", *cell)
    # Quatre athlètes dans leurs niches : deux regardent la salle du triomphe, deux le vestiaire.
    for column, row in ((3, 8), (7, 8), (3, 15), (7, 15)):
        sculpture(p, "af-statue-niche-stone", "meshy-neutral-athlete", column, row, into_wall=True)
        p.walls.pop((column, row), None)
        p.openings.add((column, row))
    # La salle du triomphe et la galerie : colonnes, braseros, arcs de la galerie.
    for cell in ((5, 10), (5, 13)):
        p.put("af-column", *cell)
    for cell in ((3, 9), (3, 14)):
        p.put("af-brazier", *cell)
    for column in (11, 15, 24):
        p.pieces.append(("voutes", "af-arch-stone-y", column, 11))
    # Le parvis : le vestibule, sous le portail monumental de la coque.
    for cell in ((15, 17), (18, 17)):
        p.put("af-brazier", *cell)
    for cell in ((15, 20), (18, 20)):
        p.put("af-column", *cell)
    # La prison nord : le corps de garde, la descente des catacombes entre deux colonnes.
    p.put("af-guard-table", 18, 5, (2, 1))
    p.put("af-rack", 18, 9, (2, 1))
    for cell in ((18, 8), (23, 9), (29, 6)):
        p.put("af-barrel", *cell)
    p.put("af-chest", 18, 3)
    for cell in ((21, 4), (24, 4)):
        p.put("af-column", *cell)
    for cell in ((21, 8), (26, 5)):
        p.put("af-brazier", *cell)
    # La prison sud : le couloir de garde, et la salle où l'on descend les morts.
    p.put("af-guard-table", 16, 15, (2, 1))
    for column, row in ((26, 18), (26, 15)):
        p.put("af-pallet", column, row, (2, 1))
    p.put("af-chains", 29, 15)
    for cell in ((19, 14), (25, 14)):
        p.put("af-brazier", *cell)
    p.put("af-barrel", 29, 16)

    p.entity("spawnPoint", (6, 12), name="from-arena-of-fate")
    p.entity("portal", (4, 12), targetMap=PLACE, arrival="from-undercroft", sealed=False, requiresFlag="")
    p.entity("spawnPoint", (16, 19), name="from-arenarea")
    p.entity("prop", (16, 20), piece="af-prison-bars", blocks=True, width=2, height=1,
             presenceFlag="quete.pommes", presenceTest="equals", presenceValue="condamne")
    p.entity("portal", (16, 21), targetMap="central-empire/capital/arenarea",
             arrival="from-arena-of-fate", sealed=False, requiresFlag="")
    p.entity("spawnPoint", (22, 3), name="from-catacombs")
    p.entity("portal", (22, 4), targetMap=PLACE + "/catacombs", arrival="from-undercroft",
             sealed=False, requiresFlag="")
    p.entity("spawnPoint", (27, 12), name="from-dead-gate")
    p.entity("portal", (29, 12), targetMap=PLACE, arrival="from-undercroft-dead", sealed=False,
             requiresFlag="")
    p.notes += [
        (6, 12, "Salle du triomphe : les deux vestiaires et la galerie des condamnés s'y rejoignent, "
                "au pied de l'escalier de la porte du triomphe."),
        (10, 6, "Vestiaire A. Zone neutre : aucun symbole impérial."),
        (10, 18, "Vestiaire B : la fontaine, l'armurerie, la porte du parvis d'Arenarea."),
        (16, 11, "Galerie axiale, sous le sable : le chemin du condamné, de la prison au triomphe."),
        (22, 3, "Descente des catacombes, au fond de la prison."),
        (27, 16, "Salle des morts, au pied de l'escalier de la porte des morts."),
    ]
    return p, (16, 19)


def chapel(p: Plan, slug: str, column: int, row: int, name: str):
    """Une chapelle : l'effigie enchaînée d'un Ungod devant son cadre, l'autel, deux braseros."""
    p.put("af-chapel-frame", column - 1, row - 1, (5, 1), layer="cadres", into_wall=True)
    for cell in [(column - 1 + dx, row - 1) for dx in range(5)]:
        p.blocked.add(cell)
        p.openings.add(cell)
    sculpture(p, "af-effigy-plinth", f"meshy-effigy-{slug}", column, row, (3, 3))
    p.put(f"af-effigy-chains-{slug}", column - 1, row, (5, 3), solid=False, layer="liens")
    p.blocked.update({(column - 1, row + 1), (column + 3, row + 1)})
    p.put("af-altar", column, row + 4, (2, 1))
    for cell in ((column - 1, row + 3), (column + 3, row + 3)):
        p.put("af-brazier", *cell)
    for cell in ((column - 2, row), (column + 4, row)):
        sculpture(p, "af-statue-niche-catacomb", "meshy-funerary-statue", *cell)
    p.pieces.append(("culte", "banner-cult", column - 2, row - 1))
    p.notes.append((column + 1, row + 1, f"Effigie enchaînée de {name}. Aucun symbole impérial."))


def catacombs() -> tuple[Plan, tuple[int, int]]:
    p = Plan("/catacombs", "catacomb", "af-cat-floor-", "af-catacomb-shell")
    # Quatre chapelles en croix autour du sanctuaire : nord et sud sur le petit axe, ouest et est
    # sur le grand. Chacune tourne le dos au nord, comme son cadre.
    p.vwall(11, 0, 9)
    p.vwall(19, 0, 9)
    p.hwall(9, 11, 19)
    p.arch(15, 9, "x")
    p.vwall(11, 14, 23)
    p.vwall(19, 14, 23)
    p.hwall(14, 11, 19)
    p.arch(11, 18, "y")
    p.arch(19, 18, "y")
    p.hwall(8, 0, 9)
    p.vwall(9, 8, 16)
    p.hwall(16, 0, 9)
    p.arch(9, 11, "y")
    p.hwall(8, 24, 33)
    p.vwall(24, 8, 16)
    p.hwall(16, 24, 33)
    p.arch(24, 11, "y")
    chapel(p, "cthraxis", 14, 3, "C'thraxis, la Dame des Péchés")
    chapel(p, "droggath", 4, 9, "Droggath, le Pondeur de chair")
    chapel(p, "krynnethoth", 27, 9, "Krynnethoth, le Mystique")
    chapel(p, "zulvath", 14, 15, "Z'ulvath, l'Aile d'Ombre")

    # L'escalier de la prison : il remonte au nord, sous la trémie du niveau −1.
    p.put("af-stair", 22, 4, (2, 3))
    p.free([(22, 6), (23, 6)])
    for cell in ((21, 7), (24, 7)):
        p.put("af-column", *cell)
    # Le sanctuaire du Culte, sous le centre du sable.
    p.put("af-vault-catacomb", 15, 10, (3, 3), solid=False, layer="voutes")
    p.blocked.update({(15, 10), (17, 10), (15, 12), (17, 12)})
    p.put("af-altar", 16, 13, (2, 1))
    for cell in ((12, 10), (12, 13), (21, 10), (21, 13)):
        p.put("af-column", *cell)
        p.pieces.append(("culte", "banner-cult", *cell))
    for cell in ((13, 11), (20, 12), (14, 13), (19, 10)):
        p.put("af-brazier", *cell)
    for cell in ((13, 13), (20, 10)):
        p.put("af-chest", *cell)
    # Les ossuaires, aux quatre coins de la croix.
    for column, row in ((5, 17), (25, 17), (28, 17), (6, 5), (25, 5)):
        sculpture(p, "af-ossuary-frame", "meshy-ossuary-insert", column, row, (2, 1))
    for cell in ((8, 18), (22, 19), (9, 6), (27, 7), (4, 19), (27, 19)):
        p.put("af-brazier", *cell)
    for cell in ((8, 4), (10, 20), (21, 20)):
        sculpture(p, "af-statue-niche-catacomb", "meshy-funerary-statue", *cell)
    for cell in ((5, 19), (23, 20), (26, 4)):
        p.put("af-chest", *cell)
    p.pieces.append(("voutes", "af-arch-catacomb-y", 10, 11))
    p.pieces.append(("voutes", "af-arch-catacomb-y", 23, 11))

    p.entity("spawnPoint", (22, 7), name="from-undercroft")
    p.entity("portal", (22, 6), targetMap=PLACE + "/undercroft", arrival="from-catacombs",
             sealed=False, requiresFlag="")
    p.notes.append((16, 11, "Sanctuaire central du Culte de l'Aile d'Ombre, sous le centre du sable."))
    p.notes.append((22, 7, "Pied de l'escalier de la prison : le seul accès aux catacombes."))
    return p, (22, 7)


def arena_fires() -> dict:
    """Les feux du pourtour de l'arène : un brasero entre deux statues voisines de la coursive.

    La carte du sable n'est pas redessinée ici : seule s'y ajoute la couche `feux`, à l'étage de
    la coursive. Les statues sont lues sur la carte ; les braseros se posent à mi-chemin, sur la
    même ellipse, hors de l'axe des deux portes et du portail.
    """
    level = json.loads((ROOT / "Source/Elements/Levels" / f"{PLACE}.json").read_text(encoding="utf-8"))
    statues = next(layer["tiles"] for layer in level["layers"] if layer["name"] == "divinites")

    def polar(tile):
        x = (tile["x"] + 0.5) * 1.5 - WIDTH * 0.75
        y = HEIGHT * 0.75 - (tile["y"] + 0.5) * 1.5
        return math.atan2(y / 11.1, x / 17.1), math.hypot(x / 17.1, y / 11.1)

    around = sorted(polar(tile) for tile in statues)
    taken = {(tile["x"], tile["y"]) for tile in statues}
    fires = []
    for (a0, r0), (a1, r1) in zip(around, around[1:] + [(around[0][0] + math.tau, around[0][1])]):
        angle, reach = (a0 + a1) / 2, (r0 + r1) / 2
        x, y = 17.1 * reach * math.cos(angle), 11.1 * reach * math.sin(angle)
        if abs(y) < 2.4 or (abs(x) < 4.5 and y < 0):
            continue  # la porte du triomphe, celle des morts, le portail monumental
        cell = (int((x + WIDTH * 0.75) // 1.5), int((HEIGHT * 0.75 - y) // 1.5))
        if cell not in taken:
            fires.append(list(cell))
    every = [[x, y] for y in range(HEIGHT) for x in range(WIDTH)]
    gestures = [
        {"tool": "layer", "name": "feux", "kind": "decor", "floor": 1},
        {"layer": "feux", "tool": "eraser", "path": every},
        {"layer": "feux", "tool": "paint", "piece": "af-pyre", "path": fires},
    ]
    # Les marqueurs de la série de l'arène : là où l'équilibrage a été mesuré (LOT-142). Le sable
    # est celui d'alors, une rangée plus bas ; un marqueur déplacé change le déploiement, donc les
    # victoires, et la bande du test de garde ne tient plus.
    for entity in level["entities"]:
        target = ARENA_ENCOUNTERS.get(entity.get("encounterId", ""))
        if target and [entity["x"], entity["y"]] != list(target):
            gestures.append({"tool": "entity", "kind": "", "at": [entity["x"], entity["y"]],
                             "to": list(target)})
    return {"format": "jadg-editor-gestures", "version": 1, "map": PLACE, "gestures": gestures}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--preview", action="store_true", help="imprimer le plan de chaque niveau")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    arguments = parser.parse_args()
    arguments.output.mkdir(parents=True, exist_ok=True)
    for build in (undercroft, catacombs):
        plan, entry = build()
        name = plan.map.rsplit("/", 1)[-1]
        if arguments.preview:
            print(plan.preview(entry))
        document = plan.gestures(entry)
        (arguments.output / f"{name}.json").write_text(
            json.dumps(document, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{name} : {len(plan.reachable(entry))} cases praticables, "
              f"{len(document['gestures'])} gestes")
    fires = arena_fires()
    (arguments.output / "arena-of-fate.json").write_text(
        json.dumps(fires, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"arena-of-fate : {len(fires['gestures'][2]['path'])} feux sur le pourtour, "
          f"{len(fires['gestures']) - 3} marqueur(s) de rencontre à replacer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
