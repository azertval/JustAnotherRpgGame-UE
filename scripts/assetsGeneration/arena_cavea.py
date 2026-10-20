# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""La cavea de l'Arena of Fate, sur le modele du Colisee (reprise du 19 octobre 2026).

Le referentiel (`Planning/referentiels/central-empire/capitale.md`) et la planche validee
(`Documentation/SourceBook/references-capitale/output/arena-of-fate-planche-v1.png`) demandent :
le sable en contrebas d'un podium droit de deux cases (3 m), plaque de marbre et couronne d'une
balustrade ; la coursive des dieux sur le podium, statues et braseros alternes ; deux portes
face a face sur le grand axe ; des gradins continus tout autour. Le Colisee donne la coupe :

- maenianum primum (ima cavea) : dix rangs de 1,5 m, du podium (3 m) a la premiere
  praecinctio (12 m) ;
- maenianum secundum (media cavea) : un balteus de 2,6 m perce de vomitoires, puis dix rangs
  jusqu'a la seconde praecinctio (24 m) ;
- summa cavea : un balteus perce de vomitoires, cinq rangs plus raides, puis le haut mur et
  le portique couvert (porticus in summa cavea) sous la terrasse ;
- les escaliers du public sont dans la masse et dans les deambulatoires, jamais dans l'arene :
  sous les gradins passent les deambulatoires du rez-de-chaussee (r > 85) et de l'etage (r > 87).

Les treize loges des delegations s'encastrent dans la media cavea, au-dessus de la premiere
praecinctio ; la loge imperiale est sur le grand axe, au-dessus de la porte de l'est.

