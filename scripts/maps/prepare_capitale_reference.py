"""Relief naturel de la capitale et son reseau de voies, lus sur le Guide de Creation.

Entrees : `Source/Elements/Terrain/capital/relief-reference/geographie.json` (cadrage, reperes
d'altitude, axes de l'eau, remparts, zones, voies) et le guide qu'il nomme. Les planches sont lues
dans le PDF (`guide_capitale.py`) :

- 06, la carte topographique : le rivage (couleur de l'eau) et le relief, lu sur les courbes de
  niveau (`relief_guide.py`) ; l'equidistance et le niveau viennent des reperes du catalogue ;
- 04, le reseau routier : l'axe de chaque voie, sa classe a sa largeur dessinee ; pave dans
  l'enceinte, terre battue au-dehors ;
- 02, le landscape valide : le couvert (bois, prairie, terre seche) ;
- 01, la carte entiere : les remparts, les jardins et les champs (contours de `geographie.json`).

Sorties, a cote du fichier de geographie : les 16 tuiles `relief-X-Y.r16/.r8` du Landscape
(504 quads de 2 m, neuf couches), `terrain.npz` (hauteur, poids, niveau de l'eau, lu par
`prepare_capitale_reference_water.py`), `T_Capitale_Rivage.png` (masques lus par la matiere), et
des controles : `plan-relief.png`, `controle-guide.png` (la planche 06, le rivage, les voies et
l'enceinte obtenus), `controle-courbes.png`, `hauteur-16bits.png`, `manifest.json`.

Ni construction, ni vegetation placee : la carte porte le relief, l'eau et les voies peintes.
"""
from pathlib import Path
import hashlib
import json
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import guide_capitale  # noqa: E402
import relief_guide  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Source/Elements/Terrain/capital/relief-reference'
N = 2017
STEP = 2.0
ORIGIN = -2016.0
LAYERS = ['Pelouse', 'Prairie', 'HerbeSauvage', 'Foret', 'Terre', 'Chemin', 'Sable', 'Roche', 'Pavage']


# --- Outils de champ ------------------------------------------------------------------------------

edt = relief_guide._edt


def blur(a, sigma):
    if sigma <= 0:
        return a
    r = int(3 * sigma)
    k = np.exp(-np.arange(-r, r + 1, dtype=np.float32) ** 2 / (2 * sigma * sigma))
    k /= k.sum()
    for axis in (0, 1):
        pad = [(0, 0), (0, 0)]
        pad[axis] = (r, r)
        p = np.pad(a, pad, mode='edge')
        acc = np.zeros(a.shape, dtype=np.float32)
        for i, w in enumerate(k):
            s = [slice(None), slice(None)]
            s[axis] = slice(i, i + a.shape[axis])
            acc += w * p[tuple(s)]
        a = acc
    return a


def signed_distance(mask, fine=40, coarse=160):
    """Distance au rivage en metres : positive dehors (`mask` faux), negative dedans. Precise a
    la cellule pres du rivage, au pas de 8 m au-dela (jusqu'a 2,5 km)."""
    near_out = edt(mask, fine) * STEP
    near_in = edt(~mask, fine) * STEP
    small = mask[::4, ::4]
    far_out = np.kron(edt(small, coarse), np.ones((4, 4), np.float32))[:N, :N] * STEP * 4
    far_in = np.kron(edt(~small, coarse), np.ones((4, 4), np.float32))[:N, :N] * STEP * 4
    far_out, far_in = blur(far_out, 6), blur(far_in, 6)
    d_out = np.where(near_out < fine * STEP - 1, near_out, np.maximum(far_out, near_out))
    d_in = np.where(near_in < fine * STEP - 1, near_in, np.maximum(far_in, near_in))
    return np.where(mask, -d_in, d_out)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def value_noise(x, y, seed):
    """Bruit de valeurs sur une trame unite, interpolation quintique : valeurs dans [-1, 1]."""
    i, j = np.floor(x), np.floor(y)
    fx, fy = x - i, y - j
    fx = fx * fx * fx * (fx * (fx * 6 - 15) + 10)
    fy = fy * fy * fy * (fy * (fy * 6 - 15) + 10)

    def corner(di, dj):
        h = np.sin((i + di) * 127.1 + (j + dj) * 311.7 + seed * 74.7) * 43758.5453
        return (h - np.floor(h)) * 2 - 1
    top = corner(0, 0) * (1 - fx) + corner(1, 0) * fx
    bottom = corner(0, 1) * (1 - fx) + corner(1, 1) * fx
    return top * (1 - fy) + bottom * fy


