#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Prepare reversible native editor gestures for the Coliseum V2 only.
Never writes a level. Spectator supports are supplied by the architecture workshop.
"""
import argparse
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE="central-empire/capital/arenarea/arena-of-fate"
OUT=ROOT/"Tools/Assets3D/Regions"/BASE/"Production/V2"
GROUPS=[
 ("tanarean-empire",68,[("seashores",20),("bennet",42),("kolbjorn",64),("empire",90)]),
 ("allied-forces",140,[("yama",110),("stravian",130),("sindile",150),("freelands",170)]),
 (None,None,[("tsvetan",194),("taii-maku",212)]),
 ("darkall",230,[("storm-islands",230)]),
 ("arcanum",320,[("kepesh",310),("mage-tower",330)])]
def anchor(angle,width,rx=21.8,ry=14.9):
 a=math.radians(angle)
 return [round(17+rx*math.cos(a)/1.5-width/2),round(12-ry*math.sin(a)/1.5-.5)]
def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--crowd',action='store_true',help='Add the installed af-arena-crowd support to floor1.')
 parser.add_argument('--sculptures',action='store_true',help='Place the installed author-supplied Meshy models from the workshop placement contract.')
 args=parser.parse_args()
 OUT.mkdir(parents=True,exist_ok=True)
 source=json.loads((ROOT/"Source/Elements/Levels"/(BASE+".json")).read_text(encoding="utf-8"))
 active_sculptures=args.sculptures or any(t.get('piece','').startswith('meshy-') for layer in source['layers'] for t in layer.get('tiles',[]))
 sculpture_data=json.loads((OUT/'Meshy/placement-contract.json').read_text(encoding='utf-8')) if active_sculptures else None
 sculptures=sculpture_data.get('placements',[]) if sculpture_data else []
 if active_sculptures:
  if sum(v['role']=='deity' for v in sculptures)!=14 or sum(v['role']=='lion' for v in sculptures)!=2:
   raise ValueError('Expected fourteen deity placements and two guardian lion placements')
  if any(not v['piece'].startswith('meshy-') for v in sculptures):raise ValueError('Only supplied Meshy models are accepted')
 old=json.loads((ROOT/"scripts/maps/arena_fate_anchors.json").read_text(encoding="utf-8"))
 for statue in old['statues']:
  statue['name']='Socle reserve - '+statue['piece'].removeprefix('statue-')
 gestures=[]
 sidecar=ROOT/"Source/Elements/Levels"/(BASE+".editor.json")
 for note in json.loads(sidecar.read_text(encoding="utf-8")).get("notes",[]):
  if note["text"].startswith(("Alliance", "Delegation", "Délégation", "Statue", "Socle reserve", "Divinite Meshy", "Lion gardien Meshy")):
   gestures.append({"tool":"note","at":[note["column"],note["row"]],"text":""})
 allcells=[[x,y] for y in range(24) for x in range(34)]
 for name in ["statues","delegations","alliances","delegations-front","alliances-front"]+(["divinites","gardiens"] if active_sculptures else []):
  if any(l["name"]==name for l in source["layers"]):gestures.append({"layer":name,"tool":"eraser","path":allcells})
 for l in source["layers"]:
  if l["name"] in ["statues","delegations","alliances","delegations-front","alliances-front"]:
   for t in l.get("tiles",[]):gestures.append({"tool":"note","at":[t["x"],t["y"]],"text":""})
 for name,floor in [("delegations",2),("alliances",3),("delegations-front",2),("alliances-front",3)]:
  gestures.append({"tool":"layer","name":name,"kind":"decor","floor":floor})
 contract={"map":BASE,"portalReservedDegrees":[250,290],"statuesState":"pending-author-Meshy-models","statueReservations":old["statues"],"groups":[]}
 for alliance,central,members in GROUPS:
  group={"alliance":alliance,"regions":[]}
  for name,angle in members:
   front=angle>180; width=3 if name=="empire" else 2;at=[29,8] if name=="seashores" else anchor(angle,width)
   layer="delegations-front" if front else "delegations"
   entry={"piece":"banner-"+name,"angleDegrees":angle,"at":at,"footprint":[width,1],"floor":2,"logeBlender":[round(23.1*math.cos(math.radians(angle)),3),round(16*math.sin(math.radians(angle)),3),3 if front else 6]}
   group["regions"].append(entry)
   gestures.append({"layer":layer,"tool":"paint","piece":entry["piece"],"path":[at]})
   gestures.append({"tool":"note","at":at,"text":"Delegation : "+name+(" | Alliance : "+alliance if alliance else " | Independante")})
  if alliance:
   front=central>180;at=[8,18] if alliance=="darkall" else anchor(central,3,23.1,16)
   group["commonBanner"]={"piece":"banner-"+alliance,"at":at,"footprint":[3,1],"floor":3,"angleDegrees":central}
   gestures.append({"layer":"alliances-front" if front else "alliances","tool":"paint","piece":"banner-"+alliance,"path":[at]})
  contract["groups"].append(group)
 if active_sculptures:
  reservations={v['piece'].removeprefix('statue-'):v for v in old['statues']}
  for sculpture in sculptures:
   layer='divinites' if sculpture['role']=='deity' else 'gardiens'
   gestures.append({'tool':'layer','name':layer,'kind':'decor','floor':sculpture['floor']})
   gestures.append({'layer':layer,'tool':'paint','piece':sculpture['piece'],'path':[sculpture['at']]})
   at=reservations[sculpture['deity']]['at'] if sculpture['role']=='deity' else sculpture['at']
   label=('Divinite Meshy : ' if sculpture['role']=='deity' else 'Lion gardien Meshy : ')+sculpture.get('name',sculpture.get('deity',sculpture['piece']))
   gestures.append({'tool':'note','at':at,'text':label})
  contract['statuesState']='author-supplied-Meshy-models-integrated'
  contract['meshySculptures']=sculptures
 else:
  for s in old["statues"]:gestures.append({"tool":"note","at":s["at"],"text":"Socle reserve : "+s["piece"].removeprefix("statue-")+" - modele Meshy en attente de validation auteur"})
 # Monumental foreground gate: visual paving only; collision remains reserved.
 for variant in range(3):
  cells=[[x,y] for y in range(20,24) for x in range(15,19) if (x+2*y)%3==variant]
  gestures.append({"layer":"sol","tool":"paint","piece":"af-paving-"+chr(97+variant),"path":cells})
 contract["reservedPortalFloor"]={"columns":[15,18],"rows":[20,23],"collision":"preserved"}
 if args.crowd:
  gestures.append({"tool":"layer","name":"spectateurs","kind":"decor","floor":1})
  gestures.append({"layer":"spectateurs","tool":"paint","piece":"af-arena-crowd","path":[[0,0]]})
  contract["crowd"]={"piece":"af-arena-crowd","at":[0,0],"footprint":[34,24],"floor":1,"construction":"Many small transparent supports following rows; no panoramic panel."}
 # Restore every collision tile verbatim through native paint, after visual edits.
 bytype={}
 for tile in source["tiles"]:bytype.setdefault(tile["type"],[]).append([tile["x"],tile["y"]])
 for kind,cells in bytype.items():gestures.append({"layer":"collision","tool":"paint","type":kind,"path":cells})
 (OUT/"arena-banner-gestures.json").write_text(json.dumps({"format":"jadg-editor-gestures","version":1,"map":BASE,"gestures":gestures},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 (OUT/"arena-layout-contract.json").write_text(json.dumps(contract,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("V2 Coliseum gestures and sector contract prepared; no Levels file written.")
if __name__=="__main__":main()