Toutes les positions sont en metres, X est, Y sud, Z haut ; un anneau de parametre `a` a pour
demi-axes (a, a - 16), comme le reste de l'arene. Geometrie seule : l'appelant exporte et pose.
"""

from __future__ import annotations

import math

import arena_geometry as kit
import arena_sculpted_geometry as sculpt

OFFSET = 16.0
PODIUM = 3.0
SAND = 43.0
COURSE = 49.0
# Passages couverts sous le podium et les gradins : portes du grand axe (|y| < 7,3) et du petit
# axe (|x| < 5,3), jusqu'au deambulatoire du rez-de-chaussee.
EW_BAND = 7.3
NS_BAND = 5.3
GROUND_AMBULATORY = 84.6
UPPER_AMBULATORY = 87.0
WALL = 87.4  # le haut mur de la summa cavea (87,0 a 87,8), de 24 a 35,7 m
PORTICUS = 87.9
LOGE_RADIUS = 68.6
# L'encoche de la loge dans la media cavea : 1 m de chaque cote et 1,6 m derriere, au niveau du
# plancher de la loge, jusqu'a son entree reservee a l'arriere (0,6 m ne laissait pas passer). Son
# bord avant mord de 0,55 m sur la praecinctio (deja a 12 m) : sur les axes, ou l'ovale tourne le
# plus, le balteus courbe passait devant un bord droit et fermait les passages lateraux.
LOGE_RECT = (-5.0, 5.0, -3.15, 4.2)
LOGE_SECTORS = (0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14)
VELUM_SECTORS = (1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15)
SEGMENTS = 8
AISLE = 0.0225
EDGE = 0.022
# Les circulations cachees : vomitoires de 2,4 m sous plafond, escaliers de 2,6 m d'echappee,
# marches de 15 x 30 cm ; une cage d'escalier par diagonale de l'ovale.
CLEAR = 2.4
HEAD = 2.6
RISE, RUN = 0.15, 0.30
CORE_SECTORS = (2, 6, 10, 14)


def xy(a, t):
    return (a * math.cos(t), (a - OFFSET) * math.sin(t))


def normal_yaw(a, t):
    """Lacet d'une piece dont la face locale -Y regarde l'arene (convention des arcades)."""
    return 90 - math.degrees(math.atan2(math.sin(t) / (a - OFFSET), math.cos(t) / a))


def rows():
    """Les rangs de la cavea, du podium au haut mur : rayon interieur, giron, dessus."""
    result = []
    for k in range(10):
        result.append({"a": COURSE + 1.5 * k, "tread": 1.5, "top": PODIUM + 0.9 * (k + 1), "kind": "seat", "first": False})
    result.append({"a": 64.0, "tread": 2.0, "top": 12.0, "kind": "walk", "first": False})
    for k in range(10):
        result.append({"a": 66.0 + 1.5 * k, "tread": 1.5, "top": 13.6 + 1.04 * (k + 1), "kind": "seat", "first": k == 0})
    result.append({"a": 81.0, "tread": 2.0, "top": 24.0, "kind": "walk", "first": False})
    for k in range(5):
        result.append({"a": 83.0 + 0.8 * k, "tread": 0.8, "top": 26.0 + 0.6 * (k + 1), "kind": "seat", "first": k == 0})
    previous = PODIUM
    for row in result:
        row["previous"] = previous
        previous = row["top"]
        # Sous les rangs qui couvrent un deambulatoire, la masse s'arrete a son plafond.
        row["bottom"] = 12.0 if row["a"] + row["tread"] > GROUND_AMBULATORY + 1e-6 else 0.0
    return result




# --- Polygones -----------------------------------------------------------------------------


def _clean(poly):
    out = []
    for p in poly:
        if not out or math.dist(p, out[-1]) > 1e-6:
            out.append(p)
    if len(out) > 2 and math.dist(out[0], out[-1]) < 1e-6:
        out.pop()
    if len(out) < 3:
        return None
    area = sum(out[i][0] * out[(i + 1) % len(out)][1] - out[(i + 1) % len(out)][0] * out[i][1] for i in range(len(out)))
    return out if abs(area) > 1e-5 else None


def clip(poly, a, b, c):
    """La part du polygone convexe ou a*x + b*y <= c (Sutherland-Hodgman)."""
    if poly is None:
        return None
    out = []
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if fp <= 0:
            out.append(p)
        if fp * fq < 0:
            t = fp / (fp - fq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return _clean(out)


def centroid(poly):
    return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))


def loge_frames():
    """Le repere de chaque loge : centre (x, y, z), lacet, et ses demi-plans dans le monde."""
    frames = []
    for sector in LOGE_SECTORS:
        t = math.tau * sector / 16
        x, y = xy(LOGE_RADIUS, t)
        # Face au balteus : la normale de l'ovale, pas l'angle polaire (de biais hors des axes,
        # l'encoche laissait des eclats de mur dans ses passages lateraux).
        yaw = normal_yaw(LOGE_RADIUS, t)
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        x0, x1, y0, y1 = LOGE_RECT
        # local x = c*dX - s*dY ; local y = s*dX + c*dY
        planes = [
            (c, -s, x1 + c * x - s * y),
            (-c, s, -x0 - c * x + s * y),
            (s, c, y1 + s * x + c * y),
            (-s, -c, -y0 - s * x - c * y),
        ]
        frames.append({"sector": sector, "angle": t, "position": [x, y, 12.0], "yaw": yaw, "planes": planes})
    return frames


LOGES = loge_frames()


def split(poly, bands=True, loges=True):
    """Decoupe exacte d'une cellule : [(polygone, dans un passage, dans une loge)]."""
    pieces = [(poly, False)]
    if bands:
        cut = []
        for piece, _ in pieces:
            for lo, hi in ((None, -EW_BAND), (-EW_BAND, EW_BAND), (EW_BAND, None)):
                part = piece
                if lo is not None:
                    part = clip(part, 0, -1, -lo)
                if hi is not None:
                    part = clip(part, 0, 1, hi)
                if part:
                    cx, cy = centroid(part)
                    cut.append((part, lo is not None and hi is not None and abs(cx) > 30))
        pieces, cut = cut, []
        for piece, inside in pieces:
            if inside:
                cut.append((piece, True))
                continue
            for lo, hi in ((None, -NS_BAND), (-NS_BAND, NS_BAND), (NS_BAND, None)):
                part = piece
                if lo is not None:
                    part = clip(part, -1, 0, -lo)
                if hi is not None:
                    part = clip(part, 1, 0, hi)
                if part:
                    cx, cy = centroid(part)
                    cut.append((part, lo is not None and hi is not None and abs(cy) > 20))
        pieces = cut
    result = []
    for piece, band in pieces:
        if not loges:
            result.append((piece, band, False))
            continue
        hit = None
        for frame in LOGES:
            inside = piece
            for plane in frame["planes"]:
                inside = clip(inside, *plane)
            if inside:
                hit = frame
                break
        if hit is None:
            result.append((piece, band, False))
            continue
        result.append((inside, band, True))
        rest = piece
        for a, b, c in hit["planes"]:
            outside = clip(rest, -a, -b, -c)
            if outside:
                result.append((outside, band, False))
            rest = clip(rest, a, b, c)
            if rest is None:
                break
    return result


# --- Circulations cachees : vomitoires et cages d'escalier ----------------------------------
#
# Un vide (« carve ») retire de la masse, entre deux rayons de rang a0..a1 et deux angles
# t0..t1, la tranche floor..floor + head. Les angles bornent par des droites (l'anneau de
# parametre a a des rayons droits), les rayons tombent sur les limites des rangs : la decoupe
# des cellules reste exacte. Sous un vide pose au sol, une dalle tient lieu de plancher.


