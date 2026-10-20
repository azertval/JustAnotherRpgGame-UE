#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Les illustrations des écrans de chargement, découpées dans la planche de référence de leur lieu
(demande de l'auteur du 20 octobre 2026 : « un écran de chargement qui montre que le niveau se
charge et que le jeu n'a pas planté, avec l'illustration de référence du lieu »).

La planche validée de l'Arena of Fate (`Documentation/SourceBook/references-capitale/output/
arena-of-fate-planche-v1.png`, 1536 x 1024) assemble quatre vues séparées de filets sombres : le
sable de jour, la façade et son parvis, les vestiaires, le sable de nuit. Chacune devient une
image de `Source/Elements/Assets/UI/Loading/`, que l'écran de chargement (`SJadgLoadingScreen`)
lit sur le disque ; `Source/Elements/Assets/UI/loading.json` dit lesquelles montre chaque carte.

Usage :
    python scripts/assetsGeneration/prepare_loading_screens.py
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PLATE = ROOT / "Documentation/SourceBook/references-capitale/output/arena-of-fate-planche-v1.png"
OUTPUT = ROOT / "Source/Elements/Assets/UI/Loading"
CATALOGUE = ROOT / "Source/Elements/Assets/UI/loading.json"
# Les vues de la planche, en pixels (mesurées sur ses filets : colonnes 959-969 en haut, 764-776
# en bas, lignes 617-626), rognées de 3 px pour ne garder aucun liseré.
VIEWS = {
    "arena-of-fate-jour": (8, 8, 959, 617),
    "arena-of-fate-facade": (970, 8, 1528, 617),
    "arena-of-fate-vestiaires": (8, 627, 764, 1016),
    "arena-of-fate-nuit": (776, 627, 1528, 1016),
}
INSET = 3


def main() -> None:
    plate = Image.open(PLATE).convert("RGB")
    if plate.size != (1536, 1024):
        raise SystemExit(f"{PLATE.name} : {plate.size}, la planche validée fait 1536 x 1024")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    images = []
    for name, (x0, y0, x1, y1) in VIEWS.items():
        view = plate.crop((x0 + INSET, y0 + INSET, x1 - INSET, y1 - INSET))
        path = OUTPUT / f"{name}.png"
        view.save(path, optimize=True)
        images.append(path.relative_to(ROOT / "Source/Elements/Assets").as_posix())
        print(f"{path.relative_to(ROOT).as_posix()} : {view.size[0]} x {view.size[1]}")
    catalogue = {
        "_doc": "Les écrans de chargement (prepare_loading_screens.py) : pour chaque carte de Core, le "
                "nom du lieu (clé de texte) et ses illustrations, montrées tour à tour d'un chargement à "
                "l'autre ; « default » pour une carte qui n'en a pas.",
        "maps": {"Capitale": {"place": "loading.place.capitale", "images": images}},
        "default": {"place": "loading.place.default", "images": images[:1]},
    }
    CATALOGUE.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(CATALOGUE.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
