#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Les vestiaires et la prison de l'Arena of Fate, aménagés (demande de l'auteur du 20 octobre
2026 : « les vestiaires et la prison sont trop simples, il faut un lieu beaucoup plus détaillé »).

Chaque salle du niveau des vestiaires (-6 m) mesure 24 x 18 m (`room_walls` de
`build_arena_fate_modern.py`) : murs intérieurs à ±11,45 m et ±8,45 m de son centre, colonnes à
(±8, ±7), porte de 3,6 m au milieu du mur qui donne sur le couloir (y = ±5). Ce module en dessine
l'aménagement fixe, en mètres de l'arène (x à l'est, y au sud, z depuis le sol de la salle) :

- **un vestiaire** (apodyterium d'un ludus) : au mur du fond, une paroi de niches (loculi) sur
  deux rangs, portes de bois entrouvertes, et le banc de marbre qui la longe ; au mur ouest,
  l'armurerie — panneau de bois, lances au râtelier, scuta, boucliers ronds, glaives aux
  chevilles ; à l'est, deux tables de massage de marbre et leurs étagères de fioles d'huile, de
  part et d'autre de la fontaine ; au fond, la fosse d'entraînement sablée, sa bordure et son
  poteau (palus) ; au mur du couloir, les chevilles des manteaux ; deux lampes de bronze
  suspendues ; une mosaïque devant la porte. Le second vestiaire est le même, de l'autre côté du
  couloir (`sign`).
- **la prison** : quatre cellules contre le mur ouest, cloisons de pierre, grilles de fer, portes
  ouvertes sauf celle de la cellule de l'enfant (y 13 → 16), paille et fers ; au nord, l'enclos
  grillagé des condamnés, son banc et ses anneaux ; près de la porte, le poste du garde et son
  tableau de clés ; à l'est, le pilori et le poteau de flagellation ; une grille d'écoulement au
  milieu ; des chaînes pendues aux voûtes.

Le passage de la porte au centre de la salle reste libre (x à ±1,5 m de l'axe de la porte,
jusqu'au centre), comme les colonnes et les appliques des murs (x à ±5 m de l'axe, à 1,9 m).
"""

from __future__ import annotations

import math

import arena_geometry as kit

# Les vestiaires : centre x, et y du centre selon le côté du couloir (-1 au nord, +1 au sud).
VESTIAIRE_X = -24.0
# La prison.
PRISON = (24.0, 14.0)
# Les cellules : fond contre le mur ouest, grilles à x = CELL_FRONT ; la cellule de l'enfant est
# la troisième (13 → 16), sa porte est fermée.
CELL_BACK = 12.3
CELL_FRONT = 14.4
CELLS = ((7.0, 10.0), (10.0, 13.0), (13.0, 16.0), (16.0, 19.0))
LOCKED_CELL = 2
# L'enclos des condamnés, au nord de la prison.
PEN = (18.6, 29.4, 19.6, 22.3)


def disc_x(x, y, z, radius, thick, material="bronze", sides=24):
    """Un disque vertical dont l'axe est x (un bouclier pendu à un mur ouest ou est)."""
    points = []
    for side in (-thick / 2, thick / 2):
        for j in range(sides):
            a = math.tau * j / sides
            points.append((x + side, y + radius * math.cos(a), z + radius * math.sin(a)))
    faces = [tuple(range(sides - 1, -1, -1)), tuple(range(sides, 2 * sides))]
    faces += [(j, (j + 1) % sides, (j + 1) % sides + sides, j + sides) for j in range(sides)]
    kit.solid(points, faces, material, bevel=0.004)


def bars(x0, y0, x1, y1, z0=0.0, z1=2.7, spacing=0.14, skip=None):
    """Une grille de fer entre (x0, y0) et (x1, y1) : barreaux ronds, trois plats, sans les
    barreaux de `skip` (l'ouverture d'une porte, en abscisses le long de la grille)."""
    length = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    count = int(length / spacing)
    for k in range(1, count):
        s = k * length / count
        if skip and skip[0] <= s <= skip[1]:
            continue
        x, y = x0 + ux * s, y0 + uy * s
        kit.rod((x, y, z0), (x, y, z1), radius=0.016, material="dark_metal", sides=8)
    for z in (z0 + 0.10, (z0 + z1) / 2, z1 - 0.04):
        for a, b in ([(0, skip[0]), (skip[1], length)] if skip else [(0, length)]):
            if b - a < 0.05:
                continue
            ca, cb = (a + b) / 2, b - a
            cx, cy = x0 + ux * ca, y0 + uy * ca
            if abs(ux) > abs(uy):
                kit.block(cx, cy, z, cb, 0.05, 0.05, "dark_metal")
            else:
                kit.block(cx, cy, z, 0.05, cb, 0.05, "dark_metal")


def shackle(x, y, z, wall_dx=0.0, wall_dy=0.0):
    """Un anneau scellé et sa chaîne, une menotte au bout (le mur est du côté (dx, dy))."""
    kit.turned(x + wall_dx * 0.04, y + wall_dy * 0.04, z, [(0.05, 0.0), (0.05, 0.03), (0.03, 0.03), (0.03, 0.0)],
               "dark_metal", sides=12)
    previous = (x, y, z)
    for k in range(1, 5):
        point = (x - wall_dx * 0.04 * k, y - wall_dy * 0.04 * k, z - 0.11 * k)
        kit.rod(previous, point, radius=0.012, material="dark_metal", sides=6)
        previous = point
    kit.turned(previous[0], previous[1], previous[2] - 0.07, [(0.055, 0.0), (0.055, 0.07), (0.04, 0.07), (0.04, 0.0)],
               "dark_metal", sides=12)


def bucket(x, y, z=0.0):
    kit.turned(x, y, z, [(0.0, 0.0), (0.16, 0.0), (0.19, 0.30), (0.17, 0.30), (0.14, 0.04), (0.0, 0.04)], "wood", sides=16)
    kit.turned(x, y, z + 0.08, [(0.172, 0.0), (0.172, 0.03), (0.165, 0.03), (0.165, 0.0)], "dark_metal", sides=16)


def straw(x, y, width, depth, seed=0.0):
    """Une litière de paille : une nappe basse et quelques bottes inégales."""
    kit.block(x, y, 0.0, width, depth, 0.035, "sand")
    for k in range(5):
        a = math.sin(seed * 12.9 + k * 7.3) * 0.5 + 0.5
        b = math.sin(seed * 4.1 + k * 3.7) * 0.5 + 0.5
        kit.block(x + (a - 0.5) * (width - 0.4), y + (b - 0.5) * (depth - 0.4), 0.03, 0.35 + 0.2 * a, 0.25 + 0.15 * b,
                  0.05 + 0.04 * b, "sand")


def hanging_lamp(x, y, top):
    """Une lampe de bronze à six becs pendue à la voûte."""
    hook = (x, y, 3.25)
    kit.rod((x, y, top), hook, radius=0.014, material="dark_metal", sides=6)
    for k in range(3):
        a = math.tau * k / 3
        kit.rod(hook, (x + 0.32 * math.cos(a), y + 0.32 * math.sin(a), 2.72), radius=0.008, material="dark_metal", sides=6)
    kit.turned(x, y, 2.62, [(0.0, 0.0), (0.30, 0.03), (0.38, 0.10), (0.0, 0.10)], "bronze", sides=24)
    for k in range(6):
        a = math.tau * k / 6
        kit.turned(x + 0.40 * math.cos(a), y + 0.40 * math.sin(a), 2.66,
                   [(0.0, 0.0), (0.06, 0.01), (0.07, 0.05), (0.02, 0.06), (0.0, 0.06)], "bronze", sides=10)


# --- Les vestiaires ------------------------------------------------------------------------


def vestiaire(sign):
    """L'aménagement d'un vestiaire, au nord (`sign` = -1) ou au sud (+1) du couloir."""

    def Y(d):
        # d : la distance au mur du couloir (y = ±5) ; le mur du fond est à d = 17,45.
        return sign * (5.0 + d)

    cx = VESTIAIRE_X
    west, east = cx - 11.45, cx + 11.45

    # Les loculi : deux rangs de niches au mur du fond, entre les deux appliques (x ±5).
    x0, x1 = cx - 3.9, cx + 3.9
    width = x1 - x0
    kit.block(cx, Y(17.15), 0.0, width, 0.6, 0.45, "stone_cream")
    kit.block(cx, Y(17.40), 0.45, width, 0.1, 1.56, "stone_cream")
    for z in (0.45, 1.20, 1.95):
        kit.block(cx, Y(17.12), z, width, 0.56, 0.06, "wood")
    kit.block(cx, Y(17.15), 2.01, width, 0.6, 0.36, "stone_cream")
    kit.block(cx, Y(17.08), 2.37, width + 0.3, 0.74, 0.12, "marble_white")
    niches = 11
    for k in range(niches + 1):
        x = x0 + width * k / niches
        kit.block(x, Y(17.12), 0.45, 0.06, 0.56, 1.56, "wood")
    for k in range(niches):
        xc = x0 + width * (k + 0.5) / niches
        for row, z in enumerate((0.51, 1.26)):
            if (k * 3 + row * 5) % 4 == 0:
                # Une porte entrouverte : le vantail pivote d'un quart vers la salle.
                hinge = xc - 0.31
                kit.solid(
                    [(hinge, Y(16.84), z), (hinge + 0.42, Y(16.84) - sign * 0.42, z),
                     (hinge + 0.42, Y(16.84) - sign * 0.42 + sign * 0.03, z), (hinge, Y(16.84) + sign * 0.03, z),
                     (hinge, Y(16.84), z + 0.66), (hinge + 0.42, Y(16.84) - sign * 0.42, z + 0.66),
                     (hinge + 0.42, Y(16.84) - sign * 0.42 + sign * 0.03, z + 0.66), (hinge, Y(16.84) + sign * 0.03, z + 0.66)],
                    [(0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)], "wood", bevel=0.004)
            elif (k + row) % 3 == 0:
                kit.block(xc, Y(16.84), z + 0.02, 0.6, 0.03, 0.66, "wood")
                kit.rod((xc + 0.2, Y(16.84) - sign * 0.015, z + 0.33), (xc + 0.2, Y(16.84) - sign * 0.06, z + 0.33),
                        radius=0.018, material="bronze", sides=8)
    # Le banc de marbre devant les niches, sur ses dés de pierre, quelques coussins.
    kit.block(cx, Y(16.45), 0.40, width, 0.5, 0.06, "marble_white")
    for k in range(6):
        kit.block(x0 + 0.3 + (width - 0.6) * k / 5, Y(16.45), 0.0, 0.3, 0.42, 0.40, "stone_cream")
    for k in (0, 2, 3, 5, 7, 8, 10):
        xc = x0 + width * (k + 0.5) / niches
        kit.block(xc, Y(16.45), 0.46, 0.58, 0.42, 0.07, "burgundy")

    # L'armurerie du mur ouest : socle, panneau, deux traverses, lances, scuta, boucliers, glaives.
    wx = west + 0.15
    kit.block(west + 0.2, Y(8.75), 0.0, 0.4, 11.5, 0.3, "stone_cream")
    kit.block(wx, Y(8.75), 0.3, 0.12, 11.5, 2.3, "wood")
    kit.block(wx + 0.02, Y(8.75), 2.6, 0.2, 11.7, 0.1, "wood")
    for z in (0.75, 2.05):
        kit.rod((wx + 0.18, Y(3.15), z), (wx + 0.18, Y(14.35), z), radius=0.03, material="wood", sides=10)
        for d in (3.15, 8.75, 14.35):
            kit.rod((wx + 0.06, Y(d), z), (wx + 0.2, Y(d), z), radius=0.03, material="bronze", sides=8)
    for k in range(10):
        d = 3.5 + 0.32 * k
        x, y = wx + 0.18, Y(d)
        kit.rod((x, y, 0.32), (x, y, 2.40), radius=0.02, material="wood", sides=8)
        kit.turned(x, y, 2.40, [(0.03, 0.0), (0.035, 0.05), (0.0, 0.24)], "dark_metal", sides=8)
    for d in (7.0, 8.0):
        y = Y(d)
        kit.block(wx + 0.12, y, 0.75, 0.06, 0.66, 1.05, "burgundy")
        kit.block(wx + 0.16, y, 0.75, 0.03, 0.70, 0.04, "bronze")
        kit.block(wx + 0.16, y, 1.76, 0.03, 0.70, 0.04, "bronze")
        disc_x(wx + 0.17, y, 1.27, 0.09, 0.05, "bronze", sides=16)
    for d in (9.6, 11.2, 12.8):
        y = Y(d)
        disc_x(wx + 0.11, y, 1.62, 0.44, 0.04, "wood")
        disc_x(wx + 0.14, y, 1.62, 0.44 - 0.03, 0.02, "bronze")
        disc_x(wx + 0.17, y, 1.62, 0.10, 0.06, "bronze", sides=16)
        # Un glaive à deux chevilles sous chaque bouclier : lame, garde, poignée.
        kit.block(wx + 0.16, y + 0.05, 0.98, 0.012, 0.52, 0.05, "dark_metal")
        kit.block(wx + 0.16, y - 0.24, 0.96, 0.03, 0.04, 0.09, "bronze")
        kit.rod((wx + 0.16, y - 0.26, 1.005), (wx + 0.16, y - 0.40, 1.005), radius=0.016, material="wood", sides=8)
        for dy in (-0.15, 0.2):
            kit.rod((wx + 0.06, y + dy, 0.95), (wx + 0.2, y + dy, 0.95), radius=0.012, material="bronze", sides=6)

    # L'est : tables de massage de part et d'autre de la fontaine (d = 9), étagères à fioles.
    for d in (5.0, 13.0):
        y = Y(d)
        kit.block(east - 1.85, y, 0.0, 0.55, 0.25, 0.76, "stone_cream")
        kit.block(east - 1.85, y + 0.75, 0.0, 0.55, 0.25, 0.76, "stone_cream")
        kit.block(east - 1.85, y - 0.75, 0.0, 0.55, 0.25, 0.76, "stone_cream")
        kit.block(east - 1.85, y, 0.76, 0.85, 2.1, 0.08, "marble_white")
        kit.block(east - 1.85, y + sign * 0.78, 0.84, 0.6, 0.35, 0.08, "burgundy")
        kit.block(east - 0.18, y, 1.52, 0.34, 2.2, 0.05, "wood")
        for dy in (-0.9, 0.9):
            kit.rod((east - 0.02, y + dy, 1.40), (east - 0.3, y + dy, 1.52), radius=0.015, material="dark_metal", sides=6)
        for k in range(6):
            fy = y - 0.85 + 0.34 * k
            kit.turned(east - 0.18, fy, 1.57, [(0.0, 0.0), (0.05, 0.0), (0.065, 0.06), (0.025, 0.15), (0.02, 0.21),
                                               (0.032, 0.23), (0.0, 0.23)], "stone_cream", sides=12)

    # La fosse d'entraînement au fond : bordure, sable, poteau cerclé de fer.
    px0, px1, pd0, pd1 = cx - 5.5, cx + 5.5, 10.6, 15.2
    kit.block(cx, Y((pd0 + pd1) / 2), 0.0, px1 - px0, pd1 - pd0, 0.06, "sand")
    for d in (pd0, pd1):
        kit.block(cx, Y(d), 0.0, px1 - px0 + 0.2, 0.2, 0.15, "stone_cream")
    for x in (px0, px1):
        kit.block(x, Y((pd0 + pd1) / 2), 0.0, 0.2, pd1 - pd0, 0.15, "stone_cream")
    post = (cx, Y(12.9))
    kit.turned(post[0], post[1], 0.06, [(0.14, 0.0), (0.13, 1.9), (0.0, 1.95)], "wood", sides=12)
    for z in (0.5, 1.2, 1.7):
        kit.turned(post[0], post[1], 0.06 + z, [(0.15, 0.0), (0.15, 0.05), (0.13, 0.05), (0.13, 0.0)], "dark_metal", sides=12)

    # Les chevilles des manteaux au mur du couloir, de part et d'autre de la porte.
    for k in range(20):
        x = west + 0.9 + 0.75 * k
        if abs(x - cx) < 2.6 or min(abs(x - (cx - 5)), abs(x - (cx + 5))) < 0.5:
            continue
        kit.rod((x, Y(0.55), 1.85), (x, Y(0.78), 1.88), radius=0.018, material="bronze", sides=8)
        if k % 3 != 1:
            kit.block(x, Y(0.70), 1.02, 0.42, 0.05, 0.84, "burgundy" if k % 2 else "mortar")

    # Deux lampes pendues à la voûte, sur l'axe de la salle (d = 9, sommet de la voûte à 4,7 m).
    for x in (cx - 5.0, cx + 5.0):
        hanging_lamp(x, Y(9.0), 4.6)

    # La mosaïque devant la porte : bordure à damier, champ clair, médaillon.
    mx0, mx1, md0, md1 = cx - 3.0, cx + 3.0, 2.6, 9.6
    kit.block(cx, Y((md0 + md1) / 2), 0.0, mx1 - mx0, md1 - md0, 0.012, "marble_white")
    step = 0.35
    for k in range(int((mx1 - mx0) / step)):
        x = mx0 + step * (k + 0.5)
        for d in (md0 + 0.25, md1 - 0.25):
            if k % 2 == 0:
                kit.block(x, Y(d), 0.0, step, 0.3, 0.016, "mortar")
    for k in range(int((md1 - md0) / step)):
        d = md0 + step * (k + 0.5)
        for x in (mx0 + 0.25, mx1 - 0.25):
            if k % 2 == 0:
                kit.block(x, Y(d), 0.0, 0.3, step, 0.016, "mortar")
    kit.turned(cx, Y((md0 + md1) / 2), 0.0, [(0.0, 0.0), (1.1, 0.0), (1.1, 0.016), (0.0, 0.016)], "mortar", sides=32)
    kit.turned(cx, Y((md0 + md1) / 2), 0.0, [(0.0, 0.0), (0.85, 0.0), (0.85, 0.02), (0.0, 0.02)], "burgundy", sides=32)


# --- La prison -----------------------------------------------------------------------------


def prison():
    """L'aménagement de la prison (centre (24, 14), porte au nord, sur le couloir, y = 5)."""
    cx, cy = PRISON
    east, near, far = cx + 11.45, cy - 8.45, cy + 8.45

    # Les cellules : cloisons, linteau, grilles, portes.
    depth = CELL_FRONT - CELL_BACK
    for y in sorted({c for cell in CELLS for c in cell}):
        kit.block((CELL_BACK + CELL_FRONT) / 2, y, 0.0, depth + 0.15, 0.25, 3.2, "stone_cream")
    for index, (y0, y1) in enumerate(CELLS):
        yc = (y0 + y1) / 2
        kit.block(CELL_FRONT, yc, 2.72, 0.3, y1 - y0 - 0.25, 0.48, "stone_cream")
        door = (0.35, 1.25)  # le long de la grille, depuis y0 + 0,125
        locked = index == LOCKED_CELL
        bars(CELL_FRONT, y0 + 0.125, CELL_FRONT, y1 - 0.125, skip=None if locked else door)
        if locked:
            # La porte fermée : gonds, serrure, cadenas.
            for z in (0.4, 2.2):
                kit.block(CELL_FRONT + 0.05, y0 + 0.125 + door[0], z, 0.06, 0.06, 0.14, "dark_metal")
            kit.block(CELL_FRONT + 0.05, y0 + 0.125 + door[1] - 0.08, 1.05, 0.08, 0.16, 0.22, "dark_metal")
            kit.turned(CELL_FRONT + 0.1, y0 + 0.125 + door[1] - 0.08, 0.92,
                       [(0.04, 0.0), (0.04, 0.09), (0.0, 0.1)], "bronze", sides=10)
        else:
            # La porte ouverte, rabattue dans la cellule le long de sa cloison.
            yy = y0 + 0.125 + door[0] - 0.04
            bars(CELL_FRONT - 0.05, yy, CELL_FRONT - 0.95, yy, z1=2.55)
        # La paille, les fers au mur du fond, un seau.
        straw(CELL_BACK + 0.65, yc + 0.55, 0.9, 1.5, seed=index)
        for dy in (-0.5, 0.5):
            shackle(CELL_BACK + 0.05, yc + dy, 1.55, wall_dx=-1.0)
        bucket(CELL_FRONT - 0.35, y1 - 0.45)

    # L'enclos des condamnés : grille, porte ouverte, banc, anneaux, paille.
    x0, x1, y0, y1 = PEN
    gate = ((x1 - x0) / 2 - 0.6, (x1 - x0) / 2 + 0.6)
    bars(x0, y0, x1, y0, skip=gate)
    bars(x0, y0, x0, y1)
    bars(x1, y0, x1, y1)
    kit.block((x0 + x1) / 2, y0, 2.70, x1 - x0, 0.2, 0.2, "wood")
    for x in (x0, x1):
        kit.block(x, (y0 + y1) / 2 + 0.05, 2.70, 0.2, y1 - y0 + 0.1, 0.2, "wood")
    gx = x0 + gate[0]
    bars(gx, y0 - 0.05, gx - 0.0, y0 - 1.15, z1=2.55)
    kit.block((x0 + x1) / 2, far - 0.3, 0.42, x1 - x0 - 1.0, 0.4, 0.06, "wood")
    for k in range(6):
        kit.block(x0 + 0.8 + (x1 - x0 - 1.6) * k / 5, far - 0.3, 0.0, 0.12, 0.36, 0.42, "wood")
    for k in range(7):
        shackle(x0 + 1.0 + (x1 - x0 - 2.0) * k / 6, far - 0.05, 1.1, wall_dy=1.0)
    straw(x0 + 2.0, (y0 + y1) / 2 - 0.2, 2.4, 1.4, seed=7)
    straw(x1 - 2.4, (y0 + y1) / 2 - 0.2, 2.0, 1.2, seed=9)
    bucket(x1 - 0.5, y0 + 0.5)

    # Le poste du garde, à l'ouest de la porte : tableau de clés au mur du couloir.
    bx, bz = cx - 4.3, 1.45
    kit.block(bx, near + 0.04, bz, 1.4, 0.05, 0.55, "wood")
    for k in range(6):
        x = bx - 0.55 + 0.22 * k
        kit.rod((x, near + 0.06, bz + 0.42), (x, near + 0.16, bz + 0.42), radius=0.012, material="bronze", sides=6)
        if k % 2 == 0:
            kit.turned(x, near + 0.15, bz + 0.24, [(0.035, 0.0), (0.035, 0.14), (0.02, 0.14), (0.02, 0.0)],
                       "dark_metal", sides=10)
            kit.rod((x, near + 0.15, bz + 0.24), (x, near + 0.15, bz + 0.02), radius=0.01, material="dark_metal", sides=6)

    # Le pilori et le poteau de flagellation, côté est.
    sx, sy = east - 2.4, cy - 1.0
    kit.block(sx, sy, 0.0, 0.5, 2.3, 0.12, "wood")
    for dy in (-0.95, 0.95):
        kit.block(sx, sy + dy, 0.12, 0.16, 0.16, 1.15, "wood")
    for z in (0.62, 0.86):
        kit.block(sx, sy, z, 0.12, 2.06, 0.2, "wood")
    for dy in (-0.55, 0.0, 0.55):
        kit.turned(sx, sy + dy, 0.79, [(0.07, 0.0), (0.07, 0.03), (0.0, 0.03)], "mortar", sides=12)
    wx, wy = cx + 6.5, cy + 2.0
    kit.turned(wx, wy, 0.0, [(0.16, 0.0), (0.14, 2.2), (0.0, 2.26)], "wood", sides=10)
    kit.turned(wx, wy, 1.9, [(0.17, 0.0), (0.17, 0.05), (0.15, 0.05), (0.15, 0.0)], "dark_metal", sides=10)
    shackle(wx + 0.16, wy, 1.85, wall_dx=-1.0)

    # La grille d'écoulement au milieu, des chaînes pendues aux voûtes.
    kit.block(cx, cy - 0.5, 0.0, 0.32, 8.0, 0.012, "dark_metal")
    for k in range(20):
        kit.block(cx, cy - 4.3 + 0.4 * k, 0.012, 0.32, 0.04, 0.004, "mortar")
    for x, y in ((cx - 4.0, cy + 1.0), (cx + 3.0, cy - 3.0), (cx + 4.5, cy + 3.5)):
        previous = (x, y, 4.4)
        for k in range(1, 12):
            point = (x + 0.02 * math.sin(k), y, 4.4 - 0.15 * k)
            kit.rod(previous, point, radius=0.015, material="dark_metal", sides=6)
            previous = point
        kit.turned(x, y, previous[2] - 0.12, [(0.08, 0.0), (0.08, 0.12), (0.06, 0.12), (0.06, 0.0)], "dark_metal", sides=10)