def speed(a, t):
    """La longueur d'arc par radian de parametre sur l'anneau a."""
    return math.hypot(a * math.sin(t), (a - OFFSET) * math.cos(t))


def advance(a, t, length, direction=1):
    """L'angle atteint en parcourant `length` metres sur l'anneau a depuis t."""
    steps = max(8, int(length / 0.05))
    for _ in range(steps):
        t += direction * length / steps / speed(a, t)
    return t


def b1_angles():
    """Les vomitoires du premier balteus (r 66) : deux par secteur, hors des loges."""
    result = []
    for i in range(16):
        for q in (-0.25, 0.25):
            t = math.tau * (i + q) / 16
            if not any(inloge for _, _, inloge in split(quad(65.8, 66.4, t - 0.012, t + 0.012), bands=False)):
                result.append(t % math.tau)
    return result


def b2_angles():
    """Les vomitoires du second balteus (r 83), au milieu d'une travee du haut mur : ils
    traversent la summa cavea et le mur jusqu'au deambulatoire de 24 m."""
    return [math.tau * ((5 * j + q) % 80) / 80 for j in range(16) for q in (-1.5, 1.5)]


def _carve(a0, a1, t0, t1, floor, head, kind):
    return {"a0": a0, "a1": a1, "t0": min(t0, t1), "t1": max(t0, t1), "floor": floor, "head": head, "kind": kind}


def _flight(a0, a1, start, direction, count, floor0, kind):
    """Une volee : `count` marches de 30 cm sur l'anneau median, montant de 15 cm chacune."""
    mid, t, result = (a0 + a1) / 2, start, []
    for k in range(count):
        nxt = advance(mid, t, RUN, direction)
        result.append(_carve(a0, a1, t, nxt, floor0 + RISE * (k + 1), HEAD, kind))
        t = nxt
    return result, t


def cores():
    """Les quatre cages d'escalier, sur les diagonales. Chacune a :

    - un escalier en U du sol a 12 m : volee A le long du deambulatoire du sol (rangs 83-84,6,
      ouverte sur lui, garde-corps), palier a 6 m, volee B interieure (praecinctio 81-83) qui
      revient jusqu'au vomitoire T1 du premier balteus ;
    - une volee droite de 12 a 24 m (rangs 84,6-87) qui longe le deambulatoire de 12 m et
      arrive au vomitoire Tb2 du second balteus, au droit d'une porte du haut mur."""
    found = b1_angles()
    result = []
    for sector in CORE_SECTORS:
        t1 = min(found, key=lambda t: abs(((t - math.tau * (sector + 0.25) / 16 + math.pi) % math.tau) - math.pi))
        d1 = 0.75 / speed(66.0, t1)
        start_a = advance(83.8, t1 + d1, 0.8)
        # Un palier de depart au niveau du sol : la premiere marche, collee au mur de bout, ne
        # raccordait pas le deambulatoire (rayon de l'agent, 35 cm de marche au plus).
        foot = advance(83.8, start_a, 1.5)
        approach = _carve(83.0, GROUND_AMBULATORY, start_a, foot, 0.0, HEAD, "palier-bas")
        flight_a, end_a = _flight(83.0, GROUND_AMBULATORY, foot, 1, 40, 0.0, "volee-a")
        landing_end = advance(82.8, end_a, 2.2)
        landing = _carve(81.0, GROUND_AMBULATORY, end_a, landing_end, 6.0, HEAD, "palier")
        flight_b, end_b = _flight(81.0, 83.0, end_a, -1, 40, 6.0, "volee-b")
        top_b = _carve(81.0, 83.0, t1, end_b, 12.0, HEAD, "palier-haut")
        tb2 = math.tau * (5 * (sector + 1) + 1.5) / 80
        d2 = 0.75 / speed(83.0, tb2)
        start_c = advance(85.8, tb2 - d2 * 0.5, RUN * 80, -1)
        flight_c, end_c = _flight(GROUND_AMBULATORY, UPPER_AMBULATORY, start_c, 1, 80, 12.0, "volee-c")
        # Son palier de depart, de plain-pied avec le deambulatoire de 12 m (comme la volee A).
        approach_c = _carve(GROUND_AMBULATORY, UPPER_AMBULATORY, advance(85.8, start_c, 1.5, -1), start_c, 12.0, HEAD,
                            "palier-bas")
        result.append({"sector": sector, "t1": t1, "tb2": tb2, "start_a": start_a, "end_a": end_a,
                       "landing_end": landing_end, "end_b": end_b, "start_c": start_c, "end_c": end_c,
                       "carves": [approach] + flight_a + [landing] + flight_b + [top_b] + [approach_c] + flight_c,
                       "flight_a": flight_a, "flight_c": flight_c})
    return result


