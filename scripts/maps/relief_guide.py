"""Lecture des planches du Guide de Creation : le relief des courbes de niveau (planche 06) et
l'axe des voies (planche 04). Numpy et Pillow seulement.

Le relief se lit en quatre temps :

1. les courbes : traits plus sombres que leur fond, debarrasses des points isoles, reduits a leur
   squelette d'un pixel ; chaque extremite libre se prolonge, dans son axe, jusqu'a la courbe ou
   au cadre qu'elle allait rejoindre (les traits dessines s'interrompent souvent) ;
2. les bandes : les regions entre deux courbes, et le graphe de leurs voisinages ;
3. les niveaux : une bande est d'un cran plus haute ou plus basse que chacune de ses voisines. Une
   bande enfermee dans sa voisine (boucle fermee) est plus haute ; sinon le sens est celui que
   donne l'a priori (les reperes d'altitude). Le systeme se resout par moindres carres, les
   bandes du rivage tenues au niveau zero ;
4. la surface : les courbes prennent la valeur de leur cran, l'eau zero, le sommet de chaque bande
   sans voisine plus haute un demi-cran de plus ; entre elles, la surface la plus douce (membrane).
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


# --- Composantes connexes -------------------------------------------------------------------------

def label(mask, conn8=False):
    """Etiquette les composantes de `mask` (0 hors masque, 1..n), par union de classes ligne a
    ligne : les segments horizontaux d'une ligne se rattachent a ceux de la ligne du dessus."""
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32)
    parent = [0]

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    prev_runs = []
    for y in range(h):
        row = mask[y]
        if not row.any():
            prev_runs = []
            continue
        d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
        starts, ends = np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]
        runs = []
        j = 0
        for s, e in zip(starts, ends):
            lo, hi = (s - 1, e + 1) if conn8 else (s, e)
            ids = []
            while j < len(prev_runs) and prev_runs[j][1] <= lo:
                j += 1
            k = j
            while k < len(prev_runs) and prev_runs[k][0] < hi:
                ids.append(prev_runs[k][2])
                k += 1
            if ids:
                roots = [find(i) for i in ids]
                r = min(roots)
                for q in roots:
                    parent[q] = r
            else:
                r = len(parent)
                parent.append(r)
            lab[y, s:e] = r
            runs.append((s, e, r))
        prev_runs = runs
    roots = np.array([find(i) for i in range(len(parent))], np.int32)
    uniq, inv = np.unique(roots, return_inverse=True)
    return inv.astype(np.int32)[lab], len(uniq) - 1


# --- Squelette et raccords ------------------------------------------------------------------------

def _neighbours(m):
    p = np.pad(m, 1)
    return [p[:-2, 1:-1], p[:-2, 2:], p[1:-1, 2:], p[2:, 2:], p[2:, 1:-1], p[2:, :-2], p[1:-1, :-2], p[:-2, :-2]]


def skeletonize(mask):
    """Amincissement de Zhang et Suen : des traits d'un pixel, connexes en 8."""
    m = mask.astype(np.uint8).copy()
    while True:
        changed = 0
        for step in (0, 1):
            p = _neighbours(m)
            b = sum(p)
            a = sum(((p[i] == 0) & (p[(i + 1) % 8] == 1)).astype(np.uint8) for i in range(8))
            if step == 0:
                c1, c2 = p[0] * p[2] * p[4], p[2] * p[4] * p[6]
            else:
                c1, c2 = p[0] * p[2] * p[6], p[0] * p[4] * p[6]
            rm = (m == 1) & (b >= 2) & (b <= 6) & (a == 1) & (c1 == 0) & (c2 == 0)
            changed += int(rm.sum())
            m[rm] = 0
        if not changed:
            return m.astype(bool)


_OFFSETS = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]


def _direction(sk, y, x, steps=10):
    """La direction de sortie d'une extremite : de son dixieme voisin vers elle."""
    h, w = sk.shape
    path = [(y, x)]
    py, px = y, x
    for _ in range(steps):
        nxt = None
        for dy, dx in _OFFSETS:
            qy, qx = py + dy, px + dx
            if 0 <= qy < h and 0 <= qx < w and sk[qy, qx] and (qy, qx) not in path:
                nxt = (qy, qx)
                break
        if nxt is None:
            break
        py, px = nxt
        path.append(nxt)
    v = np.array([y - py, x - px], float)
    n = np.hypot(*v)
    return (v / n if n > 0 else None), len(path)


