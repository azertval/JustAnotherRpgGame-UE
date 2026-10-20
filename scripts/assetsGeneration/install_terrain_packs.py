#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Installe dans le projet les packs de matière de terrain, depuis leurs archives (D-52, D-60).

`Content/` n'est pas suivi : ce que le paysage de la capitale emploie d'un pack acheté ne s'y pose
pas à la main, mais par ce script, depuis l'archive telle que l'éditeur du pack la livre. Chaque
archive est reconnue par son empreinte ; un fichier déjà en place et identique n'est pas réécrit.

    python scripts/assetsGeneration/install_terrain_packs.py [--archives <dossier>] [--check]

Le dossier des archives : `--archives`, ou `JADG_PACK_ARCHIVES`, ou `D:/Telechargement`.

Ce qui s'installe :

  - **SenseiTerrain** (accès anticipé) → `/Game/SenseiTerrain` : la matière de terrain
    `M_SenseiTerrain`, ses fonctions, ses textures de variation, ses brosses de relief. Le chemin
    du pack est gardé : la matière y cherche ses fonctions.
  - **BlendMasterMaterial** → `/Game/Surfaces/GravellySand`, `/Game/Surfaces/Grass1`,
    `/Game/Surfaces/RockVkmfaek` : les surfaces d'exemple du pack (un sable graveleux, une herbe,
    une roche), que le terrain sert dans ses couches.

Les cartes d'exemple des packs et leur salle de démonstration ne s'installent pas.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "Content"
DEFAULT_ARCHIVES = "D:/Telechargement"

# Par archive : son empreinte, et pour chaque préfixe de l'archive le dossier de contenu où il va.
PACKS = [
    {
        "name": "SenseiTerrain",
        "sha256": "dda3029ba81e2442bcfb0a1475f0a550af94fb4607a481259124e1083b2f1696",
        "routes": {"SenseiTerrain/Content/SenseiTerrain/": "SenseiTerrain/"},
    },
    {
        "name": "BlendMasterMaterial",
        "sha256": "e6f3623556de7b68b26d109f43e8c25ddf97808dc47038a0ba7d23be87735f0c",
        "routes": {
            "BlendMasterMaterial/Content/Examples/Textures/gravelly_sand_": "Surfaces/GravellySand/gravelly_sand_",
            "BlendMasterMaterial/Content/Examples/Textures/grass1-": "Surfaces/Grass1/grass1-",
            "BlendMasterMaterial/Content/Examples/Textures/T_vkmfaek_": "Surfaces/RockVkmfaek/T_vkmfaek_",
        },
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def find_archive(folder: Path, pack: dict) -> Path | None:
    """L'archive d'un pack : celle du dossier dont l'empreinte est la sienne, quel que soit son nom."""
    for candidate in sorted(folder.glob(f"*{pack['name']}*.zip")):
        if sha256(candidate) == pack["sha256"]:
            return candidate
    return None


def planned(archive: zipfile.ZipFile, pack: dict) -> list[tuple[zipfile.ZipInfo, Path]]:
    """Les fichiers de contenu que l'archive pose, et où : rien hors de `Content/`, que des `.uasset`."""
    files = []
    for info in archive.infolist():
        if info.is_dir() or not info.filename.endswith(".uasset"):
            continue
        for prefix, target in pack["routes"].items():
            if info.filename.startswith(prefix):
                destination = (CONTENT / (target + info.filename[len(prefix):])).resolve()
                if not destination.is_relative_to(CONTENT.resolve()):
                    raise RuntimeError(f"{info.filename} : sort de Content/")
                files.append((info, destination))
    return files


def install(folder: Path, check: bool) -> int:
    missing = 0
    for pack in PACKS:
        path = find_archive(folder, pack)
        if path is None:
            print(f"{pack['name']} : archive absente de {folder} (empreinte {pack['sha256'][:16]}…)")
            missing += 1
            continue
        written = same = 0
        with zipfile.ZipFile(path) as archive:
            for info, destination in planned(archive, pack):
                data = archive.read(info)
                if destination.is_file() and destination.read_bytes() == data:
                    same += 1
                    continue
                if check:
                    print(f"  à installer : {destination.relative_to(ROOT).as_posix()}")
                    missing += 1
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
                written += 1
        print(f"{pack['name']} : {written} fichier(s) posé(s), {same} déjà en place ({path.name})")
    return 1 if missing else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--archives", default=os.environ.get("JADG_PACK_ARCHIVES", DEFAULT_ARCHIVES))
    parser.add_argument("--check", action="store_true", help="dit ce qui manque, sans rien écrire")
    args = parser.parse_args()
    return install(Path(args.archives), args.check)


if __name__ == "__main__":
    sys.exit(main())