def _all_carves():
    result = []
    for t in b1_angles():
        d = 0.75 / speed(66.0, t)
        result.append(_carve(66.0, UPPER_AMBULATORY, t - d, t + d, 12.0, CLEAR, "vomitoire"))
    for t in b2_angles():
        d = 0.75 / speed(83.0, t)
        result.append(_carve(83.0, UPPER_AMBULATORY, t - d, t + d, 24.0, CLEAR, "vomitoire"))
    for core in cores():
        result += core["carves"]
    return result


_CARVES = []


def carves():
    if not _CARVES:
        _CARVES.extend(_all_carves())
    return _CARVES


def _near(t, ref):
    """L'angle t ramene a moins d'un demi-tour de ref."""
    return ref + ((t - ref + math.pi) % math.tau) - math.pi


def _at_least(t):
    """Le demi-plan des angles >= t (le rayon droit de l'anneau a l'angle t)."""
    return (math.sin(t), -math.cos(t), OFFSET * math.sin(t) * math.cos(t))


def _at_most(t):
    a, b, c = _at_least(t)
    return (-a, -b, -c)


def voided(poly, a0, a1, lo, hi):
    """Les tranches angulaires d'un morceau de cellule (rang a0..a1, angles lo..hi) et les
    vides qui les traversent : [(polygone, [(floor, head)])]."""
    mid = (lo + hi) / 2
    hits = []
    for c in carves():
        if c["a0"] > a0 + 1e-6 or a1 > c["a1"] + 1e-6:
            continue
        t0, t1 = _near(c["t0"], mid), _near(c["t0"], mid) + (c["t1"] - c["t0"])
        if t1 <= lo or t0 >= hi:
            continue
        hits.append((t0, t1, c))
    if not hits:
        return [(poly, [])]
    cuts = sorted({t for t0, t1, _ in hits for t in (t0, t1) if lo < t < hi})
    bounds = [lo] + cuts + [hi]
    result = []
    for s, e in zip(bounds, bounds[1:]):
        piece = poly
        if s > lo:
            piece = clip(piece, *_at_least(s))
        if e < hi:
            piece = clip(piece, *_at_most(e))
        if piece is None:
            continue
        m = (s + e) / 2
        result.append((piece, [(c["floor"], c["head"]) for t0, t1, c in hits if t0 <= m <= t1]))
    return result


def kept(low, high, voids):
    """Les tranches de [low, high] que les vides laissent, et la dalle sous un vide au sol."""
    spans = [(low, high)]
    for floor, head in voids:
        z0, z1 = floor, floor + head
        spans = [part for a, b in spans for part in ((a, min(b, z0)), (max(a, z1), b)) if part[1] - part[0] > 0.012]
    if any(floor <= 0.01 and low <= 0.01 for floor, _ in voids):
        spans.append((-0.3, 0.0))
    return sorted(spans)


def prism(poly, bottom, top, material="stone_cream", bevel=0.0):
    """Un prisme droit, sans biseau par defaut : la cavea compte des dizaines de milliers de
    pierres, et leurs biseaux saturaient le streaming Nanite (colonnes de la facade degradees)."""
    if poly is None or top - bottom < 0.012:
        return
    n = len(poly)
    points = [(x, y, bottom) for x, y in poly] + [(x, y, top) for x, y in poly]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    faces += [(j, (j + 1) % n, (j + 1) % n + n, j + n) for j in range(n)]
    kit.solid(points, faces, material, bevel=bevel)


def quad(a0, a1, lo, hi):
    return [xy(a0, lo), xy(a1, lo), xy(a1, hi), xy(a0, hi)]


# --- Cavea ---------------------------------------------------------------------------------


