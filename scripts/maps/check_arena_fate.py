#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Read-only integration audit of the three editor-authored Arena of Fate maps."""
from collections import deque
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'central-empire/capital/arenarea/arena-of-fate'
SOLID = {'wall','solid','cliff','deepWater','tree','rock','fence','stall','crate','column','roof','tiers','pit','lava'}
REGIONS = {'freelands','sindile','stravian','yama','bennet','kolbjorn','empire','seashores','mage-tower','kepesh','storm-islands','taii-maku','tsvetan'}
ALLIANCES = {'allied-forces','tanarean-empire','arcanum','darkall'}

def read(mid):return json.loads((ROOT/'Source/Elements/Levels'/f'{mid}.json').read_text(encoding='utf-8'))
def pieces(d):return [t['piece'] for layer in d.get('layers',[]) for t in layer.get('tiles',[]) if 'piece' in t]+[e['piece'] for e in d.get('entities',[]) if e.get('piece')]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--arena-v2',action='store_true',help='Check 14 reserved plinths and no rejected statues; Meshy art remains pending.')
    parser.add_argument('--require-meshy',action='store_true',help='Require the fourteen supplied deity models and two lion placements.')
    parser.add_argument('--underground-v3',action='store_true',help='Expect the four author-supplied Meshy Ungods in the underground V3 assembly.')
    args=parser.parse_args()
    if args.require_meshy:args.arena_v2=True
    errors=[];report=[];art_status=None
    for mid in [BASE,BASE+'/undercroft',BASE+'/catacombs']:
        d=read(mid);tile={(t['x'],t['y']):t['type'] for t in d['tiles']}
        walk={(x,y) for y in range(d['height']) for x in range(d['width']) if tile.get((x,y),'empty') not in SOLID}
        entry=next((p for p,t in tile.items() if t=='entry'),None)
        seen={entry} if entry else set();q=deque(seen)
        while q:
            x,y=q.popleft()
            for at in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if at in walk and at not in seen:seen.add(at);q.append(at)
        if walk-seen:errors.append(f'{mid}: {len(walk-seen)} unreachable walkable cells')
        if not entry:errors.append(f'{mid}: no entry')
        for e in d.get('entities',[]):
            if e['type'] in {'portal','spawnPoint'} and (e['x'],e['y']) not in seen:errors.append(f'{mid}: inaccessible {e["id"]}')
            if e['type']=='portal' and not e.get('sealed',False):
                target=read(e['targetMap']);arrivals={v.get('name') for v in target.get('entities',[]) if v['type']=='spawnPoint'}
                if e.get('arrival') not in arrivals:errors.append(f'{mid}: missing arrival for {e["id"]}')
                if not any(v['type']=='portal' and not v.get('sealed',False) and v.get('targetMap')==mid for v in target.get('entities',[])):errors.append(f'{mid}: no return for {e["id"]}')
        used=pieces(d)
        if mid==BASE:
            region=[p[7:] for p in used if p.startswith('banner-') and p[7:] in REGIONS]
            alliance=[p[7:] for p in used if p.startswith('banner-') and p[7:] in ALLIANCES]
            if set(region)!=REGIONS or len(region)!=13:errors.append('arena: expected exactly 13 regional banners')
            if set(alliance)!=ALLIANCES or len(alliance)!=4:errors.append('arena: expected four common alliance banners')
            if args.arena_v2:
                v2=ROOT/'Tools/Assets3D/Regions'/BASE/'Production/V2'
                contract=json.loads((v2/'arena-layout-contract.json').read_text(encoding='utf-8'))
                prior=json.loads((ROOT/'scripts/maps/arena_fate_v2_baseline.json').read_text(encoding='utf-8'))
                def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')).hexdigest()
                sidecar=json.loads((ROOT/'Source/Elements/Levels'/(BASE+'.editor.json')).read_text(encoding='utf-8'))
                if digest(d['tiles'])!=prior['tilesSha256']:errors.append('arena V2: collision differs from preserved baseline')
                if digest(d['entities'])!=prior['entitiesSha256']:errors.append('arena V2: entities differ from preserved baseline')
                if any(p.startswith('statue-') for p in used):errors.append('arena V2: rejected procedural statue still placed')
                reservations=contract.get('statueReservations',[])
                sculpture_entries=contract.get('meshySculptures',[])
                note_prefix='Divinite Meshy' if sculpture_entries else 'Socle reserve'
                note_positions={(n['column'],n['row']) for n in sidecar.get('notes',[]) if n['text'].startswith(note_prefix)}
                if len(reservations)!=14 or len({tuple(v['at']) for v in reservations})!=14:errors.append('arena V2: expected 14 distinct reserved positions')
                if note_positions!={tuple(v['at']) for v in reservations}:errors.append('arena V2: reserved positions absent from editor notes')
                placed={(t.get('piece'),t['x'],t['y'],l.get('floor',0)) for l in d['layers'] for t in l.get('tiles',[])}
                for group in contract['groups']:
                    for entry in group['regions']+([group['commonBanner']] if group.get('commonBanner') else []):
                        if (entry['piece'],*entry['at'],entry['floor']) not in placed:errors.append('arena V2: misplaced '+entry['piece'])
                if contract.get('crowd'):
                    crowd=contract['crowd']
                    if (crowd['piece'],*crowd['at'],crowd['floor']) not in placed:errors.append('arena V2: missing crowd support at contracted height')
                deity_count=0;lion_count=0
                if sculpture_entries or args.require_meshy:
                    expected={v['piece'].removeprefix('statue-') for v in reservations}
                    deities=[v for v in sculpture_entries if v['role']=='deity'];lions=[v for v in sculpture_entries if v['role']=='lion']
                    if len(deities)!=14 or {v.get('deity') for v in deities}!=expected:errors.append('arena V2: expected fourteen distinct supplied deity models')
                    if len(lions)!=2:errors.append('arena V2: expected two Meshy guardian lions')
                    expected_pieces=sorted(v['piece'] for v in sculpture_entries)
                    actual_pieces=sorted(p for p in used if p.startswith('meshy-'))
                    if actual_pieces!=expected_pieces:errors.append('arena V2: supplied sculpture inventory differs from placement contract')
                    reservation_by_id={v['piece'].removeprefix('statue-'):v for v in reservations}
                    for v in sculpture_entries:
                        if (v['piece'],*v['at'],v['floor']) not in placed:errors.append('arena V2: misplaced '+v['piece'])
                        elif v['role']=='deity':deity_count+=1
                        else:lion_count+=1
                        if v['role']=='deity' and v.get('deity') in reservation_by_id:
                            reserved=reservation_by_id[v['deity']]['at'];fp=v['footprint']
                            if [v['at'][i]+(fp[i]-1)/2 for i in range(2)]!=reserved:errors.append('arena V2: deity centre misses reserved plinth '+v['deity'])
                            if v['floor']!=1 or abs(v['supportTopMetres']-3.94)>.005:errors.append('arena V2: deity support height mismatch '+v['deity'])
                        if v['role']=='lion' and (v['floor']!=2 or abs(v['supportTopMetres']-7.69)>.005):errors.append('arena V2: lion support height mismatch '+v['piece'])
                art_status={'reservedStatuePositions':14,'deliveredMeshyStatues':deity_count,'guardianLionPlacements':lion_count,'artisticApproval':'author review pending; technical integration checked' if sculpture_entries else 'pending; reserved positions do not validate missing Meshy models'}
            elif len([p for p in used if p.startswith('statue-')])!=14:errors.append('arena: expected 14 deity statues')
            if any('cult' in p or p.startswith('effigy-') for p in used):errors.append('arena: Cult or Ungod iconography above ground')
        else:
            if any('empire' in p or 'imperial' in p for p in used):errors.append(f'{mid}: imperial emblem in neutral underground zone')
        if mid.endswith('/catacombs'):
            prefix='meshy-effigy-' if args.underground_v3 else 'effigy-'
            effigies=[p for p in used if p.startswith(prefix)]
            if set(effigies)!={prefix+n for n in ['cthraxis','droggath','krynnethoth','zulvath']} or len(effigies)!=4:errors.append('catacombs: expected four distinct effigies')
            if args.underground_v3 and any(p.startswith('effigy-') for p in used):errors.append('catacombs: replaced procedural effigy remains')
        report.append({'map':mid,'walkable':len(walk),'reachable':len(seen),'pieces':len(used),'portals':sum(e['type']=='portal' for e in d.get('entities',[]))})
    print(json.dumps({'maps':report,'errors':errors,'arenaArtStatus':art_status},ensure_ascii=False,indent=2))
    return 1 if errors else 0

if __name__=='__main__':raise SystemExit(main())