def fbm(x, y, scale, octaves, seed, ridged=False):
    """Bruit fractal de valeurs, la trame tournee et decalee a chaque octave : ni lignes, ni grille."""
    rng = np.random.default_rng(seed)
    total = np.zeros_like(x, dtype=np.float32)
    amp, freq, norm = 1.0, 1.0 / scale, 0.0
    for octave in range(octaves):
        a = rng.uniform(0, np.pi)
        ox, oy = rng.uniform(0, 1000, 2)
        u = (x * np.cos(a) + y * np.sin(a)) * freq + ox
        v = (-x * np.sin(a) + y * np.cos(a)) * freq + oy
        n = value_noise(u, v, seed * 17 + octave)
        if ridged:
            n = 1 - 2 * np.abs(n)
        total += (amp * n).astype(np.float32)
        norm += amp
        amp *= .5
        freq *= 2.03
    return total / norm


def parcels(x, y, spec):
    """Le parcellaire des champs : des bandes en quinconce sur une trame tournee, labourees ou en
    herbe selon un tirage stable par parcelle, bords nets a 2 m."""
    a = np.radians(spec['angle_deg'])
    xr = x * np.cos(a) + y * np.sin(a)
    yr = -x * np.sin(a) + y * np.cos(a)
    w, h = spec['size_m']
    col = np.floor(xr / w)
    shift = np.sin(col * 12.9898) * 43758.5453
    row = np.floor(yr / h + (shift - np.floor(shift)))
    r = np.sin(col * 78.233 + row * 39.425) * 24634.6345
    r = r - np.floor(r)
    fx = np.abs((xr / w) % 1 - .5) * w
    fy = np.abs((yr / h + (shift - np.floor(shift))) % 1 - .5) * h
    edge = smoothstep(0, 2, np.minimum(w / 2 - fx, h / 2 - fy))
    return ((r < spec['ploughed']) * edge).astype(np.float32)


def polygon_mask(points, shape):
    img = Image.new('L', (shape[1], shape[0]), 0)
    ImageDraw.Draw(img).polygon([tuple(p) for p in points], fill=255)
    return np.array(img) > 127


def polyline_param(x, y, pts):
    """Distance a une polyligne et abscisse curviligne normalisee (0 a son debut, 1 a sa fin)."""
    seg = np.diff(pts, axis=0)
    lens = np.hypot(seg[:, 0], seg[:, 1])
    cum = np.concatenate([[0], np.cumsum(lens)])
    best = np.full(x.shape, np.inf, np.float32)
    s = np.zeros(x.shape, np.float32)
    for i, ((ax, ay), (vx, vy), ln) in enumerate(zip(pts[:-1], seg, lens)):
        t = np.clip(((x - ax) * vx + (y - ay) * vy) / (ln * ln), 0, 1)
        d = np.hypot(x - ax - t * vx, y - ay - t * vy)
        closer = d < best
        best = np.where(closer, d, best)
        s = np.where(closer, (cum[i] + t * ln) / cum[-1], s)
    return best, s, cum[-1]


def grey_filter(a, size, op):
    """Minimum ou maximum glissant carre de `size` cellules (separable)."""
    r = size // 2
    for axis in (0, 1):
        pad = [(0, 0), (0, 0)]
        pad[axis] = (r, r)
        p = np.pad(a, pad, mode='edge')
        out = p[tuple(slice(0, a.shape[k]) if k == axis else slice(None) for k in (0, 1))].copy()
        for i in range(1, 2 * r + 1):
            sl = tuple(slice(i, i + a.shape[k]) if k == axis else slice(None) for k in (0, 1))
            out = op(out, p[sl])
        a = out
    return a


def idw(points, values, xx, yy, soft):
    """Interpolation inverse de la distance, adoucie par `soft` (meme unite que les positions)."""
    num = np.zeros(xx.shape, np.float64)
    den = np.zeros(xx.shape, np.float64)
    for (px, py), v in zip(points, values):
        w = 1 / ((xx - px) ** 2 + (yy - py) ** 2 + soft ** 2) ** 1.4
        num += w * v
        den += w
    return num / den