def _layers(row, a0, a1, lo, hi, top, bottom, seat=True):
    """La masse et ses couvertures d'un morceau de rang, decoupes par passages, loges et vides."""
    for whole, band, loge in split(quad(a0, a1, lo, hi)):
        low = max(bottom, PODIUM) if band else bottom
        high = min(top, 12.0) if loge else top
        cap = 0.14 if (row["kind"] == "walk" or loge or not seat) else 0.16
        for poly, voids in voided(whole, a0, a1, lo, hi):
            for z0, z1 in kept(low, high, voids):
                if z1 < high - 1e-6:
                    prism(poly, z0, z1)
                    continue
                prism(poly, z0, max(z0, high - cap))
                prism(poly, max(z0, high - cap), high, "marble_white", 0.006)
        if seat and not loge and row["kind"] == "seat":
            tread = a1 - a0
            for b0, b1, z0, z1, material in (
                (a0 + 0.52 * tread, a0 + 0.953 * tread, high, high + 0.10, "burgundy"),
                (a0 + 0.52 * tread, a0 + 0.547 * tread, high + 0.10, high + 0.12, "bronze"),
            ):
                inner = quad(b0, b1, lo + 0.006, hi - 0.006)
                for piece, _, inloge in split(inner, bands=False):
                    if not inloge:
                        prism(piece, z0, z1, material)


def _mouth(a, lo, hi):
    """Vrai si un vomitoire s'ouvre dans la contremarche du rang a, entre les angles lo et hi."""
    mid = (lo + hi) / 2
    for c in carves():
        if c["kind"] != "vomitoire" or abs(c["a0"] - a) > 0.01:
            continue
        t0 = _near(c["t0"], mid)
        if t0 < hi and t0 + (c["t1"] - c["t0"]) > lo:
            return True
    return False


def sector(index):
    """Un secteur de gradins (1/16 de l'ovale), du podium au haut mur."""
    centre, half = math.tau * index / 16, math.pi / 16
    lo, hi = centre - half + EDGE, centre + half - EDGE
    for row in rows():
        for j in range(SEGMENTS):
            a, b = lo + (hi - lo) * j / SEGMENTS, lo + (hi - lo) * (j + 1) / SEGMENTS
            _layers(row, row["a"], row["a"] + row["tread"], a, b, row["top"], row["bottom"])
            rise = row["top"] - row["previous"]
            if row["kind"] != "seat" or rise < 0.3:
                continue
            # Le parement de la contremarche : marbre au balteus, pierre ailleurs.
            material = "marble_white" if row["first"] else "stone_cream"
            for k in range(2):
                c, d = a + (b - a) * k / 2 + 0.0012, a + (b - a) * (k + 1) / 2 - 0.0012
                face = quad(row["a"] - 0.03, row["a"] + 0.06, c, d)
                if any(inloge for _, _, inloge in split(face, bands=False)) or _mouth(row["a"], c, d):
                    continue
                prism(face, row["previous"] + 0.04, row["top"] - 0.18, material, 0.004)
            if row["first"]:
                # La moulure qui couronne le balteus.
                prism(quad(row["a"] - 0.09, row["a"] + 0.10, a, b), row["top"] - 0.30, row["top"] - 0.16, "marble_white", 0.01)


def scalaria(index):
    """L'escalier rayonnant entre deux secteurs : il monte d'une praecinctio a la suivante et
    s'arrete au balteus, comme au Colisee (on change de maenianum par les vomitoires)."""
    angle = math.tau * (index + 0.5) / 16
    lo, hi = angle - AISLE, angle + AISLE
    for row in rows():
        if row["kind"] == "walk" or row["first"]:
            _layers(row, row["a"], row["a"] + row["tread"], lo, hi, row["top"], row["bottom"], seat=False)
            continue
        rise = row["top"] - row["previous"]
        count = max(2, round(rise / 0.2))
        for k in range(count):
            a0 = row["a"] + row["tread"] * k / count
            a1 = row["a"] + row["tread"] * (k + 1) / count
            _layers(row, a0, a1, lo, hi, row["previous"] + rise * (k + 1) / count, row["bottom"], seat=False)


# --- Podium --------------------------------------------------------------------------------


def podium():
    """Le mur du podium (3 m) plaque de marbre, et sa masse sous la coursive. Ouvert sur le
    grand axe pour les deux portes ; ferme sur le petit axe (l'escalier du sud passe dessous)."""
    count = 192
    for i in range(count):
        lo, hi = math.tau * i / count, math.tau * (i + 1) / count
        for poly, band, _ in split(quad(SAND + 0.35, COURSE, lo, hi), loges=False):
            ew = band and abs(centroid(poly)[0]) > 30
            if not ew:
                prism(poly, 0, PODIUM - 0.3)
        mid = (lo + hi) / 2
        x, y = xy(SAND, mid)
        if abs(x) > 30 and abs(y) < 2.55:
            continue  # l'ouverture de la porte
        prism(quad(SAND - 0.08, SAND + 0.40, lo, hi), 0, 0.28, "stone_cream", 0.01)
        prism(quad(SAND, SAND + 0.40, lo + 0.0006, hi - 0.0006), 0.28, 2.42, "marble_white", 0.008)
        prism(quad(SAND - 0.10, SAND + 0.40, lo, hi), 2.42, PODIUM - 0.3, "marble_white", 0.01)
        if i % 4 == 0:
            # Pilastres reguliers du parement.
            prism(quad(SAND - 0.06, SAND + 0.02, lo, lo + 0.006), 0.28, 2.42, "marble_white", 0.006)


