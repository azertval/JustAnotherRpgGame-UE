#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Range les maillages Meshy au maître dans `Source/Elements/Assets/Master/` et écrit leur manifeste.

Un maillage se livre au maître, sans décimation (D-53) : Nanite prend la coque telle quelle. Ce
script prend un dossier de retours Meshy (`<Famille>/Meshy_AI_<Nom>_<id>_texture.glb`), copie
chaque pièce sous un identifiant lisible, et écrit `manifest.json` — le texte que Git relit : pour
chaque pièce, sa famille, son fichier source, son empreinte SHA-256, ses triangles, ses sommets,
le nombre de ses images, et l'asset Unreal que `import_master_unreal.py` en produit.

Le nom d'une pièce est celui de sa **référence**, pas celui que Meshy a inventé : le dieu de Tanares
pour une statue, la fiche de personnage pour un PNJ, la pièce d'équipement pour une arme. La table
`references.json`, à côté du manifeste, donne pour chaque retour (`<Famille Meshy>/<Nom Meshy>`, ou
`<Famille>/<Nom>_<id Meshy>` quand deux retours portent le même nom) l'identifiant de sa référence
et d'où vient l'attribution. Un retour absent de la table arrête le script : rien n'est deviné.

Deux retours de même empreinte sont un seul maillage : le second est ignoré et nommé dans le
manifeste (`duplicates`).

Usage :
  python scripts/assetsGeneration/build_master_manifest.py D:\\Telechargement\\Assets
  python scripts/assetsGeneration/build_master_manifest.py <source> --dest Source/Elements/Assets/Master
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import struct
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DEST = ROOT / "Source" / "Elements" / "Assets" / "Master"

# Famille du dossier Meshy -> dossier du kit, dossier de contenu Unreal, préfixe d'asset.
FAMILIES = {
    "gods statues": ("Statues", "/Game/Master/Statues", "SM_Statue_"),
    "weapon": ("Weapons", "/Game/Master/Weapons", "SM_Weapon_"),
}
# Famille de la référence -> dossier du kit, dossier de contenu, préfixe. Un retour rangé dans le
# mauvais dossier Meshy (un immeuble sous NPC) suit sa référence, pas son dossier.
KIT_FAMILIES = {kit: (kit, content, prefix) for kit, content, prefix in FAMILIES.values()}
KIT_FAMILIES["Scenery"] = ("Scenery", "/Game/Master/Scenery", "SM_Scenery_")

MESHY_NAME = re.compile(r"^Meshy_AI_(?P<name>.+?)_(?P<id>\d{10})_texture(?: \(\d+\))?\.glb$", re.IGNORECASE)


def asset_name(prefix: str, reference_id: str) -> str:
    """`Statues/statue-bauron` -> `SM_Statue_Statue_Bauron` serait redondant : le préfixe de famille
    suffit, le reste est la référence en CamelCase (`SM_Statue_Bauron`, `SM_Weapon_Longbow`)."""
    leaf = reference_id.rsplit("/", 1)[1]
    family_word = prefix.split("_")[1].lower()
    parts = [part for part in leaf.split("-") if part]
    if parts and parts[0] == family_word:
        parts = parts[1:]
    return prefix + "_".join(part.capitalize() for part in parts)