# --- Le relief de la planche 06 ------------------------------------------------------------------

def plate_relief(geo, topo, water):
    """Le relief en metres sur la grille de la planche (eau a zero), et ses controles."""
    h, w = water.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    anchors = geo['anchors']
    pts = [a['px'] for a in anchors]
    alt = np.array([a['m'] for a in anchors], float)
    # L'a priori : les reperes, ramenes au rivage. Il ne donne que le sens des courbes ouvertes.
    shore = edt(water, 300)
    prior = idw(pts, alt, xx, yy, 60.0) * (1 - np.exp(-shore / 25))
    prior = blur(prior.astype(np.float32), 3)
    spec = geo['courbes']
    sk, links = relief_guide.contour_lines(topo, water, spec)
    crans, bands, stats = relief_guide.contour_levels(sk, water, prior)
    # Une bande mal orientee fait une bosse ou un creux de quelques pixels : l'ouverture puis la
    # fermeture (9 px, 24 m) les retirent, les reliefs dessines plus larges restent.
    crans = crans.astype(np.float32)
    size = spec['nettoyage_px']
    crans = grey_filter(grey_filter(crans, size, np.minimum), size, np.maximum)
    crans = grey_filter(grey_filter(crans, size, np.maximum), size, np.minimum)
    # Plus larges, des pointes et des puits etroits (moins de pointes_px) restent : ils sont
    # ecretes a pointes_crans au-dessus (au-dessous) de leur entourage ; les reliefs larges,
    # comme la butte du palais, n'y perdent presque rien.
    size, cap = spec['pointes_px'], spec['pointes_crans']
    low = grey_filter(grey_filter(crans, size, np.minimum), size, np.maximum)
    crans = low + np.clip(crans - low, 0, cap)
    high = grey_filter(grey_filter(crans, size, np.maximum), size, np.minimum)
    crans = high - np.clip(high - crans, 0, cap)
    crans = blur(crans, spec['lissage_px'])
    # Le haut de la planche ecrase les collines lointaines en un lacis de courbes : il se fond
    # dans sa version lissee.
    top = smoothstep(spec['bandeau_px'], 0, yy)
    crans = crans * (1 - top) + blur(crans, 14) * top
    crans = np.where(water, 0, crans)
    # L'equidistance : ce qui accorde le mieux les crans aux altitudes du catalogue.
    at = np.array([crans[min(int(p[1]), h - 1), min(int(p[0]), w - 1)] for p in pts], float)
    step = float((at * alt).sum() / (at * at).sum())
    relief = crans * step
    # Le reste de l'ecart aux reperes, reparti en grand (rayon correction_px) : la forme des
    # courbes ne change pas a l'echelle d'un quartier, les reperes tombent juste.
    resid = alt - at * step
    sigma = spec['correction_px']
    num = np.zeros_like(relief)
    den = np.full_like(relief, 0.35)
    for (px, py), r in zip(pts, resid):
        g = np.exp(-((xx - px) ** 2 + (yy - py) ** 2) / (2 * sigma * sigma))
        num += g * r
        den += g
    relief = relief + (num / den) * (1 - np.exp(-shore / 12))
    relief = np.where(water, 0, np.maximum(relief, 0))
    final = np.array([relief[min(int(p[1]), h - 1), min(int(p[0]), w - 1)] for p in pts], float)
    stats.update(links=links, equidistance_m=round(step, 3),
                 anchors={a['id']: [a['m'], round(float(v), 1)] for a, v in zip(anchors, final)})
    return relief.astype(np.float32), sk, stats


# --- Construction ---------------------------------------------------------------------------------