def podium_gate():
    """La porte du grand axe (est), herse levee : a poser aussi en lacet 180 pour l'ouest."""
    for side in (-1, 1):
        y = side * 2.86
        kit.block(SAND + 0.32, y, 0, 0.86, 0.62, 0.20, "marble_white")
        for row in range(5):
            kit.dressed_block(SAND + 0.32, y, 0.20 + row * 0.44, 0.78, 0.56, 0.43)
        kit.block(SAND + 0.30, y, 2.40, 0.92, 0.66, 0.12, "marble_white")
    kit.block(SAND + 0.30, 0, 2.52, 0.96, 6.40, 0.18, "marble_white")
    kit.block(SAND - 0.02, 0, 2.30, 0.30, 0.70, 0.40, "marble_white")
    # La herse levee : ses pointes depassent sous le linteau, a 2,06 m du sol (le groupe, 1,96 m,
    # passe dessous ; a 1,94 m, il s'y heurtait, 20 octobre 2026).
    for k in range(21):
        y = -2.4 + k * 0.24
        kit.rod((SAND + 0.36, y, 2.14), (SAND + 0.36, y, 2.66), 0.022, "dark_metal", 12)
        kit.rod((SAND + 0.36, y, 2.06), (SAND + 0.36, y, 2.14), 0.012, "dark_metal", 8)
    for z in (2.22, 2.54):
        kit.rod((SAND + 0.36, -2.46, z), (SAND + 0.36, 2.46, z), 0.03, "dark_metal", 12)
    # Les rainures de la herse dans les piedroits.
    for side in (-1, 1):
        kit.block(SAND + 0.36, side * 2.5, 0, 0.14, 0.10, 2.52, "dark_metal")


def tunnel_floors():
    """Le sol des passages du petit axe, de part et d'autre de la descente du sud."""
    for sign in (-1, 1):
        y0, y1 = sorted((sign * 33.0, sign * 38.0))
        if sign > 0:
            for x0, x1 in ((-NS_BAND, -1.9), (1.9, NS_BAND)):
                sculpt.paving(x0, x1, y0, y1, 0)
            for x in (-1.9, 1.9):
                kit.rail(x, (y0 + y1) / 2, 0, y1 - y0, axis="y")
        else:
            sculpt.paving(-NS_BAND, NS_BAND, y0, y1, 0)


def vomitorium(spring=1.45, clear=CLEAR):
    """Une bouche de vomitoire, face -Y vers l'arene, sur le passage creuse derriere elle :
    piedroits, arc et ecoincons de marbre jusqu'au plafond du passage (`clear`)."""
    width, radius = 1.3, 0.65
    for side in (-1, 1):
        kit.block(side * (width / 2 + 0.13), -0.10, 0, 0.26, 0.20, spring, "marble_white")
    kit.arc(0, -0.10, spring, ri=radius, thick=0.20, depth=0.20, segments=17)
    # Les ecoincons ferment, entre l'arc et le plafond du passage, ce que l'arc laisse ouvert.
    for k in range(16):
        a0, a1 = math.pi * k / 16, math.pi * (k + 1) / 16
        x0, x1 = radius * math.cos(a0), radius * math.cos(a1)
        z0, z1 = spring + radius * math.sin(a0), spring + radius * math.sin(a1)
        kit.prism([(x0, z0), (x1, z1), (x1, clear + 0.04), (x0, clear + 0.04)], -0.06, 0.0)
    kit.block(0, -0.10, 0, width + 0.52, 0.22, 0.02, "marble_white")


def vomitoria_positions():
    """Les bouches : premier balteus (r 66, 12 m) et second (r 83, 24 m)."""
    result = []
    for a, z, angles in ((66.0, 12.0, b1_angles()), (83.0, 24.0, b2_angles())):
        for t in angles:
            x, y = xy(a, t)
            result.append({"position": [x, y, z], "yaw": normal_yaw(a, t), "spring": 1.45})
    return result


def door_bays():
    """Les travees du haut mur percees d'une porte : celles des vomitoires du second balteus."""
    return {round(t / math.tau * 80 - 0.5) % 80 for t in b2_angles()}


