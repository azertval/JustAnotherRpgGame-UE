#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Compare des captures du moteur à leurs références, à tolérance, par blocs (LOT-1014).

Sous Lumen et un anticrénelage temporel, deux captures de la même scène ne sont jamais identiques
au pixel : le bruit de l'accumulation change d'un lancement à l'autre. Ce qui ne change pas, c'est
la **moyenne d'un bloc** de pixels. Une capture est donc ramenée à une image de blocs — un pixel
par bloc, sa couleur moyenne — et comparée à la référence, qui est elle-même une image de blocs.

Une référence est un dossier :

- `reference.json` : la taille des captures, le côté d'un bloc, et les deux seuils ;
- une image de blocs par capture, du même nom (`socle-1200.png`) : quelques kilo-octets, lisible
  à l'œil comme une vignette, et sans le poids d'une capture entière dans le dépôt.

Les deux seuils :

- `tolerance` : l'écart, en niveaux sur 255, qu'un bloc peut avoir avec sa référence sur son canal
  le plus éloigné ;
- `outliers` : la part des blocs, de 0 à 1, qui peut dépasser cette tolérance.

Une capture passe si la part de ses blocs hors tolérance ne dépasse pas `outliers`. Les seuils
s'écrivent dans `reference.json` avec la mesure qui les justifie (`comment`) : ils ne se devinent
pas, ils se relèvent sur plusieurs captures de la même scène.

Usage :
    python scripts/checks/compare_captures.py --reference REF --captures DOSSIER
    python scripts/checks/compare_captures.py --reference REF --captures DOSSIER --update

`--update` réécrit les images de blocs depuis les captures (et crée `reference.json` s'il manque,
aux seuils par défaut) : c'est ainsi qu'une image qui a changé exprès devient la référence. Le
changement se relit dans la PR, vignette contre vignette.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REFERENCE_FILE = "reference.json"
DEFAULT_BLOCK = 24
DEFAULT_TOLERANCE = 8.0
DEFAULT_OUTLIERS = 0.01


def block_means(pixels: np.ndarray, block: int) -> np.ndarray:
    """La couleur moyenne de chaque bloc de `block` pixels de côté : (lignes, colonnes, 3)."""
    height, width = pixels.shape[:2]
    if height % block or width % block:
        raise ValueError(f"{width} × {height} ne se découpe pas en blocs de {block}")
    cells = pixels[:, :, :3].astype(np.float64).reshape(height // block, block, width // block, block, 3)
    return cells.mean(axis=(1, 3))


def compare(reference: np.ndarray, candidate: np.ndarray, tolerance: float) -> dict:
    """L'écart d'une image de blocs à sa référence : moyen, pire, et part des blocs hors tolérance."""
    if reference.shape != candidate.shape:
        raise ValueError(f"{candidate.shape[1]} × {candidate.shape[0]} blocs, "
                         f"{reference.shape[1]} × {reference.shape[0]} attendus")
    # L'écart d'un bloc est celui de son canal le plus éloigné.
    distance = np.abs(candidate.astype(np.float64) - reference.astype(np.float64)).max(axis=2)
    return {"mean": float(distance.mean()), "worst": float(distance.max()),
            "beyond": float((distance > tolerance).mean())}


def load_pixels(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"))


def read_reference(folder: Path) -> dict:
    return json.loads((folder / REFERENCE_FILE).read_text(encoding="utf-8"))


def update(folder: Path, captures: Path, names: list[str]) -> int:
    """Réécrit les images de blocs de `folder` depuis les captures `names` de `captures`."""
    settings = (read_reference(folder) if (folder / REFERENCE_FILE).is_file()
                else {"block": DEFAULT_BLOCK, "tolerance": DEFAULT_TOLERANCE, "outliers": DEFAULT_OUTLIERS})
    folder.mkdir(parents=True, exist_ok=True)
    size = None
    for name in names:
        pixels = load_pixels(captures / name)
        if size is not None and [pixels.shape[1], pixels.shape[0]] != size:
            print(f"compare_captures : {name} n'a pas la taille des autres captures", file=sys.stderr)
            return 1
        size = [pixels.shape[1], pixels.shape[0]]
        means = np.rint(block_means(pixels, settings["block"])).astype(np.uint8)
        Image.fromarray(means, "RGB").save(folder / name, optimize=True)
        print(f"compare_captures : référence écrite, {name} ({means.shape[1]} × {means.shape[0]} blocs)")
    settings["size"] = size
    settings["captures"] = sorted(names)
    (folder / REFERENCE_FILE).write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8", newline="\n")
    return 0


def check(folder: Path, captures: Path) -> list[str]:
    """Les erreurs des captures de `captures` contre la référence `folder` ; vide si tout passe."""
    if not (folder / REFERENCE_FILE).is_file():
        return [f"{folder} : pas de {REFERENCE_FILE}"]
    settings = read_reference(folder)
    names = settings.get("captures", [])
    if not names:
        # Une référence sans capture rendrait la comparaison verte par vacuité.
        return [f"{folder / REFERENCE_FILE} : aucune capture de référence"]
    errors = []
    for name in names:
        if not (folder / name).is_file():
            errors.append(f"{name} : image de référence absente de {folder}")
            continue
        if not (captures / name).is_file():
            errors.append(f"{name} : capture absente de {captures}")
            continue
        pixels = load_pixels(captures / name)
        if [pixels.shape[1], pixels.shape[0]] != settings["size"]:
            errors.append(f"{name} : {pixels.shape[1]} × {pixels.shape[0]}, "
                          f"{settings['size'][0]} × {settings['size'][1]} attendus")
            continue
        try:
            result = compare(load_pixels(folder / name), block_means(pixels, settings["block"]),
                             settings["tolerance"])
        except ValueError as error:
            errors.append(f"{name} : {error}")
            continue
        verdict = "passe" if result["beyond"] <= settings["outliers"] else "REFUSÉE"
        print(f"compare_captures : {name} {verdict} — écart moyen {result['mean']:.2f}, pire bloc "
              f"{result['worst']:.2f}, {result['beyond'] * 100:.2f} % des blocs au-delà de "
              f"{settings['tolerance']:g} (admis : {settings['outliers'] * 100:g} %)")
        if result["beyond"] > settings["outliers"]:
            errors.append(f"{name} : {result['beyond'] * 100:.2f} % des blocs s'écartent de la référence de "
                          f"plus de {settings['tolerance']:g} niveaux ({settings['outliers'] * 100:g} % admis)")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reference", required=True, type=Path, help="le dossier de la référence")
    parser.add_argument("--captures", required=True, type=Path, help="le dossier des captures")
    parser.add_argument("--update", action="store_true",
                        help="réécrire la référence depuis les captures, sans comparer")
    arguments = parser.parse_args()

    if arguments.update:
        names = sorted(path.name for path in arguments.captures.glob("*.png"))
        if not names:
            print(f"compare_captures : aucune capture dans {arguments.captures}", file=sys.stderr)
            return 1
        return update(arguments.reference, arguments.captures, names)

    errors = check(arguments.reference, arguments.captures)
    for error in errors:
        print(f"compare_captures : {error}", file=sys.stderr)
    if errors:
        print("compare_captures : si l'image a changé exprès, relancer avec --update et relire les vignettes",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
