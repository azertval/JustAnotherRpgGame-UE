#!/usr/bin/env python3
"""Reproducible post-composition heights, slopes, sections and source-map overlay.
These are diagnostics, not a substitute for the Unreal captures or navigation.
"""
from pathlib import Path
import json
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import capital_landscape_layout as layout
import capital_city_layout as city
from capital_landscape import Landscape

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Saved/Jadg/capital-landscape'


def load():
    spec=json.loads((OUT/'relief.json').read_text())
    h=np.fromfile(OUT/'hauteurs.r16',dtype='<u2').reshape(spec['quads'][1]+1,spec['quads'][0]+1)
    return Landscape(tuple(spec['quads']),spec['area'],(h.astype(float)-32768)/128,{},h<32448)


def main():
    terrain=load();font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',16)
    from capital_urban_scene import distance_segment
    def finished(p):
        for name,(a,b) in layout.BRIDGES.items():
            if name=='aqueduct':continue
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
            aa=(a[0]-dx/length*10,a[1]-dy/length*10);bb=(b[0]+dx/length*10,b[1]+dy/length*10)
            distance,t=distance_segment(p,aa,bb)
            if distance*layout.METRES_PER_UNIT<4.5:return city.BRIDGE_LEVELS[name]
        return terrain.height_at(*layout.metres(p))+.10
    roads=[];bridges=[]
    for road in layout.ROADS:
        grades=[];samples=[]
        for a,b in zip(road['points'],road['points'][1:]):
            distance=math.dist(a,b)*layout.METRES_PER_UNIT;count=math.ceil(distance/2)
            last=None
            for i in range(count+1):
                t=i/count;p=(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)
                x,y=layout.metres(p)
                if not terrain.area[0]<=x<=terrain.area[2] or not terrain.area[1]<=y<=terrain.area[3]:continue
                h=finished(p)
                if h<layout.SEA_LEVEL+.4:last=None;continue
                if last is not None:grades.append(abs(h-last)/(distance/count))
                last=h;samples.append(h)
        # Allow 3 percentage points for 2m heightfield interpolation at junctions.
        # This is an explicit diagnostic tolerance, not an accessibility claim.
        limit=road.get('grade',.12)+.03
        roads.append({'id':road['id'],'minMetres':min(samples),'maxMetres':max(samples),
                      'designGradePercent':road.get('grade',.12)*100,'diagnosticLimitPercent':limit*100,
                      'aboveDesignTolerance':sum(g>limit for g in grades),
                      'maximumGradePercent':round(max(grades)*100,2),
                      'p95GradePercent':round(float(np.percentile(grades,95))*100,2),
                      'above12Percent':sum(g>.12 for g in grades)})
    for name,ends in layout.BRIDGES.items():
        bridges.append({'id':name,'deckMetres':city.BRIDGE_LEVELS[name],
                        'surveyedEndTerrain':[round(terrain.height_at(*layout.metres(p)),3) for p in ends],
                        'note':'end coordinates may stand over water; check extended dry abutments in engine'})
    gates={k:round(terrain.height_at(*layout.metres(v[:2])),3) for k,v in city.LANDMARKS.items() if k in city.GATES}
    assertions={'sameGrid':terrain.quads==(1512,1008),'arenaDatum':abs(terrain.height_at(0,0))<.01,
                'dryWaterGate':gates['X01']>layout.SEA_LEVEL+2,
                'oldtownAcrossRiver':terrain.height_at(*layout.metres((1500,418)))<layout.SEA_LEVEL,
                'naturalPoolSeparate':terrain.height_at(*layout.metres((910,437)))<layout.SEA_LEVEL,
                'noHeightClipping':bool(terrain.heights.max()<255.99),'references80':len(city.LANDMARKS)+len(city.REGIONS)==80}
    sections={}
    for name,points in city.SECTIONS.items():
        samples=[];distance=0
        for a,b in zip(points,points[1:]):
            length=math.dist(a,b)*layout.METRES_PER_UNIT
            for t in np.linspace(0,1,100,endpoint=False):
                p=(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)
                samples.append([round(distance+length*t,2),round(terrain.height_at(*layout.metres(p)),3)])
            distance+=length
        sections[name]=samples
        image=Image.new('RGB',(1400,420),'#f5f0e6');d=ImageDraw.Draw(image)
        lo=min(-16,min(p[1] for p in samples));hi=max(p[1] for p in samples)+6
        def xy(s,z):return (70+s/distance*1270,355-(z-lo)/(hi-lo)*280)  # noqa: B023
        for z in range(math.floor(lo/5)*5,math.ceil(hi/5)*5,5):
            py=xy(0,z)[1];d.line([(65,py),(1340,py)],fill='#d3cab9');d.text((12,py-8),str(z)+' m',font=font,fill='#665c4c')
        d.line([xy(0,layout.SEA_LEVEL),xy(distance,layout.SEA_LEVEL)],fill='#318c99',width=3)
        d.line([xy(*p) for p in samples],fill='#7d5140',width=3)
        d.text((65,18),name+' | terrain final encode (m), seuil Arena = 0',font=font,fill='#302e27')
        d.text((65,380),f'0 m    -    Distance parcourue en plan : {distance:.0f} m. Eau : -2,5 m. Ouvrages exclus de la ligne du terrain.',font=font,fill='#302e27')
        image.save(OUT/('section-'+name+'.png'))
    gy,gx=np.gradient(terrain.heights,2);slope=np.degrees(np.arctan(np.hypot(gx,gy)))
    h=(terrain.heights+16)/(terrain.heights.max()+16)
    for name,data in [('heights',h),('slopes',np.clip(slope/40,0,1))]:
        rgb=np.dstack([70+180*data,135-75*data,110-65*data]).astype('uint8')
        Image.fromarray(rgb).save(OUT/(name+'.png'))
    source=Image.open('D:/JustAnotherDnDGame/Documentation/SourceBook/VTT/Map - Capital.jpg')
    source.thumbnail((2000,1412));source=source.convert('RGB');d=ImageDraw.Draw(source)
    sx,sy=source.width/2000,source.height/1412
    for key,(u,v,*_) in city.LANDMARKS.items():
        if u is None or key in ('X12','X13'):continue
        x,y=u*sx,v*sy;d.ellipse((x-5,y-5,x+5,y+5),fill='#fff2ca',outline='#a22238',width=2)
        d.text((x+6,y-14),key,font=font,fill='#fff2ca',stroke_width=2,stroke_fill='#3e2430')
    source.save(OUT/'source-map-placements.jpg')
    result={'assertions':assertions,'roadGrades':roads,'gateTerrainMetres':gates,'bridges':bridges,
            'sections':sections,'limits':['Terrain gradients do not prove navigation reachability.',
                       'Source map is nonmetric; anchors are reversible survey decisions.']}
    (OUT/'geography-review.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps({'assertions':assertions,'steepRoads':[r for r in roads if r['above12Percent']]},indent=2))
    if not all(assertions.values()) or any(r['aboveDesignTolerance'] for r in roads):raise SystemExit(1)


if __name__=='__main__':main()
