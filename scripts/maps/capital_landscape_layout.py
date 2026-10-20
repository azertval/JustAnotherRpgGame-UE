#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""La géographie de la capitale impériale, relevée sur le plan d'ensemble : le texte du paysage.

Aucun import du moteur ni de numpy : le générateur (`capital_landscape.py`), le script de scène
(`build_capital_landscape_scene.py`) et les tests lisent ce même relevé.

**Le repère du relevé** est celui du plan d'ensemble de la capitale, ramené à une grille de
2000 × 1412 unités : u vers la droite, v vers le bas. C'est la convention des quartiers déjà écrits
(`arenarea_district_layout.py`, `martpart_district_layout.py`) : x de la carte = droite du plan,
y = bas du plan — une convention de scène, pas la rose des vents du plan (qui met l'ouest en haut).

**L'échelle** se prend sur le seul monument déjà mesuré : l'Arena of Fate, 189 m de grand axe,
150 unités sur le plan — 1,26 m par unité. Son centre est l'origine de la carte, son seuil le
niveau zéro, comme dans Arenarea. Les quartiers écrits resserrent le plan autour de leurs lieux
(le Natural Pool d'Arenarea est à 0,6 fois sa distance du plan) : ils ne se superposent pas à ce
paysage, qui est la vue d'ensemble.

Ce relevé est une lecture du plan, à ± 15 unités : rives, enceinte, quartiers, bois. Les hauteurs
sont une proposition (la source ne cote rien). Révision autorisée le 13 octobre :
éperons urbains et terrasses côtières expressives ; eau calme au niveau de la baie.
"""

from __future__ import annotations

METRES_PER_UNIT = 1.26
ARENA = (1083.0, 337.0)          # le centre de l'Arena of Fate sur le plan : l'origine de la carte
PLAN = (2000.0, 1412.0)
# Le terrain déborde le plan : les collines derrière Oldtown, le large, les bois. En unités du plan.
AREA_UNITS = (-200.0, -140.0, 2200.0, 1460.0)
RESOLUTION = 2.0                 # mètres par quad : 1512 × 1008 quads, 24 × 16 composants de 63
SEA_LEVEL = -2.5                 # mètres sous le seuil de l'arène : la baie, la rivière, le ruisseau
# Le bord du terrain descend sous l'eau sur cette marge (mètres), jusqu'au sol lointain : la carte
# n'a pas de tranche ouverte.
EDGE = {"margin": 36.0, "floor": -15.5}
SEED = 20261012


def metres(point: tuple[float, float]) -> tuple[float, float]:
    """Un point du relevé, dans la carte (x droite du plan, y bas du plan, en mètres)."""
    return ((point[0] - ARENA[0]) * METRES_PER_UNIT, (point[1] - ARENA[1]) * METRES_PER_UNIT)


def area_metres() -> list[float]:
    (x0, y0), (x1, y1) = metres(AREA_UNITS[:2]), metres(AREA_UNITS[2:])
    return [x0, y0, x1, y1]


# --- L'eau --------------------------------------------------------------------------------------
# Tourmaline Bay, la Rubicund River et South Creek : un seul contour, la rive nord d'ouest en est,
# la rive sud de la rivière d'est en ouest, la côte de la ville, puis le ruisseau.
WATER = [
    (-260, 100), (100, 104), (190, 112),
    # la presqu'île du tigre sentinelle
    (215, 135), (200, 160), (175, 178), (165, 200), (175, 225), (170, 250), (185, 270), (200, 290),
    (215, 310), (240, 325), (275, 340), (300, 350), (330, 345), (348, 325), (350, 300), (365, 280),
    (380, 260), (400, 245), (415, 232), (418, 215), (400, 200), (410, 185), (440, 170), (480, 155),
    (520, 142), (545, 132),
    # la rive nord de la baie, puis de la rivière, vers l'amont
    (600, 126), (650, 125), (700, 130), (750, 138), (800, 150), (850, 160), (900, 175), (940, 190),
    (1000, 210), (1100, 220), (1200, 235), (1300, 262), (1350, 300), (1400, 320), (1500, 395),
    (1600, 460), (1700, 510), (1800, 555), (1900, 585), (2000, 595), (2260, 600),
    # la rive sud de la rivière, vers l'aval
    (2260, 652), (2000, 645), (1900, 630), (1800, 600), (1700, 555), (1600, 505), (1500, 440),
    (1400, 385), (1350, 350), (1300, 320), (1200, 280), (1100, 260), (1000, 250), (955, 247),
    # la pointe sableuse à l'ouest de l'arène, Water Gate, les quais
    (930, 255), (905, 280), (898, 320), (900, 360), (885, 385), (850, 393), (800, 385), (750, 372),
    (700, 372), (655, 385), (610, 402), (560, 410), (500, 400), (450, 395), (405, 390),
    # la côte de Palacedomain, vers le sud
    (400, 430), (410, 455), (405, 480), (430, 500), (455, 525), (460, 545), (445, 570), (425, 590),
    (410, 610), (400, 640), (385, 670), (375, 700), (372, 720), (355, 735), (350, 760), (360, 790),
    (345, 810), (335, 835), (300, 850),
    # Grove of Hope, sa pointe, l'embouchure
    (262, 828), (235, 857), (200, 872), (165, 887), (135, 902), (128, 927), (150, 962), (138, 997),
    # South Creek : rive est vers l'amont, puis rive ouest vers l'aval
    (165, 1012), (175, 1042), (210, 1072), (228, 1092), (265, 1117), (262, 1150), (258, 1200),
    (252, 1250), (250, 1300), (262, 1350), (290, 1385), (292, 1520),
    (228, 1520), (225, 1392), (222, 1350), (220, 1300), (222, 1250), (220, 1200), (215, 1150),
    (206, 1117), (200, 1092), (175, 1070), (146, 1042), (138, 1020), (120, 992), (95, 962),
    (60, 940), (30, 912), (-260, 905),
]
# Terres prolongees hors cadre autour de Cyan Fortress (insularite non attestee), et ilot des quais.
ISLANDS = [
    [(-260, 372), (50, 368), (100, 366), (140, 372), (185, 378), (205, 395), (215, 420), (225, 440),
     (240, 460), (246, 490), (240, 515), (215, 535), (190, 545), (180, 560), (195, 580), (215, 600),
     (222, 625), (205, 650), (185, 668), (178, 690), (188, 712), (190, 730), (175, 748), (140, 757),
     (110, 752), (80, 735), (40, 715), (-260, 700)],
    [(797, 300), (815, 290), (840, 293), (852, 308), (848, 325), (832, 338), (815, 335), (800, 322)],
]
# Le Natural Pool d'Arenarea : une eau calme dans les murs, au niveau de la baie.
POOLS = [
    [(858, 402), (880, 410), (905, 425), (935, 438), (965, 447), (968, 458), (950, 465), (920, 460),
     (890, 448), (868, 432), (855, 415)],
]

# --- Les murs et les quartiers ------------------------------------------------------------------
# L'enceinte extérieure, organique : de Water Gate par Arena Gate, Market Gate, Wildlife Gate,
# Bauron Gate, Tamera Gate, puis la côte de Palacedomain.
CITY_WALL = [
    (850, 400), (905, 330), (950, 285), (1000, 262), (1080, 258), (1150, 270), (1200, 290),
    (1262, 318), (1300, 345), (1345, 372), (1390, 395), (1440, 430), (1448, 462), (1418, 500),
    (1405, 625), (1405, 640), (1480, 655), (1560, 672), (1605, 712), (1710, 770), (1760, 830),
    (1800, 905), (1835, 985), (1860, 1080), (1885, 1180), (1890, 1228), (1850, 1205), (1800, 1180),
    (1752, 1090), (1740, 1120), (1700, 1160), (1685, 1172), (1640, 1160), (1560, 1150),
    (1575, 1250), (1590, 1315), (1500, 1290), (1380, 1265), (1368, 1248), (1335, 1190),
    (1300, 1255), (1250, 1320), (1195, 1325), (1130, 1245), (1085, 1250), (1010, 1280),
    (980, 1340), (960, 1300), (880, 1240), (840, 1300), (700, 1305), (580, 1315), (525, 1345),
    (450, 1307), (450, 1152), (525, 1140), (500, 1100), (505, 1000), (512, 950), (410, 817),
    (395, 787), (425, 700), (450, 625), (480, 550), (500, 510), (562, 462), (650, 452), (780, 445),
]
# Le seul mur intérieur : celui du palais.
PALACE_WALL = [
    (545, 520), (640, 500), (745, 512), (782, 560), (778, 640), (745, 725), (690, 775), (605, 790),
    (552, 740), (530, 660), (528, 580),
]
# Le bâti hors les murs.
OLDTOWN = [
    (1000, 212), (985, 185), (1040, 150), (1150, 135), (1335, 118), (1345, 105), (1440, 105),
    (1450, 170), (1500, 195), (1560, 215), (1640, 255), (1690, 290), (1700, 330), (1705, 400),
    (1720, 450), (1715, 500), (1700, 508), (1600, 458), (1500, 393), (1400, 318), (1350, 298),
    (1300, 260), (1200, 233), (1100, 218),
]
SLOGHOOD = [
    (300, 860), (400, 790), (410, 817), (512, 950), (505, 1000), (500, 1100), (525, 1140),
    (450, 1152), (450, 1290), (380, 1290), (350, 1250), (300, 1180), (280, 1120), (270, 1000),
    (280, 900),
]
BOOMBURBS = [
    (300, 1290), (450, 1307), (525, 1345), (580, 1315), (700, 1305), (840, 1300), (880, 1240),
    (960, 1300), (980, 1340), (1010, 1280), (1085, 1250), (1130, 1245), (1195, 1325), (1250, 1320),
    (1300, 1255), (1335, 1190), (1368, 1248), (1340, 1330), (1300, 1520), (300, 1520),
]
NECKOFFOODS_VILLAGE = [
    (1368, 1248), (1380, 1265), (1500, 1290), (1590, 1315), (1575, 1250), (1560, 1150),
    (1640, 1160), (1685, 1172), (1700, 1160), (1740, 1120), (1752, 1090), (1800, 1180),
    (1890, 1228), (1870, 1290), (1800, 1300), (1700, 1330), (1600, 1335), (1400, 1345),
    (1340, 1330),
]
HALFLING_BARROWS = [
    (1448, 462), (1500, 440), (1600, 505), (1700, 555), (1760, 590), (1700, 700), (1605, 712),
    (1560, 672), (1480, 655), (1405, 640), (1405, 625), (1418, 500),
]
DOCKS = [(610, 402), (655, 385), (700, 372), (750, 372), (800, 385), (850, 393), (850, 400),
         (780, 445), (650, 452), (600, 440)]
# Les verts dans les murs : jardins, champ d'exercice.
GREENS = [
    [(790, 830), (850, 790), (920, 800), (930, 830), (905, 870), (870, 880), (820, 870)],  # Tyreen's Verdant
    [(580, 865), (730, 865), (730, 945), (580, 945)],                                       # Duke Wicar's War School
]
# Les cultures de Neckoffoods : parcelles en rangs.
FIELDS = [
    [(1340, 1345), (1600, 1335), (1800, 1300), (1900, 1260), (1990, 1300), (2260, 1300),
     (2260, 1520), (1300, 1520)],
]
# Les bois : où le couvert domine (ailleurs, hors du bâti, la prairie).
FORESTS = [
    [(-260, 55), (700, 65), (1000, 90), (1335, 100), (1335, 118), (1150, 135), (1040, 150),
     (985, 185), (1000, 212), (940, 190), (800, 150), (650, 125), (545, 132), (190, 112), (-260, 100)],  # Yorehoi Forest
    [(190, 112), (545, 132), (410, 185), (418, 215), (350, 300), (330, 345), (275, 340), (215, 310),
     (170, 250), (165, 200), (215, 135)],                                                   # la presqu'île du tigre
    ISLANDS[0],
    [(405, 390), (560, 410), (562, 462), (500, 510), (450, 625), (425, 700), (395, 787), (350, 760),
     (385, 670), (410, 610), (460, 545), (405, 480)],                                       # la côte boisée de Palacedomain
    [(262, 828), (300, 850), (345, 810), (400, 790), (300, 860), (280, 900), (270, 1000),
     (280, 1120), (265, 1117), (228, 1092), (175, 1042), (138, 997), (150, 962), (128, 927),
     (135, 902), (200, 872)],                                                               # Grove of Hope
    [(-260, 905), (30, 912), (95, 962), (138, 1020), (200, 1092), (215, 1150), (222, 1350),
     (228, 1520), (-260, 1520)],                                                            # les bois de l'ouest
    [(262, 1150), (300, 1180), (350, 1250), (380, 1290), (300, 1290), (300, 1520), (292, 1520),
     (290, 1385), (250, 1300), (258, 1200)],                                                # la rive du ruisseau
    [(1700, 330), (1760, 320), (1790, 380), (2260, 330), (2260, 600), (1900, 585), (1800, 555),
     (1715, 500), (1705, 400)],                                                             # les bois sous Stone Fortress
    [(1760, 590), (1800, 600), (1900, 630), (2260, 652), (2260, 1300), (1990, 1300), (1900, 1260),
     (1890, 1228), (1860, 1080), (1835, 985), (1800, 905), (1760, 830), (1710, 770), (1700, 700)],  # The Northwoods
    [(1262, 318), (1300, 320), (1400, 385), (1500, 440), (1448, 462), (1440, 430), (1345, 372)],  # la rive d'Arenarea
]
# Les jardins du palais : un couvert d'arbres plus clair que les bois.
GARDENS = [PALACE_WALL]

# --- Le relief ----------------------------------------------------------------------------------
# Une butte : centre et rayon (unités du plan), hauteur au sommet et largeur de la pente (mètres
# et unités). `terraces` découpe la pente en paliers de cette hauteur.
HILLS = [
    # Les collines de la ville : chaque quartier a sa hauteur, les maquettes la montrent.
    # Elongated landforms: interlocking ridges, not a hill centred on every monument.
    {"id": "palais", "centre": (630, 645), "radius": 46, "axes": (1.0,1.55), "height": 57.0, "falloff": 175},
    {"id": "cote-du-palais", "centre": (485, 620), "radius": 25, "axes": (.65,1.65), "height": 35.0, "falloff": 100},
    {"id": "downtown", "centre": (1170, 760), "radius": 35, "axes": (.9,1.45), "height": 47.0, "falloff": 190},
    {"id": "dweomer", "centre": (1550, 1030), "radius": 35, "axes": (1.65,.8), "height": 57.0, "falloff": 190},
    {"id": "scholarnest", "centre": (1200, 1140), "radius": 35, "axes": (.85,1.35), "height": 42.0, "falloff": 160},
    {"id": "uptown", "centre": (665, 1090), "radius": 35, "axes": (1.35,.85), "height": 30.0, "falloff": 175},
    {"id": "artisansquare", "centre": (930, 1080), "radius": 30, "axes": (.8,1.5), "height": 33.0, "falloff": 135},
    {"id": "martpart", "centre": (1570, 820), "radius": 30, "axes": (1.15,.75), "height": 28.0, "falloff": 150},
    {"id": "arenarea", "centre": (1160, 570), "radius": 30, "axes": (1.8,.7), "height": 32.0, "falloff": 160},
    {"id": "oldtown", "centre": (1300, 158), "radius": 35, "axes": (2.5,.7), "height": 32.0, "falloff": 130},
    {"id": "sloghood", "centre": (380, 1010), "radius": 25, "axes": (.6,1.7), "height": 17.0, "falloff": 130},
    {"id": "boomburbs", "centre": (800, 1400), "radius": 70, "axes": (2.0,.6), "height": 9.0, "falloff": 150},
    {"id": "neckoffoods", "centre": (1700, 1420), "radius": 90, "axes": (2.0,.7), "height": 7.0, "falloff": 210},
    # Les hauts hors la ville.
    {"id": "stone-fortress", "centre": (1850, 262), "radius": 70, "height": 60.0, "falloff": 170},
    {"id": "hauts-de-l-est", "centre": (2000, 130), "radius": 180, "height": 45.0, "falloff": 260},
    {"id": "northwoods", "centre": (2010, 1000), "radius": 140, "height": 50.0, "falloff": 260},
    {"id": "bois-de-l-ouest", "centre": (40, 1260), "radius": 110, "height": 40.0, "falloff": 220},
    {"id": "tigre-sentinelle", "centre": (300, 228), "radius": 40, "height": 18.0, "falloff": 95},
    {"id": "cyan-fortress", "centre": (105, 545), "radius": 60, "height": 22.0, "falloff": 120},
]
# La chaîne derrière la baie et Oldtown : le terrain monte au nord de cette ligne (v), sur cette
# profondeur (unités), jusqu'à cette hauteur (mètres).
RIDGE = {"line": 95.0, "depth": 230.0, "height": 125.0}
# La ville monte de la rive vers l'intérieur des terres.
INLAND_RISE = 10.0
# Les vallons : les grandes avenues courent au creux des collines. Profondeur (m), largeur (unités).
VALLEYS = [
    {"id": "shield-avenue", "depth": 14.0, "width": 70, "points": [(1000, 470), (985, 560), (1080, 640), (1120, 700), (1160, 880), (1180, 950), (1220, 1000), (1280, 1110), (1335, 1190)]},
    {"id": "stravian-avenue", "depth": 10.0, "width": 60, "points": [(1575, 675), (1540, 760), (1470, 870), (1400, 950), (1340, 1000)]},
    {"id": "knights-avenue", "depth": 10.0, "width": 60, "points": [(512, 950), (650, 945), (790, 920), (905, 880), (1000, 935), (1160, 950)]},
]
# Dans les murs, les pentes se tiennent en terrasses : cette part de la pente se met en paliers de
# cette hauteur (les murs de soutènement des maquettes).
CITY_TERRACES = {"step": 4.0, "share": 0.5}
# Le froissement des collines : de combien (unités du plan) et à quelle maille (sommets) leur
# contour s'écarte du cercle.
HILL_WARP = {"units": 34.0, "cell": 60}
# Le relief propre aux quartiers, pour que la ville ne soit pas une suite de buttes lisses :
#  - `swell` : une houle du sol sous le bâti, par amplitude (m) et maille (sommets) ;
#  - `knolls` : des mamelons semés au hasard sur la terre ferme (nombre, rayon en unités, hauteur
#    en mètres ; un sur quatre est un creux) ;
#  - `terraceShare` : la part de pente mise en terrasses varie d'un îlot à l'autre entre ces bornes.
DISTRICT_RELIEF = {
    "swell": [(1.5, 70), (0.45, 28), (0.08, 11)],
    "knolls": {"count": 24, "radius": (45, 110), "height": (1.0, 4.0), "falloff": 2.2},
    "terraceShare": (0.0, 0.08),
}
# Les crêtes de la chaîne : un bruit à arêtes, de cette amplitude relative.
RIDGE_CRESTS = 0.45
# Le plus bas de la terre ferme avant sa plage (mètres) : le niveau des quais.
QUAY_LEVEL = 1.2
# Les terre-pleins : une ellipse (centre, demi-axes) ou un contour mis à plat, à une hauteur donnée
# ou à celle du terrain en son centre (`None`), sur une marge de raccord (unités).
PADS = [
    {"id": "arena-of-fate", "centre": ARENA, "radii": (100, 84), "z": 0.0, "blend": 20},
    {"id": "hippodrome", "centre": (1277, 527), "radii": (44, 52), "z": None, "blend": 30},
    {"id": "illu-die-arena", "centre": (1425, 808), "radii": (46, 46), "z": None, "blend": 28},
    {"id": "braves-arena", "centre": (1385, 1352), "radii": (26, 26), "z": None, "blend": 22},
    {"id": "war-school", "centre": (655, 905), "radii": (80, 44), "z": None, "blend": 26},
    {"id": "cathedrale", "centre": (1215, 775), "radii": (40, 44), "z": None, "blend": 26},
    {"id": "quais", "centre": (725, 412), "radii": (110, 30), "z": 1.0, "blend": 22},
]

# --- Les voies ----------------------------------------------------------------------------------
# Largeur en mètres ; peintes dans la couche du sable graveleux.
ROADS = [
    {"id": "herofate-avenue", "width": 14, "points": [(850, 400), (836, 449), (866, 484), (985, 482), (1060, 440), (1150, 430), (1240, 372), (1275, 327)]},
    {"id": "shield-avenue", "width": 14, "points": [(1000, 470), (985, 560), (1080, 640), (1120, 700), (1160, 880), (1180, 950), (1220, 1000), (1280, 1110), (1335, 1190)]},
    {"id": "knights-avenue", "width": 12, "points": [(512, 950), (650, 945), (790, 920), (905, 880), (1000, 935), (1160, 950), (1180, 950)]},
    {"id": "knights-avenue-uptown", "width": 12, "points": [(790, 920), (720, 1010), (660, 1090), (560, 1125), (525, 1140)]},
    {"id": "oath-avenue", "width": 10, "points": [(545, 1125), (552, 1200), (590, 1235), (590, 1290), (580, 1315)]},
    {"id": "stravian-avenue", "width": 12, "points": [(1575, 675), (1540, 760), (1470, 870), (1400, 950), (1340, 1000), (1320, 1060), (1335, 1190)]},
    {"id": "imperial-avenue", "width": 12, "points": [(562, 462), (650, 452), (780, 445), (850, 400)]},
    {"id": "autumn-avenue", "width": 9, "points": [(782, 560), (800, 640), (760, 740), (690, 790), (600, 805), (512, 950)]},
    {"id": "saint-malrok", "width": 9, "points": [(1160, 880), (1250, 870), (1340, 900), (1400, 950)]},
    {"id": "dweomer-view", "width": 9, "points": [(1400, 950), (1500, 960), (1580, 900), (1590, 800), (1600, 715)]},
    {"id": "grain-road", "width": 8, "points": [(410, 817), (512, 950), (505, 1000), (500, 1100), (460, 1150), (440, 1310), (525, 1360), (580, 1330), (840, 1315), (880, 1258), (975, 1355), (1012, 1295), (1128, 1260), (1195, 1340), (1255, 1335), (1335, 1210), (1375, 1280), (1500, 1305), (1600, 1330), (1585, 1250), (1572, 1165), (1690, 1187), (1752, 1108), (1800, 1195), (1900, 1240), (1900, 1180), (1875, 1080), (1850, 985), (1815, 905), (1775, 830), (1720, 765), (1640, 715)]},
    {"id": "hudlodge-route", "width": 7, "points": [(120, 1118), (206, 1117), (265, 1117), (282, 1117), (330, 1170), (380, 1250), (450, 1250)]},
    {"id": "old-path", "width": 6, "points": [(1345, 266), (1280, 250), (1180, 200), (1090, 180), (1020, 190)]},
    {"id": "arching-path", "width": 7, "points": [(1345, 266), (1350, 250), (1380, 190), (1400, 150)]},
    {"id": "smithheim-way", "width": 6, "points": [(1350, 250), (1450, 280), (1560, 300), (1660, 380), (1705, 400)]},
    {"id": "fortway", "width": 6, "points": [(1705, 400), (1730, 340), (1780, 325), (1850, 290)]},
    {"id": "old-bridge-road", "width": 8, "points": [(1575, 675), (1640, 600), (1688, 575), (1725, 495), (1716, 470)]},
    {"id": "northwoods-track", "width": 5, "points": [(1890, 1228), (1960, 1190), (2060, 1180), (2260, 1150)]},
]
# Les ponts : la chaussée passe au-dessus de l'eau, le terrain ne s'y relève pas. Ce sont des
# ouvrages à poser (X07, X08, X09, X10), cités ici pour leurs culées.
BRIDGES = {
    "arching-bridge": [(1288, 318), (1345, 266)],
    "old-bridge": [(1688, 575), (1725, 495)],
    "aqueduct": [(1890, 640), (1925, 575)],
    "eastern-bridge": [(206, 1117), (265, 1117)],
}

# --- Les couches de matière ---------------------------------------------------------------------
# Les cinq matières de `M_SenseiTerrain`, de la plus basse à la plus haute : la matière les empile
# (A, puis B par-dessus, puis C…), chacune par son canal — A n'en a pas, elle est le fond.
# `id` est la couche que le générateur peint ; `channel`, le canal de la matière du pack.
LAYERS = [
    {"id": "herbe", "slot": "A", "channel": None, "colour": "#6f8b3a",
     "textures": {"Albedo Color": "/Game/Surfaces/MossyGrass/T_MossyGrass_01_BC",
                  "Normal": "/Game/Surfaces/MossyGrass/T_MossyGrass_01_N",
                  "Roughness": "/Game/Surfaces/MossyGrass/T_MossyGrass_01_Roughness"}},
    {"id": "roche", "slot": "B", "channel": "Material B", "colour": "#8d8576",
     "textures": {"Albedo Color": "/Game/Surfaces/RockVkmfaek/T_vkmfaek_1K_B",
                  "Normal": "/Game/Surfaces/RockVkmfaek/T_vkmfaek_1K_N",
                  "MaskORM": "/Game/Surfaces/RockVkmfaek/T_vkmfaek_1K_ORM",
                  "Height": "/Game/Surfaces/RockVkmfaek/T_vkmfaek_1K_H"}},
    {"id": "sous-bois", "slot": "C", "channel": "Material C", "colour": "#3f5a2c",
     "textures": {"Albedo Color": "/Game/Surfaces/ForestGround/T_ForestGround_A",
                  "Normal": "/Game/Surfaces/ForestGround/T_ForestGround_N",
                  "Roughness": "/Game/Surfaces/ForestGround/T_ForestGround_R"}},
    {"id": "terre", "slot": "D", "channel": "Material D", "colour": "#7b6a4c",
     "textures": {"Albedo Color": "/Game/Capitale/Ressources/Surfaces/T_soil_0_BC",
                  "Normal": "/Game/Capitale/Ressources/Surfaces/T_soil_0_N",
                  "MaskORM": "/Game/Capitale/Ressources/Surfaces/T_soil_0_ORM",
                  "Height": "/Game/Capitale/Ressources/Surfaces/T_soil_0_H"}},
    {"id": "sable", "slot": "E", "channel": "Material E", "colour": "#cdbd96",
     "textures": {"Albedo Color": "/Game/Surfaces/GravellySand/gravelly_sand_diff_1k",
                  "Normal": "/Game/Surfaces/GravellySand/gravelly_sand_nor_dx_1k",
                  "MaskORM": "/Game/Surfaces/GravellySand/gravelly_sand_arm_1k",
                  "Height": "/Game/Surfaces/GravellySand/gravelly_sand_disp_1k"}},
]

# --- La matière du terrain ----------------------------------------------------------------------
# `M_SenseiTerrain` est écrite pour le Mesh Terrain : ses canaux se lisent par des nœuds que le
# `Landscape` n'a pas. Le script en fait une copie portée (`ported`), où chaque lecture de canal
# devient une couche de paysage du même nom ; le reste du graphe du pack ne change pas. Le terrain
# porte une instance de cette copie. Ses paramètres, par leur nom dans la matière : des réglages
# d'essai, à juger sur captures — pas des valeurs du standard.
MATERIAL = {
    "source": "/Game/Bibliotheque/Materiaux/SenseiTerrain/Materials/M_SenseiTerrain",
    "functions": "/Game/Bibliotheque/Materiaux/SenseiTerrain/MaterialFunctions",
    "ported": "/Game/Capitale/Ressources/M_SenseiTerrain_Landscape",
    "switches": {
        "2nd Material Layer B?": True, "3rd Material Layer C?": True, "4th Material Layer D?": True,
        "5th Material Layer E?": True,
        # La roche vient aussi d'elle-même sur les pentes, et se projette sur trois plans.
        "Use Auto Blend? B": True, "Triplanar? B": True,
        "Variation Color?": True, "Variation Normal?": True,
    },
    # Par matière : `<nom> <A–E>`.
    "layerSwitches": {
        "Distance Blend?": {"A": True, "B": True, "C": True, "D": True, "E": True},
        "Cell Bombing?": {"A": True, "C": True, "D": True},
        "Far Distance Cellbomb?": {"A": True, "C": True, "D": True},
        "Use Mask?": {"B": True, "D": True, "E": True},
        "Use AO?": {"B": True, "D": True, "E": True},
    },
    "layerScalars": {
        "Size": {"A": 0.5, "B": 0.5, "C": 0.5, "D": 0.5, "E": 0.5},
        "Size Far": {"A": 0.12, "B": 0.15, "C": 0.12, "D": 0.12, "E": 0.2},
        "StartOffset": {"A": 2500.0, "B": 3000.0, "C": 2500.0, "D": 2500.0, "E": 2500.0},
        "Blend Falloff": {"A": 6000.0, "B": 6000.0, "C": 6000.0, "D": 6000.0, "E": 6000.0},
        "Normal Strength": {"A": 0.55, "B": 0.65, "C": 0.55, "D": 0.5, "E": 0.55},
        "Displacement Amount": {"A": 0.0, "B": 0.0, "C": 0.0, "D": 0.0, "E": 0.0},
        "Height Blend Strength": {"B": 1.2, "D": 1.0, "E": 1.0},
    },
    "layerVectors": {
        # La palette du jeu : herbe soignée, calcaire clair, sous-bois, terre, sable pâle.
        "Albedo Tint": {"A": [0.92, 1.0, 0.78, 1.0], "B": [1.0, 0.98, 0.92, 1.0], "C": [1.0, 1.1, 0.8, 1.0],
                        "D": [0.78, 0.74, 0.66, 1.0], "E": [1.0, 0.96, 0.86, 1.0]},
    },
    "scalars": {"Angle Contrast B": 3.0, "Fall Off Amount B": 2.5,
                "Color Variation Amount": 0.4, "MacroVariationAmount": 0.45, "MacroVariationSize": 1.0,
                "Normal Variation Strength": 0.15, "Variation Start": 3000.0, "Variation Falloff": 9000.0,
                "Distance Variation Size": 0.004},
    # Le déplacement ne se rend que sur un terrain Nanite ; `None` garde l'amplitude de la matière.
    # Collision remains the 2m heightfield. Displacement is evaluated separately
    # in the material witness, never silently enabled across player routes.
    "displacementMagnitude": 2.0,
}

# --- L'eau --------------------------------------------------------------------------------------
# Une eau à une couche (Single Layer Water) : absorption et diffusion par centimètre, turquoise
# sur les hauts-fonds, sombre au large.
WATER_MATERIAL = {
    "absorption": [0.0065, 0.0016, 0.0012],
    "scattering": [0.0001, 0.0006, 0.0006],
    "roughness": 0.06,
    "waveMetres": [9.0, 23.0],          # la période des deux trains de vagues
    "waveSpeed": [0.012, -0.007],
    "waveStrength": 1.0,
}

# --- Les cadrages -------------------------------------------------------------------------------
# Cible en unités du plan ; cap de boussole de la carte (0 = haut du plan), plongée et distance (m).
SHOTS = [
    {"id": "ensemble", "target": (1000, 700), "heading": 0, "pitch": 50, "distance": 2000},
    {"id": "baie", "target": (620, 300), "heading": 300, "pitch": 24, "distance": 700},
    {"id": "riviere", "target": (1330, 310), "heading": 60, "pitch": 26, "distance": 520},
    {"id": "palais", "target": (655, 640), "heading": 270, "pitch": 28, "distance": 620},
    {"id": "cultures", "target": (1650, 1380), "heading": 20, "pitch": 24, "distance": 420},
    {"id": "ruisseau", "target": (240, 1117), "heading": 330, "pitch": 26, "distance": 380},
    {"id": "panorama", "target": (1000, 760), "heading": 335, "pitch": 18, "distance": 1500},
    {"id": "collines", "target": (1190, 790), "heading": 300, "pitch": 14, "distance": 520},
    {"id": "seuil-arene", "target": (1083, 420), "heading": 0, "pitch": 20, "distance": 60},
]
# Le groupe : sur le terre-plein de l'arène, face à son seuil.
ENTRY_UNITS = (1083, 420)

# Same terrain system, extended with surveyed urban access and explicit platforms.
import capital_city_layout as city  # noqa: E402
ROADS.extend(city.EXTRA_ROADS)
PADS = [pad for pad in PADS if pad['id'] in ('arena-of-fate','quais')]
for identifier, (u,v,z,_facade,_roof,total) in city.LANDMARKS.items():
    if z is None or identifier in ('L07-01','L07-06') or identifier.startswith('X') or total == 0:
        continue
    radii = (48,44) if identifier in ('L12-01','L11-01') else (23,22)
    if identifier == 'L12-01': radii = (36,62)
    if identifier == 'L04-01': radii = (36,46)
    if identifier == 'L07-03': radii = (46,80)
    PADS.append({'id':identifier,'centre':(u,v),'radii':radii,'z':z,'blend':12})
SHOTS.extend([
 {'id':'proche-arching','target':(1267,339),'heightOffset':1.5,'heading':35,'pitch':35,'distance':60},
 {'id':'proche-oldtown','target':(1570,305),'heightOffset':5,'heading':0,'pitch':38,'distance':65},
 {'id':'proche-market','target':(1585,654),'heightOffset':1.5,'heading':35,'pitch':40,'distance':50},
 {'id':'proche-palais','target':(656,693),'heightOffset':1.5,'heading':0,'pitch':32,'distance':95},
 {'id':'proche-terrasses','target':(598,718),'heightOffset':1.5,'heading':300,'pitch':40,'distance':100},
 {'id':'proche-universite','target':(1175,1158),'heightOffset':5,'heading':0,'pitch':42,'distance':55},
 {'id':'proche-dweomer','target':(1448,1054),'heightOffset':1.5,'heading':25,'pitch':35,'distance':90},
 {'id':'market-gate-old-bridge','target':(1630,603),'heading':25,'pitch':28,'distance':410},
 {'id':'scholarnest-dweomer','target':(1360,1080),'heading':330,'pitch':26,'distance':680},
 {'id':'sloghood-uptown','target':(520,1110),'heading':315,'pitch':28,'distance':520},
 {'id':'bloomburgs-rempart','target':(800,1325),'heading':10,'pitch':22,'distance':390},
 {'id':'joueur-water-gate','target':(850,414),'heading':45,'pitch':35,'distance':45},
 {'id':'joueur-market-gate','target':(1575,675),'heading':45,'pitch':40,'distance':38},
 {'id':'joueur-universite','target':(1175,1136),'heightOffset':8,'heading':180,'pitch':35,'distance':55},
])
