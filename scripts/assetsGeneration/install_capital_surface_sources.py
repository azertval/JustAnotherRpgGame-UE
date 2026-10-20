"""Restore the two existing Landscape surface families missing from pack install.

Only absent required texture packages are copied. Existing Unreal-resaved
textures are preserved, and source pack files are read only and hash checked.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    args=parser.parse_args();missing=[]
    lock=json.loads((ROOT/'Source/Elements/Assets/Library/capital-surface-sources.json').read_text())
    for row in lock['surfaces']:
        if not row['required']:continue
        source=Path(row['source']);target=(ROOT/row['destination']).resolve()
        if not target.is_relative_to((ROOT/'Content/Surfaces').resolve()):raise ValueError(target)
        if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=row['sha256']:
            raise RuntimeError(f'Source absent or changed: {source}')
        if target.exists():continue
        if args.check:missing.append(str(target));continue
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    if missing:raise RuntimeError('Required surface packages absent: '+', '.join(missing))
    print('Capital source surfaces available; original packs preserved.')


if __name__=='__main__':main()