def slugify(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return "_".join(part.capitalize() for part in text.split("_") if part)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def glb_stats(path: Path) -> dict:
    """Triangles, sommets, images, matières, peaux et animations lus dans le JSON du .glb."""
    with path.open("rb") as stream:
        magic, _version, _length = struct.unpack("<III", stream.read(12))
        if magic != 0x46546C67:
            raise ValueError(f"{path} : pas un GLB")
        chunk_length, _chunk_type = struct.unpack("<II", stream.read(8))
        document = json.loads(stream.read(chunk_length))
    accessors = document.get("accessors", [])
    triangles = vertices = 0
    for mesh in document.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            positions = accessors[primitive["attributes"]["POSITION"]]["count"]
            vertices += positions
            count = accessors[primitive["indices"]]["count"] if "indices" in primitive else positions
            triangles += count // 3
    return {
        "triangles": triangles,
        "vertices": vertices,
        "images": len(document.get("images", [])),
        "materials": len(document.get("materials", [])),
        "skins": len(document.get("skins", [])),
        "animations": len(document.get("animations", [])),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path, help="Dossier des retours Meshy, un sous-dossier par famille")
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST, help="Dossier du kit Master (défaut : Source/Elements/Assets/Master)")
    parser.add_argument("--no-copy", action="store_true", help="N'écrire que le manifeste, sans copier les fichiers")
    parser.add_argument("--references", type=Path, default=None,
                        help="Table des références (défaut : <dest>/references.json)")
    args = parser.parse_args(argv)

    references_path = args.references or (args.dest / "references.json")
    if not references_path.exists():
        print(f"table des références absente : {references_path}", file=sys.stderr)
        return 1
    references = json.loads(references_path.read_text(encoding="utf-8"))["references"]
    unreferenced: list[str] = []

    pieces: list[dict] = []
    duplicates: list[dict] = []
    seen: dict[str, str] = {}
    used_ids: set[str] = set()

    for family_dir in sorted(p for p in args.source.iterdir() if p.is_dir()):
        family = FAMILIES.get(family_dir.name.lower())
        if family is None:
            print(f"famille inconnue, ignorée : {family_dir.name}", file=sys.stderr)
            continue
        for source in sorted(family_dir.glob("*.glb")):
            match = MESHY_NAME.match(source.name)
            if match is None:
                print(f"nom hors convention Meshy, ignoré : {source.name}", file=sys.stderr)
                continue
            digest = sha256_of(source)
            if digest in seen:
                duplicates.append({"file": f"{family_dir.name}/{source.name}", "same_as": seen[digest]})
                continue
            meshy_name = match.group("name")
            key_with_id = f"{family_dir.name}/{meshy_name}_{match.group('id')}"
            key = f"{family_dir.name}/{meshy_name}"
            reference = references.get(key_with_id) or references.get(key)
            if reference is None:
                unreferenced.append(key_with_id)
                continue
            piece_id = reference["id"]
            ref_family = piece_id.split("/", 1)[0]
            if ref_family not in KIT_FAMILIES:
                print(f"{key_with_id} : famille inconnue dans la référence {piece_id}", file=sys.stderr)
                return 1
            kit_dir, content_path, prefix = KIT_FAMILIES[ref_family]
            if piece_id in used_ids:
                print(f"{key_with_id} : la référence {piece_id} est déjà prise", file=sys.stderr)
                return 1
            slug = piece_id.rsplit("/", 1)[1]
            used_ids.add(piece_id)
            seen[digest] = piece_id
            target = args.dest / kit_dir / f"{slug}.glb"
            if not args.no_copy:
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists() or sha256_of(target) != digest:
                    shutil.copy2(source, target)
            stats = glb_stats(source)
            pieces.append({
                "id": piece_id,
                "name": reference.get("name", slug),
                "family": kit_dir,
                "file": f"Master/{kit_dir}/{slug}.glb",
                "source": f"{family_dir.name}/{source.name}",
                "meshy_name": meshy_name,
                "meshy_id": match.group("id"),
                "basis": reference.get("basis", ""),
                "sha256": digest,
                "bytes": source.stat().st_size,
                **stats,
                # Interchange range chaque pièce dans un dossier à son nom : StaticMeshes/, Materials/,
                # Textures/. Le manifeste nomme le maillage là où l'import le pose.
                "asset": f"{content_path}/{slug}/StaticMeshes/{asset_name(prefix, piece_id)}",
            })
            print(f"{piece_id:48} {stats['triangles']:>9} tris")

    if unreferenced:
        print("retours Meshy sans référence dans " + str(references_path) + " :", file=sys.stderr)
        for key in unreferenced:
            print(f"  {key}", file=sys.stderr)
        return 1

    # Un .glb du kit que le manifeste ne cite plus (ancien nom, retour retiré) est un fichier mort.
    if not args.no_copy:
        kept = {args.dest / p["file"].removeprefix("Master/") for p in pieces}
        for stale in args.dest.rglob("*.glb"):
            if stale not in kept:
                stale.unlink()
                print(f"retiré : {stale.relative_to(args.dest)}")

    manifest = {
        "version": 1,
        "note": "Maillages Meshy au maître (D-53), nommés d'après references.json et importés par "
                "scripts/assetsGeneration/import_master_unreal.py ; aucun .glb n'est retouché, l'empreinte le vérifie.",
        "pieces": pieces,
        "duplicates": duplicates,
    }
    args.dest.mkdir(parents=True, exist_ok=True)
    manifest_path = args.dest / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    total = sum(p["triangles"] for p in pieces)
    print(f"{len(pieces)} pièces, {total} triangles, {len(duplicates)} doublon(s) -> {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