def stair_dressing():
    """Les garde-corps des volees ouvertes sur un deambulatoire et le mur d'echiffre entre les
    deux volees de l'escalier en U (coordonnees de la carte, a poser a l'origine)."""
    for core in cores():
        for k, step in enumerate(core["flight_a"]):
            if k >= 4:
                prism(quad(GROUND_AMBULATORY - 0.15, GROUND_AMBULATORY, step["t0"], step["t1"]),
                      step["floor"], step["floor"] + 1.05, "marble_white", 0.004)
        prism(quad(GROUND_AMBULATORY - 0.15, GROUND_AMBULATORY, core["end_a"], core["landing_end"]), 6.0, 7.05,
              "marble_white", 0.004)
        for k, step in enumerate(core["flight_c"]):
            if 4 <= k < len(core["flight_c"]) - 4:
                prism(quad(UPPER_AMBULATORY - 0.15, UPPER_AMBULATORY, step["t0"], step["t1"]),
                      step["floor"], step["floor"] + 1.05, "marble_white", 0.004)
        # Le mur d'echiffre, du cote de la volee B (la plus large) : la volee A garde 1,45 m utiles,
        # assez pour la navigation (rayon 35 cm sur des cellules de 19 cm ; 1,23 m ne passait pas).
        lo, hi = sorted((core["start_a"], core["end_a"]))
        count = max(1, int((hi - lo) * 83.0 / 1.5))
        for j in range(count):
            prism(quad(82.7, 83.0, lo + (hi - lo) * j / count, lo + (hi - lo) * (j + 1) / count), 0.0, 12.0 + HEAD,
                  "stone_cream")


def core_points():
    """Les reperes de chaque cage (pour le parcours, les cibles et les torches)."""
    result = []
    for core in cores():
        land = (core["end_a"] + core["landing_end"]) / 2
        mid_c = (core["start_c"] + core["end_c"]) / 2
        result.append({
            "sector": core["sector"],
            "ambulatory": [*xy(88.5, core["start_a"]), 0.0],
            "bottom_a": [*xy(83.8, core["start_a"]), 0.0],
            "landing": [*xy(82.8, land), 6.0],
            "top_b": [*xy(82.0, core["t1"]), 12.0],
            "praecinctio_1": [*xy(65.0, core["t1"]), 12.0],
            "ambulatory_12": [*xy(89.5, core["start_c"]), 12.0],
            "bottom_c": [*xy(85.8, advance(85.8, core["start_c"], 0.75, -1)), 12.0],
            "top_c": [*xy(85.8, core["end_c"]), 24.0],
            "praecinctio_2": [*xy(82.0, core["tb2"]), 24.0],
            "ambulatory_24": [*xy(90.0, core["tb2"]), 24.0],
            "torches": [
                ([*xy(81.25, land), 7.3], normal_yaw(81.0, land)),
                ([*xy(84.85, mid_c), 18.0 + 1.4], normal_yaw(84.6, mid_c)),
            ],
        })
    return result


# --- Haut mur, portique, velum -------------------------------------------------------------


def summa_wall(door=False):
    """Une travee (6 m) du haut mur, posee a 24 m : de 24 a 35,7 m sous le sol du portique.
    Sa face -Y, visible au-dessus des derniers rangs (29 m), porte une arcade aveugle. `door` :
    la travee d'un vomitoire du second balteus, percee a sa base (1,6 x 2,4 m) vers le
    deambulatoire de 24 m."""
    if door:
        for x0, x1 in ((-3, -0.8), (0.8, 3)):
            kit.masonry(x0, x1, 0, 0, 11.7, 0.8, course=0.55, brick=1.0)
        kit.masonry(-0.8, 0.8, 0, CLEAR, 11.7, 0.8, course=0.55, brick=1.0)
    else:
        kit.masonry(-3, 3, 0, 0, 11.7, 0.8, course=0.55, brick=1.0)
    base = 5.0
    for side in (-1, 1):
        kit.block(side * 2.86, -0.46, base, 0.28, 0.14, 6.7, "marble_white")
        kit.block(side * 1.22, -0.46, base, 0.26, 0.14, 3.2, "marble_white")
    kit.block(0, -0.42, base, 2.2, 0.06, 3.2, "mortar")
    kit.prism([(1.1 * math.cos(math.pi * k / 16), base + 3.2 + 1.1 * math.sin(math.pi * k / 16)) for k in range(17)],
              -0.45, -0.39, "mortar")
    kit.arc(0, -0.47, base + 3.2, ri=1.1, thick=0.26, depth=0.16, segments=17)
    kit.block(0, -0.48, base - 0.1, 6.0, 0.2, 0.18, "marble_white")
    kit.block(0, -0.50, 11.1, 6.0, 0.24, 0.32, "marble_white")
    kit.block(0, -0.56, 11.42, 6.0, 0.16, 0.12, "marble_white")