def link_gaps(sk, radius, cone_deg):
    """Prolonge chaque extremite libre vers le trait le plus proche dans son axe (un autre trait,
    ou le bout de la meme courbe au-dela de sa coupure), ou vers le cadre."""
    h, w = sk.shape
    comp, _ = label(sk, True)
    p = _neighbours(sk.astype(np.uint8))
    ey, ex = np.nonzero(sk & (sum(p) == 1))
    grid = {}
    for y, x in zip(*np.nonzero(sk)):
        grid.setdefault((y // radius, x // radius), []).append((y, x))
    img = Image.fromarray((sk * 255).astype(np.uint8))
    draw = ImageDraw.Draw(img)
    cos_cone = np.cos(np.radians(cone_deg))
    links = 0
    for y, x in zip(ey, ex):
        v, n = _direction(sk, y, x)
        if v is None or n < 6:
            continue
        best = None
        for gy in range(y // radius - 1, y // radius + 2):
            for gx in range(x // radius - 1, x // radius + 2):
                for qy, qx in grid.get((gy, gx), ()):
                    dy, dx = qy - y, qx - x
                    dist = np.hypot(dy, dx)
                    if dist < 3 or dist > radius:
                        continue
                    c = (dy * v[0] + dx * v[1]) / dist
                    if c < cos_cone or (comp[qy, qx] == comp[y, x] and dist < 12):
                        continue
                    score = dist * (2 - c)
                    if best is None or score < best[0]:
                        best = (score, qy, qx)
        if best is None:
            for t in range(3, radius + 1):
                qy, qx = int(round(y + v[0] * t)), int(round(x + v[1] * t))
                if qy <= 0 or qx <= 0 or qy >= h - 1 or qx >= w - 1:
                    best = (0, min(max(qy, 0), h - 1), min(max(qx, 0), w - 1))
                    break
        if best:
            draw.line([(x, y), (best[2], best[1])], fill=255, width=1)
            links += 1
    return np.asarray(img) > 127, links


# --- Moindres carres sur la grille ----------------------------------------------------------------

def membrane(mu, target, start, iters=6000, tol=1e-7):
    """La surface la plus douce qui passe par `target` la ou `mu` est fort : minimise
    sum |grad h|^2 + mu (h - target)^2, par gradient conjugue preconditionne."""
    def apply(hh):
        out = mu * hh
        fx = hh[:, 1:] - hh[:, :-1]
        out[:, 1:] += fx
        out[:, :-1] -= fx
        fy = hh[1:, :] - hh[:-1, :]
        out[1:, :] += fy
        out[:-1, :] -= fy
        return out
    b = mu * target
    diag = mu + 4.0
    x = start.astype(np.float64).copy()
    r = b - apply(x)
    z = r / diag
    p = z.copy()
    rz = (r * z).sum()
    bn = np.sqrt((b * b).sum()) + 1e-12
    for it in range(iters):  # noqa: B007 (son rang sert après la boucle)
        ap = apply(p)
        al = rz / (p * ap).sum()
        x += al * p
        r -= al * ap
        if np.sqrt((r * r).sum()) / bn < tol:
            break
        z = r / diag
        rz2 = (r * z).sum()
        p = z + rz2 / rz * p
        rz = rz2
    return x, it


def _shift(a, dy, dx, fill=0):
    h, w = a.shape
    out = np.full_like(a, fill)
    out[max(-dy, 0):h + min(-dy, 0), max(-dx, 0):w + min(-dx, 0)] = a[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)]
    return out


def _edt(feature, radius):
    big = np.float32(radius * radius * 4 + 1)
    out = None
    for axis in (0, 1):
        src = np.where(feature, 0, big).astype(np.float32) if axis == 0 else out
        best = src.copy()
        n = src.shape[axis]
        for k in range(1, radius + 1):
            a = [slice(None), slice(None)]
            b = [slice(None), slice(None)]
            a[axis], b[axis] = slice(k, n), slice(0, n - k)
            np.minimum(best[tuple(a)], src[tuple(b)] + np.float32(k * k), out=best[tuple(a)])
            np.minimum(best[tuple(b)], src[tuple(a)] + np.float32(k * k), out=best[tuple(b)])
        out = best
    return np.sqrt(np.minimum(out, radius * radius))


# --- Le relief des courbes ------------------------------------------------------------------------

def contour_lines(topo, water, spec):
    """Le squelette raccorde des courbes de la planche topographique, cadre compris."""
    a = np.asarray(topo).astype(np.float32)
    lum = a.mean(-1)
    bg = np.asarray(Image.fromarray(lum.astype(np.uint8)).filter(ImageFilter.MaxFilter(7))).astype(np.float32)
    line = ((bg - lum) > spec['assombrissement']) & ~water
    comp, _ = label(line, True)
    line &= np.bincount(comp.ravel())[comp] >= spec['longueur_min_px']
    line = np.asarray(Image.fromarray((line * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 127
    sk = skeletonize(line)
    comp, _ = label(sk, True)
    sk &= np.bincount(comp.ravel())[comp] >= spec['squelette_min_px']
    sk, links = link_gaps(sk, spec['raccord_px'], spec['cone_deg'])
    sk[0, :] = sk[-1, :] = sk[:, 0] = sk[:, -1] = True
    return sk, links


def contour_levels(sk, water, prior):
    """Le cran de chaque bande entre deux courbes (moindres carres sur leur graphe) et la surface
    continue qui en decoule, en crans (0 au rivage)."""
    h, w = sk.shape
    bands, n = label(~sk & ~water, False)
    count = np.bincount(bands.ravel(), minlength=n + 1)
    # Voisinages : deux bandes de part et d'autre d'un trait du squelette.
    pairs = {}
    for dy, dx in [(0, 2), (2, 0), (2, 2), (2, -2), (0, 3), (3, 0)]:
        a, b = _shift(bands, -dy, -dx), _shift(bands, dy, dx)
        m = (a > 0) & (b > 0) & (a != b) & (sk | (bands == 0)) & ~water
        lo, hi = np.minimum(a[m], b[m]).astype(np.int64), np.maximum(a[m], b[m]).astype(np.int64)
        keys, c = np.unique(lo * 1_000_000 + hi, return_counts=True)
        for k, cc in zip(keys, c):
            pairs[k] = pairs.get(k, 0) + cc
    idx = bands.ravel()
    mean_prior = np.bincount(idx, weights=prior.ravel(), minlength=n + 1) / np.maximum(count, 1)
    ys, xs = np.nonzero(bands)
    lab = bands[ys, xs]
    y0, y1 = np.full(n + 1, h), np.zeros(n + 1, int)
    x0, x1 = np.full(n + 1, w), np.zeros(n + 1, int)
    np.minimum.at(y0, lab, ys)
    np.maximum.at(y1, lab, ys)
    np.minimum.at(x0, lab, xs)
    np.maximum.at(x1, lab, xs)
    shore = np.asarray(Image.fromarray((water * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 127
    touch_water = np.bincount(idx, weights=(shore & (bands > 0)).ravel().astype(float), minlength=n + 1)
    frame = np.zeros((h, w), bool)
    frame[:3, :] = frame[-3:, :] = frame[:, :3] = frame[:, -3:] = True
    touch_frame = np.bincount(idx, weights=(frame & (bands > 0)).ravel().astype(float), minlength=n + 1) > 0

    def inside(a, b):
        return (y0[a] > y0[b] + 2 and y1[a] < y1[b] - 2 and x0[a] > x0[b] + 2 and x1[a] < x1[b] - 2
                and not touch_frame[a] and touch_water[a] == 0)

    rows, signs, weights = [], [], []
    enclosed = 0
    for key, c in pairs.items():
        a, b = int(key // 1_000_000), int(key % 1_000_000)
        if count[a] < 8 or count[b] < 8:
            continue
        if inside(a, b):
            s, conf = 1.0, 1.0
            enclosed += 1
        elif inside(b, a):
            s, conf = -1.0, 1.0
            enclosed += 1
        else:
            d = mean_prior[a] - mean_prior[b]
            s, conf = (1.0 if d >= 0 else -1.0), float(np.clip(abs(d) / 3.0, 0.05, 1))
        rows.append((a, b))
        signs.append(s)
        weights.append(c * conf)
    rows = np.array(rows)
    signs = np.array(signs)
    weights = np.array(weights, float)
    m = np.zeros((n + 1, n + 1))
    r = np.zeros(n + 1)
    np.add.at(m, (rows[:, 0], rows[:, 0]), weights)
    np.add.at(m, (rows[:, 1], rows[:, 1]), weights)
    np.add.at(m, (rows[:, 0], rows[:, 1]), -weights)
    np.add.at(m, (rows[:, 1], rows[:, 0]), -weights)
    np.add.at(r, rows[:, 0], weights * signs)
    np.add.at(r, rows[:, 1], -weights * signs)
    # Le rivage tient les bandes qui le touchent ; l'a priori retient faiblement les autres.
    m[np.arange(n + 1), np.arange(n + 1)] += touch_water * 5.0 + 1e-5 * count
    r += 1e-5 * count * mean_prior
    level = np.linalg.solve(m, r)
    level[0] = 0

    # La surface : chaque trait a la moyenne des crans voisins plus un demi-cran, l'eau zero,
    # le coeur de chaque bande sommitale un cran de plus.
    total = np.zeros((h, w))
    seen = np.zeros((h, w))
    for dy, dx in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1), (0, 2), (2, 0), (0, -2), (-2, 0)]:
        b = _shift(bands, dy, dx)
        total += np.where(b > 0, level[b], 0)
        seen += b > 0
    fixed = (sk & (seen > 0)) | water
    target = np.where(water, 0.0, total / np.maximum(seen, 1) + 0.5)
    higher = np.zeros(n + 1, bool)
    for (a, b) in rows:
        higher[b if level[a] > level[b] else a] = True
    summit = (~higher) & (count > 150)
    summit[0] = False
    depth = _edt(bands == 0, 60)
    for k in np.nonzero(summit)[0]:
        mk = bands == k
        dk = np.where(mk, depth, 0)
        y, x = np.unravel_index(np.argmax(dk), dk.shape)
        rad = max(1, int(dk[y, x] * 0.4))
        sl = (slice(max(0, y - rad), y + rad + 1), slice(max(0, x - rad), x + rad + 1))
        yy, xx = np.ogrid[sl[0], sl[1]]
        disk = (((yy - y) ** 2 + (xx - x) ** 2) <= rad * rad) & mk[sl]
        fixed[sl] |= disk
        target[sl] = np.where(disk, level[k] + 1.0, target[sl])
    start = np.where(bands > 0, level[bands] + 0.5, target)
    surface, its = membrane(np.where(fixed, 100.0, 1e-6), target, start)
    stats = dict(bands=int(n), edges=len(rows), enclosed=enclosed, summits=int(summit.sum()),
                 levels=float(level[1:].max() - level[1:].min()), iterations=int(its))
    return surface, bands, stats


# --- Les voies ------------------------------------------------------------------------------------

def road_axes(plate, water, spec):
    """Le squelette des voies de la planche 04 et leur largeur dessinee (pixels), sans les lisieres
    des bois (traits d'un ou deux pixels que l'ouverture retire)."""
    a = np.asarray(plate).astype(np.float32)
    r, g = a[..., 0], a[..., 1]
    mx, mn = a.max(-1), a.min(-1)
    road = (a.mean(-1) < spec['lum_max']) & ((mx - mn) / (mx + 1) < spec['saturation_max']) & (g < r + 8) & ~water
    img = Image.fromarray((road * 255).astype(np.uint8))
    # Fermeture (le liseré sombre et le gris de la chaussee font un seul trait), puis ouverture.
    img = img.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    img = img.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    road = np.asarray(img) > 127
    comp, _ = label(road, True)
    road &= np.bincount(comp.ravel())[comp] >= 60
    width = 2 * _edt(~road, 12)
    sk = skeletonize(road)
    comp, _ = label(sk, True)
    sk &= np.bincount(comp.ravel())[comp] >= 8
    return sk, width * sk, road