def build():
    t0 = time.time()
    geo = json.loads((OUT / 'geographie.json').read_text(encoding='utf-8'))
    plates = guide_capitale.plates()
    pw, ph = guide_capitale.PLATE
    scale = geo['cadrage']['metres_par_px']
    ox, oy = geo['cadrage']['origine_m']

    def blue(img):
        a = np.asarray(img).astype(np.float32)
        m = (a[..., 2] - a[..., 0]) > geo['eau']['bleu_sur_rouge']
        m = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
        m = m.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
        return np.asarray(m) > 127

    water_p = blue(plates[geo['planches']['topographie']])
    relief_p, contours, stats = plate_relief(geo, plates[geo['planches']['topographie']], water_p)
    print('relief des courbes', json.dumps(stats), round(time.time() - t0, 1), flush=True)

    # Le couvert de la planche 02 : bois, terre seche, prairie.
    cov = np.asarray(plates[geo['planches']['paysage']]).astype(np.float32)
    c = geo['couvert']
    lum = blur(cov.mean(-1), c['flou_px'])
    dry_p = blur(cov[..., 0] - cov[..., 1], c['flou_px']) > c['sec']
    forest_p = (lum < c['lum_foret']) & ~dry_p & ~water_p
    forest_p = np.asarray(Image.fromarray((forest_p * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))) > 127
    bushes_p = blur(((lum < c['lum_foret'] + 18) & ~water_p).astype(np.float32), 3)

    # Les voies de la planche 04.
    r = geo['routes']
    axes_p, width_p, road_p = relief_guide.road_axes(plates[geo['planches']['routes']], blue(plates[geo['planches']['routes']]), r)
    lo, hi = r['seuils_px']
    widths = r['largeurs_m']
    classes = np.where(width_p >= hi, widths['avenue'], np.where(width_p >= lo, widths['rue'], widths['ruelle']))

    # --- La grille du Landscape et sa lecture dans la planche ---------------------------------
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    x = xx * STEP + ORIGIN
    y = yy * STEP + ORIGIN
    u = (x - ox) / scale
    v = (y - oy) / scale
    uc, vc = np.clip(u, 0, pw - 1), np.clip(v, 0, ph - 1)

    def sample(a, sigma=0.0):
        a = a.astype(np.float32)
        if sigma:
            a = blur(a, sigma)
        x0, y0 = np.floor(uc).astype(int), np.floor(vc).astype(int)
        x1, y1 = np.minimum(x0 + 1, pw - 1), np.minimum(y0 + 1, ph - 1)
        fx, fy = uc - x0, vc - y0
        return ((a[y0, x0] * (1 - fx) + a[y0, x1] * fx) * (1 - fy) + (a[y1, x0] * (1 - fx) + a[y1, x1] * fx) * fy)

    # Au-dela du bord nord ou sud de la planche, les champs ne se prolongent pas pixel par pixel
    # (des rayures) : ils se fondent en 40 m dans leur version tres lissee.
    beyond = np.maximum(-v, v - (ph - 1)).clip(0) * scale
    fade = smoothstep(0, 40, beyond)

    def extend(a, sigma=0.0):
        near = sample(a, sigma)
        return near * (1 - fade) + sample(a, 40.0) * fade

    def to_cells(px):
        px = np.asarray(px, np.float64)
        return ((px[..., 0] * scale + ox - ORIGIN) / STEP, (px[..., 1] * scale + oy - ORIGIN) / STEP)

    def zone(polys, sigma=4):
        polys = polys if isinstance(polys[0][0], (list, tuple)) else [polys]
        img = Image.new('L', (N, N), 0)
        d = ImageDraw.Draw(img)
        for p in polys:
            cx, cy = to_cells(p)
            d.polygon(list(zip(cx.tolist(), cy.tolist())), fill=255)
        return blur(np.asarray(img).astype(np.float32) / 255, sigma)

    # L'eau : le contour de la planche, adouci d'un demi-pixel, dechire d'une frange fractale de
    # 1 a 2 m (le dessin a 2,7 m par pixel ne fait pas de criques plus fines).
    wet = sample(water_p, 1.0)
    edge_noise = fbm(x, y, 45, 3, 11) * 0.8 + fbm(x, y, 160, 3, 12) * 1.4
    water = (wet - 0.5) * 12 + edge_noise > 0
    sd = blur(signed_distance(water), 2.5)
    sd = sd + (blur(sd, 22) - sd) * smoothstep(12, 70, np.abs(sd))
    land_d = np.maximum(sd, 0)
    water_d = np.maximum(-sd, 0)

    # Les niveaux d'eau : la baie a 0, la riviere et le ruisseau montent vers l'amont.
    zones = {}
    level = np.zeros_like(x)
    for key, near, far in (('river', 140, 420), ('creek', 50, 180)):
        cx, cy = to_cells(geo[key]['centre_px'])
        pts = np.stack([cx * STEP + ORIGIN, cy * STEP + ORIGIN], -1)
        d, s, _ = polyline_param(x, y, pts)
        wk = 1 - smoothstep(near, far, d)
        zones[key] = (wk, d, s)
        lo_m, hi_m = geo[key]['level_m']
        level = np.maximum(level, wk * (lo_m + (hi_m - lo_m) * smoothstep(0, 1, s)))
    level = blur(level.astype(np.float32), 4)

    # --- Le relief au sol ------------------------------------------------------------------------
    walls = zone(geo['zones']['remparts'], 3)
    gardens = zone(geo['zones']['jardins'], 6)
    fields = zone(geo['zones']['champs'], 8) * smoothstep(-0.5, 0.0, fbm(x, y, 260, 2, 72))
    land = extend(relief_p)
    # Au nord de la planche, les collines peripheriques montent vers l'horizon de la planche 02.
    beyond_n = np.clip(-v * scale, 0, None)
    ridge = fbm(x, y, 380, 5, 24, ridged=True)
    north = geo['marges']['nord_m'] * smoothstep(0, 700, beyond_n) * (0.65 + 0.35 * ridge) \
        + smoothstep(0, 300, beyond_n) * fbm(x, y, 150, 4, 25) * 8
    land = land + north
    # Le modele fin : sous l'equidistance, pour que les courbes restent lisibles ; plus vif hors
    # de l'enceinte, croupes et ravines dans les bois et les collines.
    forest = extend(forest_p, 1.5)
    forest = forest * (1 - fade) + smoothstep(0.35, 0.65, forest + fbm(x, y, 180, 4, 27) * 0.3) * fade
    in_city = walls
    rough = 0.35 + 0.65 * (1 - in_city)
    land += (fbm(x, y, 140, 4, 22) * 1.4 * rough + fbm(x, y, 38, 3, 23) * 0.35
             + (forest + smoothstep(0, 400, beyond_n)) * fbm(x, y, 70, 4, 26, ridged=True) * 1.6)
    # La berge : une levee basse au bord de l'eau, puis la pente lue sur les courbes.
    berge = geo['rive_m']
    land = land + berge['berge'] * smoothstep(0, berge['largeur'], land_d)

    # Les voies au sol, rendues au double de la grille puis ramenees (bords sans marches).
    sup = 2
    img = Image.new('L', (N * sup, N * sup), 0)
    d = ImageDraw.Draw(img)
    ys_p, xs_p = np.nonzero(axes_p)
    cx, cy = to_cells(np.stack([xs_p, ys_p], -1).astype(float))
    width_c = classes[ys_p, xs_p] / STEP * sup
    index = {(int(a), int(b)): k for k, (a, b) in enumerate(zip(ys_p, xs_p))}
    for k, (py, px) in enumerate(zip(ys_p, xs_p)):
        for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
            j = index.get((int(py + dy), int(px + dx)))
            if j is not None:
                wdt = max(1, int(round(min(width_c[k], width_c[j]))))
                d.line([(cx[k] * sup, cy[k] * sup), (cx[j] * sup, cy[j] * sup)], fill=255, width=wdt)
        rad = width_c[k] / 2
        d.ellipse([cx[k] * sup - rad, cy[k] * sup - rad, cx[k] * sup + rad, cy[k] * sup + rad], fill=255)
    road = np.asarray(img.resize((N, N), Image.BOX)).astype(np.float32) / 255
    road = smoothstep(0.15, 0.85, blur(road, 0.6))
    road *= ~water
    road_edge = smoothstep(0.02, 0.5, blur(road, r['bord_m'] / STEP))
    # Le nivellement : sous la voie, le terrain prend sa moyenne voisine (pas de devers).
    graded = blur(land.astype(np.float32), r['nivellement_m'] / STEP / 2)
    land = land * (1 - road_edge) + graded * road_edge

    # L'emprise de l'Arena of Fate : l'ovale et son parvis de niveau (mediane du relief de
    # l'emprise), raccordes a la pente ; le parvis est une voie pavee, l'ovale n'en porte aucune.
    a = geo['arene']
    acx, acy = a['centre_px'][0] * scale + ox, a['centre_px'][1] * scale + oy
    cap = np.radians(a['cap_deg'])
    lx = (x - acx) * np.cos(cap) + (y - acy) * np.sin(cap)
    ly = -(x - acx) * np.sin(cap) + (y - acy) * np.cos(cap)
    ra, rb = a['demi_axes_m']
    radius = np.hypot(lx, ly)
    rim = 1 / np.sqrt((lx / np.maximum(radius, 1e-6) / ra) ** 2 + (ly / np.maximum(radius, 1e-6) / rb) ** 2)
    arena_d = radius - rim  # distance au bord de l'ovale le long du rayon, negative dedans
    forecourt = arena_d <= a['parvis_m']
    arena_z = float(np.median(land[forecourt]))
    keep = smoothstep(a['parvis_m'], a['parvis_m'] + a['raccord_m'], arena_d)
    land = land * keep + arena_z * (1 - keep)
    # Sous l'ovale, le sol du monument (sable, galeries) se pose a arena_z : le relief s'y abaisse
    # d'un metre pour ne pas transparaitre dans ses dalles, puis, sous les etages -1 et -2 (a 17 m
    # et plus du bord, jusqu'a -12,35 m), de 14,5 m : les portes du grand axe y descendent.
    land -= smoothstep(-1, -3, arena_d) + 13.5 * smoothstep(-6, -14, arena_d)
    road = np.maximum(road * (arena_d > 0), smoothstep(a['parvis_m'] + 1, a['parvis_m'] - 1, arena_d) * (arena_d > -2))

    # Les fonds : plateau peu profond le long des rives, cuvette de la baie, lits des cours d'eau.
    bay = geo['bay']
    depth = (bay['shelf_m'] * (1 - np.exp(-water_d / bay['shelf_bed_m']))
             + (bay['depth_m'] - bay['shelf_m']) * (1 - np.exp(-water_d / bay['bed_m'])) ** 1.6)
    for key in ('river', 'creek'):
        wk, _, _ = zones[key]
        bed = geo[key]['depth_m'] * (1 - np.exp(-water_d / geo[key]['bed_m']))
        depth = depth * (1 - wk) + bed * wk
    depth += fbm(x, y, 90, 3, 31) * 0.6 * smoothstep(4, 30, water_d)
    water_level = level
    height = np.where(water, -depth + water_level, land + level)
    height = blur(height.astype(np.float32), 0.8)
    shore_z = height - water_level
    ring = forecourt & (arena_d > 1)  # le parvis, ou les portes du monument rejoignent le sol

    # --- Couches peintes -------------------------------------------------------------------------
    dy, dx = np.gradient(height, STEP)
    slope = np.hypot(dx, dy)
    pts = np.stack(to_cells([a['px'] for a in geo['anchors']]), -1) * STEP + ORIGIN
    beach = idw(pts, [a['beach'] for a in geo['anchors']], x, y, 260.0).astype(np.float32)
    beach = blur(beach, 20)
    dry = extend(dry_p, 2.0) + smoothstep(100, 600, beyond_n)
    rocky = np.clip(smoothstep(0.5, 0.95, slope) + dry * smoothstep(0.25, 0.6, slope), 0, 1)

    paving = road * in_city
    track = road * (1 - in_city)
    free = 1 - road
    sand = (1 - smoothstep(0.4, 2.2, shore_z)) * smoothstep(-6, -0.5, shore_z) * (0.05 + 0.95 * beach)
    sand *= 1 - smoothstep(0.25, 0.5, slope)
    sand += np.where(water, 0.25 + 0.6 * beach, 0) * (1 - smoothstep(2, 7, water_d))
    sand = np.clip(sand * (1 - 0.85 * zones['creek'][0]) * (1 - in_city * 0.6), 0, 1) * free
    rock = np.clip(rocky + smoothstep(0.2, 0.8, fbm(x, y, 45, 3, 41)) * dry * 0.6, 0, 1) * (1 - 0.6 * sand) * free
    creek_w = zones['creek'][0]
    soil = (fields * parcels(x, y, geo['parcels'])
            + creek_w * (1 - smoothstep(0, 7, land_d)) * 0.55
            + dry * 0.35
            + in_city * (1 - gardens) * smoothstep(-0.1, 0.5, fbm(x, y, 55, 3, 52)) * 0.55)
    soil = np.clip(soil, 0, 1) * (1 - sand) * (1 - rock) * free
    rest = np.clip(free - sand - rock - soil, 0, 1)
    woods = rest * np.clip(forest * (1 - in_city * (1 - gardens)), 0, 1)
    rest = np.clip(rest - woods, 0, 1)
    lawn = rest * np.clip(gardens * 0.9 + in_city * 0.6, 0, 1)
    shrub = (rest - lawn) * np.clip(extend(bushes_p) * 1.2 + dry * 0.5 + smoothstep(0.2, 0.7, fbm(x, y, 240, 3, 61)) * 0.4, 0, 1)
    meadow = np.clip(rest - lawn - shrub, 0, None)
    weights = np.stack([lawn, meadow, shrub, woods, soil, track, sand, rock, paving])
    weights = np.round(weights / np.maximum(weights.sum(axis=0), 1e-6) * 255).astype(np.int16)
    weights[1] += 255 - weights.sum(axis=0)
    weights = np.clip(weights, 0, 255).astype(np.uint8)

    # --- Ecriture des tuiles ---------------------------------------------------------------------
    np.savez_compressed(OUT / 'terrain.npz', height=height.astype(np.float32), weights=weights,
                        water_z=water_level.astype(np.float32))
    tiles, files = [], {}
    for iy in range(4):
        for ix in range(4):
            sub = (slice(iy * 504, iy * 504 + 505), slice(ix * 504, ix * 504 + 505))
            name = f'relief-{ix}-{iy}'
            # Echelle Z de 100 : une unite de hauteur vaut 1/128 m.
            np.round(height[sub] * 128 + 32768).astype('<u2').tofile(OUT / (name + '.r16'))
            weights[:, sub[0], sub[1]].tofile(OUT / (name + '.r8'))
            tiles.append(dict(id=name, origin=[ORIGIN + ix * 1008, ORIGIN + iy * 1008], quads=504, spacing=2))
            for ext in ('.r16', '.r8'):
                files[name + ext] = hashlib.sha256((OUT / (name + ext)).read_bytes()).hexdigest()

    # Masques pour la matiere : R berge humide, G fond immerge, B roche des rivages et des
    # collines, A champs.
    wet_band = (1 - smoothstep(0.2, 2.2, shore_z)) * (1 - smoothstep(0, 14, land_d)) * (~water)
    under = smoothstep(0, 1.5, -shore_z) * (1 - smoothstep(1.5, 10, water_d))
    rivage = np.stack([wet_band, under, np.clip(dry * 0.8, 0, 1), fields], axis=-1)
    Image.fromarray(np.round(np.clip(rivage, 0, 1) * 255).astype(np.uint8), 'RGBA').resize(
        (2048, 2048), Image.BILINEAR).save(OUT / 'T_Capitale_Rivage.png')

    coverage = {name: round(float(weights[k].mean() / 255), 4) for k, name in enumerate(LAYERS)}
    manifest = dict(reference='Guide de Creation.pdf', geography='geographie.json', plates=geo['planches'],
                    extent_m=[-2016, -2016, 2016, 2016], sea_level_m=0, tiles=tiles, layers=LAYERS,
                    roads=dict(axis_pixels=int(axes_p.sum()), paved_fraction=round(float(paving.mean()), 4),
                               dirt_fraction=round(float(track.mean()), 4), widths_m=widths),
                    building_sites=0, vegetation=0, coverage=coverage,
                    arena=dict(centre_m=[round(float(acx), 2), round(float(acy), 2)], cap_deg=a['cap_deg'],
                               demi_axes_m=[ra, rb], sol_m=round(float(np.median(height[ring])), 3),
                               parvis_ecart_m=round(float(np.ptp(height[ring])), 3)),
                    contours=stats, height_range_m=[float(height.min()), float(height.max())],
                    water_fraction=float(water.mean()),
                    interpretation='Relief lu sur les courbes de la planche 06 (crans par moindres carres, equidistance '
                                   'et niveau donnes par les reperes du catalogue) ; rivage de la planche 06 ; voies de la '
                                   'planche 04, pavees dans l\'enceinte de la planche 01, en terre au-dehors.')
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    prov_path = OUT / 'provenance.json'
    prov = json.loads(prov_path.read_text(encoding='utf-8')) if prov_path.exists() else {}
    prov.update(geography='geographie.json', guide=geo['guide'], generator='scripts/maps/prepare_capitale_reference.py',
                files=files, roads=True, building_sites=False, buildings=False, vegetation=False)
    for stale in ('reference', 'geography_reference', 'approved_preview'):
        prov.pop(stale, None)
    prov_path.write_text(json.dumps(prov, indent=2, ensure_ascii=False), encoding='utf-8')

    # --- Controles ------------------------------------------------------------------------------
    light = np.clip(.78 - .8 * dx - .6 * dy, .4, 1.15)[..., None]
    palette = np.array([[118, 150, 70], [140, 150, 82], [108, 116, 66], [62, 88, 48], [122, 96, 64],
                        [150, 122, 88], [206, 192, 150], [128, 124, 118], [150, 146, 140]], np.float32)
    land_rgb = np.tensordot(np.moveaxis(weights.astype(np.float32) / 255, 0, -1), palette, axes=1) * light
    dep = np.clip((water_level - height) / 20, 0, 1)[..., None]
    water_rgb = np.array([70, 170, 180]) * (1 - dep) + np.array([22, 82, 118]) * dep
    rgb = np.where((height > water_level)[..., None], land_rgb, water_rgb).clip(0, 255).astype(np.uint8)
    Image.fromarray(rgb).save(OUT / 'plan-relief.png')
    Image.fromarray(np.round(height * 128 + 32768).astype(np.uint16)).save(OUT / 'hauteur-16bits.png')

    # Sur la planche 06 : le rivage obtenu (jaune), les voies (rouge : pavees, orange : terre),
    # l'enceinte (blanc).
    topo = np.asarray(plates[geo['planches']['topographie']]).copy()
    ctrl = Image.fromarray(topo)
    inside_p = polygon_mask(geo['zones']['remparts'], (ph, pw))
    over = np.zeros((ph, pw, 3), np.uint8)
    over[road_p & inside_p] = (200, 40, 30)
    over[road_p & ~inside_p] = (230, 140, 30)
    ctrl = Image.fromarray(np.where((road_p)[..., None], (topo * 0.35 + over * 0.65).astype(np.uint8), topo))
    dr = ImageDraw.Draw(ctrl)
    dr.line([tuple(p) for p in geo['zones']['remparts'] + geo['zones']['remparts'][:1]], fill=(255, 255, 255), width=2)
    # Le rivage du sol, ramene sur la planche.
    coast = water ^ np.roll(water, 1, 0) | water ^ np.roll(water, 1, 1)
    cy_, cx_ = np.nonzero(coast[::1, ::1])
    pu = ((cx_ * STEP + ORIGIN) - ox) / scale
    pv = ((cy_ * STEP + ORIGIN) - oy) / scale
    ok = (pu >= 0) & (pu < pw) & (pv >= 0) & (pv < ph)
    arr = np.asarray(ctrl).copy()
    arr[pv[ok].astype(int), pu[ok].astype(int)] = (255, 236, 0)
    for a in geo['anchors']:
        px, py = a['px']
        arr[max(py - 3, 0):py + 4, max(px - 3, 0):px + 4] = (20, 20, 160)
    Image.fromarray(arr).save(OUT / 'controle-guide.png')
    # Le relief lu, ombre, et les courbes raccordees de la planche.
    gy, gx = np.gradient(relief_p)
    shade = np.clip(.75 - (gx * 0.6 - gy * 0.8) / scale * 3, 0.2, 1.3)
    tint = np.clip(relief_p / 90, 0, 1)
    img = np.stack([150 + 90 * tint, 170 + 50 * tint, 120 + 40 * tint], -1) * shade[..., None]
    img[water_p] = (60, 120, 200)
    img[contours & ~water_p] = img[contours & ~water_p] * 0.55
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(OUT / 'controle-courbes.png')
    print(json.dumps({k: manifest[k] for k in ('height_range_m', 'water_fraction', 'coverage', 'roads')}, ensure_ascii=False))
    print('duree', round(time.time() - t0, 1), 's')
    return manifest


if __name__ == '__main__':
    build()