def porticus():
    """Une travee du portique couvert du sommet, posee a 36 m sous la terrasse (46,5 m)."""
    for x in (-1.5, 1.5):
        kit.column(x, 0, 0, 9.6, 0.32)
    kit.block(0, 0, 9.6, 6.0, 0.86, 0.34, "marble_white")
    kit.block(0, 0, 9.94, 6.0, 0.80, 0.30, "stone_cream")
    kit.block(0, -0.06, 10.24, 6.0, 0.92, 0.26, "marble_white")


def tenture():
    """Une tenture bourgogne pendue a une corniche, face -Y vers l'arene (planche : les rouges
    des tribunes hautes) ; son haut est a l'origine."""
    sculpt.cloth(0, -0.16, 0, 2.6, 1.3, folds=6, swag=0.28)
    kit.rod((-1.35, -0.12, -0.02), (1.35, -0.12, -0.02), 0.035, "bronze", 12)


def tenture_positions():
    """Une tenture au milieu de chaque secteur sur le balteus de la summa cavea, une par travee
    entre les colonnes du portique : (position, lacet)."""
    result = []
    for i in range(16):
        t = math.tau * i / 16
        x, y = xy(83.0, t)
        result.append(([x, y, 26.35], normal_yaw(83.0, t)))
    for i in range(80):
        t = math.tau * (i + 0.5) / 80
        x, y = xy(PORTICUS - 0.45, t)
        result.append(([x, y, 45.55], normal_yaw(PORTICUS - 0.45, t)))
    return result


def _sheet(grid, thickness, material):
    """Une toile : grille de points (lignes x colonnes) epaissie, fermee sur ses bords."""
    rows_, cols = len(grid), len(grid[0])
    points = [p for line in grid for p in line] + [(x, y, z - thickness) for line in grid for x, y, z in line]
    n = rows_ * cols

    def at(i, j, low=False):
        return i * cols + j + (n if low else 0)

    faces = []
    for i in range(rows_ - 1):
        for j in range(cols - 1):
            faces.append((at(i, j), at(i + 1, j), at(i + 1, j + 1), at(i, j + 1)))
            faces.append((at(i, j + 1, True), at(i + 1, j + 1, True), at(i + 1, j, True), at(i, j, True)))
    border = [(0, j) for j in range(cols - 1)] + [(i, cols - 1) for i in range(rows_ - 1)]
    border += [(rows_ - 1, j) for j in range(cols - 1, 0, -1)] + [(i, 0) for i in range(rows_ - 1, 0, -1)]
    for k, (i, j) in enumerate(border):
        p, q = (i, j), border[(k + 1) % len(border)]
        faces.append((at(*q), at(*p), at(*p, True), at(*q, True)))
    kit.solid(points, faces, material, bevel=0)
    kit.FACE_SMOOTH[-len(faces):] = [True] * len(faces)


def velum():
    """Le velum sur les tribunes choisies, tendu des mats du sommet ; le centre reste au ciel."""
    outer, inner = 92.4, 66.0
    for index in VELUM_SECTORS:
        centre, half = math.tau * index / 16, math.pi / 16
        for strip in range(2):
            lo = centre - half + strip * half + 0.004
            hi = lo + half - 0.008
            grid = []
            for i in range(9):
                u = i / 8
                a = outer + (inner - outer) * u
                line = []
                for j in range(7):
                    v = j / 6
                    t = lo + (hi - lo) * v
                    x, y = xy(a, t)
                    z = 51.0 + (45.8 - 51.0) * u - 0.9 * math.sin(math.pi * v) * (0.35 + 0.65 * u)
                    line.append((x, y, z))
                grid.append(line)
            _sheet(grid, 0.035, "burgundy")
            # Les cordages des lisieres, du mat a l'anneau interieur.
            for t in (lo, hi):
                xo, yo = xy(outer, t)
                xi, yi = xy(inner, t)
                kit.rod((xo, yo, 51.05), (xi, yi, 45.85), 0.03, "wood", 8)


def mast_positions():
    return [math.tau * (k + 0.5) / 32 for k in range(32)]




def podium_braziers():
    """Les braseros de la coursive, un entre deux statues : (position, lacet)."""
    result = []
    for i in range(14):
        t = math.tau * i / 14
        x, y = xy(44.9, t)
        result.append(([x, y, PODIUM], normal_yaw(44.9, t) + 180))
    return result
