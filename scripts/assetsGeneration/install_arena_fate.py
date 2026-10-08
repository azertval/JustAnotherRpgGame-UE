#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Installe les fragments GLB de l'atelier Arena of Fate et retire ses pieces remplacees.

Usage: python scripts/assetsGeneration/install_arena_fate.py --fragments A.json B.json
Le controle de chaque GLB precede toute installation. Ne modifie aucune carte.

`--only id,id` ne prend d'un fragment que les pieces nommees. Une fois les pieces en place, chacune
recoit ses cartes de matiere (`material_maps.py`, D-46) : celles de son original pour une sculpture
de l'auteur, derivees de sa couleur de base pour une piece construite par script.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import shutil
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from material_maps import enrich_folder  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SCENE = ROOT/'Source/Elements/Assets/Regions/central-empire/capital/arenarea/arena-of-fate/Scene'
WORKSHOP = ROOT/'Tools/Assets3D/Regions/central-empire/capital/arenarea/arena-of-fate/Production'

def inspect_glb(path: Path) -> dict:
    raw = path.read_bytes()
    assert len(raw) >= 20, f'{path}: truncated GLB'
    magic, version, size, chunk_size, kind = struct.unpack_from('<5I', raw)
    assert (magic, version, size, kind) == (0x46546C67, 2, len(raw), 0x4E4F534A), f'{path}: invalid GLB'
    doc = json.loads(raw[20:20+chunk_size])
    assert len(doc.get('meshes', [])) == 1, f'{path}: expected one mesh'
    assert len(doc['meshes'][0]['primitives']) == 1, f'{path}: expected one primitive'
    assert len(doc.get('materials', [])) == 1, f'{path}: expected one material'
    prim = doc['meshes'][0]['primitives'][0]
    assert prim.get('mode', 4) == 4 and 'indices' in prim, f'{path}: indexed triangles required'
    assert {'POSITION', 'NORMAL', 'TEXCOORD_0'} <= prim['attributes'].keys(), f'{path}: missing attributes'
    material = doc['materials'][0]
    assert 'baseColorTexture' in material.get('pbrMetallicRoughness', {}), f'{path}: missing albedo'
    assert all('uri' not in image and 'bufferView' in image for image in doc.get('images', [])), f'{path}: external image'
    assert all('uri' not in buffer for buffer in doc.get('buffers', [])), f'{path}: external buffer'
    triangles = doc['accessors'][prim['indices']]['count']//3
    return {'triangles': triangles, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def install(fragments: list[Path], *, preserve_existing: bool = False, remove_pieces: list[str] | None = None,
            only: set[str] | None = None) -> dict:
    entries, sources, measures = {}, {}, {}
    for fragment in fragments:
        data = json.loads(fragment.read_text(encoding='utf-8'))
        for key, entry in data['textures'].items():
            assert key.startswith('scene/arena-of-fate/'), key
            if only and key.removeprefix('scene/arena-of-fate/') not in only:
                continue
            assert key not in entries, f'duplicate piece: {key}'
            relative = Path(entry['mesh'])
            assert not relative.is_absolute() and relative.parent == Path('.'), 'flat GLB filenames required'
            source = fragment.parent/relative
            assert source.is_file(), source
            measures[key] = inspect_glb(source)
            entries[key], sources[key] = entry, source
    assert entries, 'no pieces'
    removed_keys = set(remove_pieces or [])
    assert all(key.startswith('scene/arena-of-fate/') for key in removed_keys)
    assert not (removed_keys & entries.keys()), 'cannot install and remove the same piece'
    manifest = SCENE/'manifest.json'
    old = json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {'textures': {}}
    if preserve_existing:
        for key, entry in old['textures'].items():
            if key in entries or key in removed_keys:
                continue
            source = (SCENE/entry['mesh']).resolve()
            assert source.is_relative_to(SCENE.resolve()), 'existing asset outside Scene'
            measures[key] = inspect_glb(source)
            entries[key], sources[key] = entry, source
    WORKSHOP.mkdir(parents=True, exist_ok=True)
    if not (WORKSHOP/'replaced-manifest.json').exists():
        (WORKSHOP/'replaced-manifest.json').write_text(json.dumps(old, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    SCENE.mkdir(parents=True, exist_ok=True)
    for key, source in sources.items():
        destination = SCENE/entries[key]['mesh']
        if source.resolve() != destination.resolve():
            shutil.copy2(source, destination)
    installed = {'version': 1, 'disposition': 'arena-of-fate', 'tile': [256, 159], 'storey': 3 * 256 / (1.5 * math.sqrt(2)) * math.sqrt(1 - (159 / 256)**2), 'textures': entries}
    manifest.write_text(json.dumps(installed, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    keep = {entry['mesh'] for entry in entries.values()}
    removed = []
    for item in old['textures'].values():
        name = item.get('mesh', item.get('file'))
        if not name or name in keep:
            continue
        target = (SCENE/name).resolve()
        assert target.is_relative_to(SCENE.resolve()), f'old asset outside Scene: {target}'
        if target.is_file():
            target.unlink()
            removed.append(name)
    report = {'pieces': len(entries), 'triangles_all_unique_pieces': sum(x['triangles'] for x in measures.values()),
              'bytes_all_unique_pieces': sum(x['bytes'] for x in measures.values()), 'removed': removed, 'measurements': measures}
    (WORKSHOP/'installation-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    # Les cartes de matiere (D-46), sur tout le dossier : les originaux viennent des releves d'import.
    reports = [path for path in (WORKSHOP/'V2/Sculptures/sculptures-measurements.json',
                                 WORKSHOP/'V3/Sculptures/sculptures-measurements.json') if path.is_file()]
    report['materialMaps'] = len(enrich_folder(SCENE, reports=reports))
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fragments', type=Path, nargs='+', required=True)
    parser.add_argument('--preserve-existing', action='store_true', help='Merge a single-card update without removing other installed pieces')
    parser.add_argument('--remove-piece', action='append', default=[], help='Explicit full piece id to remove when merging')
    parser.add_argument('--only', default='', help='Comma-separated piece ids to take from the fragments')
    args = parser.parse_args()
    report = install(args.fragments, preserve_existing=args.preserve_existing, remove_pieces=args.remove_piece,
                     only={name for name in args.only.split(',') if name} or None)
    print(json.dumps({key: value for key, value in report.items() if key != 'measurements'}, ensure_ascii=False, indent=2))
