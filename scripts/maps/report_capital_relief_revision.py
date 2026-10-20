"""Compare the revised single Landscape with its preserved initial realization.

No old screenshot, performance sample or walk report is used as a new result.
"""
from pathlib import Path
import json
import math
import html
import hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import capital_city_layout as city
import capital_landscape_layout as layout
from capital_landscape import Grid, Landscape
from review_capital_geography import load

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Saved/Jadg/capital-relief-revision'
CURRENT=ROOT/'Saved/Jadg/capital-landscape'
BEFORE=OUT/'before/Saved/Jadg/capital-landscape'
CAP=ROOT/'Saved/Captures/capital-landscape/final'


def surface_review():
    """Read each physical channel independently; Height is source data, not proof of tessellation."""
    source=ROOT/'Source/Elements/Assets/Built/capital-surfaces'
    manifest=json.loads((source/'manifest.json').read_text())
    records=[]
    for t in manifest['textures']:
        im=Image.open(source/t['file']);a=np.asarray(im).astype(float)
        scale=65535 if im.mode in ('I;16','I') else 255
        a/=scale
        records.append({'name':t['name'],'mode':im.mode,'size':list(im.size),'role':t['role'],
                        'min':float(a.min()),'max':float(a.max()),'srgb':t['srgb'],
                        'normalConvention':t['normalConvention'],'geometryDisplacement':t['geometryDisplacement']})
    panel=Image.new('RGB',(1230,820),'#f4efe5');d=ImageDraw.Draw(panel)
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',19)
    d.text((20,12),'Canaux sources : couleur / rugosité / normale / métal / hauteur',font=font,fill='#243239')
    for row,family in enumerate(('soil','paving','wet-soil')):
        textures={t['role']:Image.open(source/t['file']) for t in manifest['textures'] if t['family']==family and t['variant']==0}
        orm=textures['ORM'].convert('RGB')
        h=np.asarray(textures['H']).astype(float)/65535
        channels=[textures['BC'],orm.getchannel('G'),textures['N'],orm.getchannel('B'),Image.fromarray((h*255).astype('uint8'))]
        d.text((20,55+row*245),family+' · variante 0 · motif de 2 m',font=font,fill='#243239')
        for col,im in enumerate(channels):panel.paste(im.convert('RGB').resize((210,210)),(20+col*243,84+row*245))
    d.text((20,798),'Height en niveaux linéaires : aucune amplification visuelle, aucun déplacement géométrique dans la capitale.',font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',15),fill='#243239')
    panel.save(OUT/'canaux-sources.png')
    (OUT/'surface-channel-review.json').write_text(json.dumps(records,indent=2),encoding='utf8')


def walking_review(terrain):
    path=CURRENT/'runtime-walk.json'
    if not path.exists():return
    walk=json.loads(path.read_text(encoding='utf-8-sig'))
    route=json.loads((CURRENT/'runtime-route.json').read_text())
    if walk.get('routeSha256')!=hashlib.sha256((CURRENT/'runtime-route.json').read_bytes()).hexdigest():return
    samples=walk.get('samples',[])
    if not samples:return
    axes=route['unrealAxes']
    actual=[]
    for s in samples:
        glb=[0.,0.,0.]
        for k,(i,sign) in enumerate(axes):glb[i]=sign*s['feetCm'][k]/100
        actual.append([glb[0],glb[2],glb[1]])
    values=np.clip((terrain.heights+5)/85,0,1)
    rgb=np.dstack([52+185*values,125-32*values,160-117*values]).astype('uint8')
    canvas=Image.new('RGB',(1540,1120),'#f4efe5');canvas.paste(Image.fromarray(rgb).resize((1500,1000)),(20,80))
    d=ImageDraw.Draw(canvas);font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',19)
    x0,y0,x1,y1=terrain.area
    def pixel(p):return 20+(p[0]-x0)/(x1-x0)*1500,80+(p[1]-y0)/(y1-y0)*1000
    d.line([pixel(p) for p in route['pointsMetres']],fill='#f8f0d9',width=5)
    d.line([pixel(p) for p in actual],fill='#e6534a',width=3)
    d.text((20,12),'Parcours physique : crème = prévu ; rouge = positions des pieds enregistrées dans le jeu',font=font,fill='#243239')
    d.text((20,43),f"{walk.get('pointsReached')}/{walk.get('pointsPlanned')} étapes atteintes · collision active · vitesse nominale 3 m/s",font=font,fill='#243239')
    canvas.save(OUT/'parcours-physique.png')
    distance=sum(math.dist(a,b) for a,b in zip(actual,actual[1:]))
    reached=walk.get('reached',[])
    xy_error=max((math.dist(s['feetCm'][:2],s['targetCm'][:2]) for s in reached),default=None)
    z_error=max((abs(s['feetCm'][2]-s['targetCm'][2]) for s in reached),default=None)
    result={'completed':walk['completed'],'sampleCount':len(actual),'measuredTravelMetres':distance,
            'plannedLengthMetres':route['lengthMetres'],'elapsedSeconds':walk['seconds'],
            'walkingSeconds':samples[-1]['seconds']-samples[0]['seconds'],
            'startupSeconds':samples[0]['seconds'],
            'maximumReachedHorizontalErrorCm':xy_error,'maximumReachedVerticalErrorCm':z_error,
            'minimumFeetMetres':min(p[2] for p in actual),'maximumFeetMetres':max(p[2] for p in actual),
            'scope':'One exterior route. Positions are sampled at runtime; no whole-city acceptance inferred.'}
    (OUT/'walking-summary.json').write_text(json.dumps(result,indent=2),encoding='utf8')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    surface_review()
    paths=[*('scripts/maps/'+n for n in ('capital_landscape.py','capital_landscape_layout.py','capital_city_layout.py',
            'capital_urban_terrain.py','capital_urban_scene.py','capital_surface_materials.py','build_capital_landscape_scene.py',
            'review_capital_geography.py','review_capital_navigation.py','review_capital_landscape.ps1','review_capital_access.py',
            'review_capital_walk_failure.py','audit_capital_landscape.py',
            'report_capital_relief_revision.py','report_capital_review.py','capital_comparison_shots.json')),
            'scripts/assetsGeneration/build_capital_urban_assets.py','scripts/assetsGeneration/arena_geometry.py',
            'Source/JustAnotherRpgGame/Scene/JadgSceneBuild.cpp','Source/JustAnotherRpgGame/Scene/JadgSceneBuild.h',
            'Planning/referentiels/central-empire/capitale-landscape-20261013.md',
            'Planning/referentiels/central-empire/capitale-relief-reprise-20261013.md']
    sources=[]
    for relative in paths:
        old=OUT/'before'/relative;new=ROOT/relative
        sources.append({'path':relative,'beforeSha256':hashlib.sha256(old.read_bytes()).hexdigest() if old.exists() else None,
                        'afterSha256':hashlib.sha256(new.read_bytes()).hexdigest()})
    (OUT/'sources-revised.json').write_text(json.dumps(sources,indent=2),encoding='utf8')
    now=load();grid=Grid()
    walking_review(now)
    spec=json.loads((BEFORE/'relief.json').read_text())
    raw=np.fromfile(BEFORE/'hauteurs.r16',dtype='<u2').reshape(grid.shape)
    before=Landscape(tuple(spec['quads']),spec['area'],(raw.astype(float)-32768)/128,{},raw<32448)
    records=[]
    for key,(name,poly,_,_) in city.REGIONS.items():
        mask=(grid.polygons([poly])>.5)&(now.heights>layout.SEA_LEVEL)
        row={'id':key,'name':name}
        for tag,terrain in [('before',before),('after',now)]:
            vals=terrain.heights[mask];gy,gx=np.gradient(terrain.heights,2)
            slopes=np.degrees(np.arctan(np.hypot(gx,gy)))[mask]
            row[tag]={'minimum':float(vals.min()),'maximum':float(vals.max()),
                      'p10':float(np.percentile(vals,10)),'p50':float(np.median(vals)),
                      'p90':float(np.percentile(vals,90)),
                      'reliefP90P10':float(np.percentile(vals,90)-np.percentile(vals,10)),
                      'medianSlopeDegrees':float(np.median(slopes)),
                      'p90SlopeDegrees':float(np.percentile(slopes,90))}
        records.append(row)
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',19)
    small=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',15)
    # Same scales, legend and geographic labels in both cartographic panels.
    for name in ('hauteurs','pentes'):
        panel=Image.new('RGB',(1660,780),'#f4efe5');draw=ImageDraw.Draw(panel)
        draw.text((30,15),f'{name.capitalize()} — avant / après — même emprise et même échelle',fill='#272f35',font=font)
        for idx,(tag,t) in enumerate([('Avant',before),('Après',now)]):
            if name=='hauteurs':values=np.clip((t.heights+5)/85,0,1);legend='Échelle : −5 m (bleu) → 80 m (ocre) ; crêtes >80 m saturées'
            else:
                gy,gx=np.gradient(t.heights,2);values=np.clip(np.degrees(np.arctan(np.hypot(gx,gy)))/35,0,1)
                legend='Échelle : 0° (bleu) → 35° (ocre) ; pentes supérieures saturées'
            rgb=np.dstack([52+185*values,125-32*values,160-117*values]).astype('uint8')
            im=Image.fromarray(rgb).resize((795,530));panel.paste(im,(25+idx*815,80))
            draw.text((25+idx*815,53),tag,fill='#272f35',font=font)
            for _key,(district,poly,_,_) in city.REGIONS.items():
                u=sum(p[0] for p in poly)/len(poly);v=sum(p[1] for p in poly)/len(poly)
                px,py=grid.pixel((u,v));x=25+idx*815+px/grid.shape[1]*795;y=80+py/grid.shape[0]*530
                draw.text((x,y),district,fill='white',font=small,stroke_width=2,stroke_fill='#283138')
        draw.text((25,635),legend,fill='#272f35',font=font)
        draw.text((25,676),'Orientation : haut = ouest géographique ; droite = nord. Eau = −2,5 m ; seuil Arena = 0 m.',fill='#272f35',font=font)
        draw.text((25,717),'Carte de contrôle de terrain ; elle ne remplace ni les collisions ni une marche jouée.',fill='#272f35',font=font)
        panel.save(OUT/(name+'-comparaison.png'))
    sections=[]
    for name,points in city.SECTIONS.items():
        samples=[];length=0;marks=[]
        for a,b in zip(points,points[1:]):
            segment=math.dist(a,b)*layout.METRES_PER_UNIT;marks.append((length,a))
            for t in np.linspace(0,1,110,endpoint=False):
                p=(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t);x,y=layout.metres(p)
                samples.append([length+segment*t,before.height_at(x,y),now.height_at(x,y)])
            length+=segment
        marks.append((length,points[-1]))
        image=Image.new('RGB',(1500,530),'#f4efe5');d=ImageDraw.Draw(image)
        lo=-17;hi=max(max(p[1:]) for p in samples)+10
        def xy(s,z):return 65+s/length*1380,425-(z-lo)/(hi-lo)*335  # noqa: B023
        for z in range(-10,math.ceil(hi/10)*10,10):
            y=xy(0,z)[1];d.line([(65,y),(1445,y)],fill='#d7cdbb');d.text((8,y-9),f'{z} m',fill='#514c43',font=small)
        for index,colour in [(1,'#8b8e91'),(2,'#9d3b3c')]:d.line([xy(p[0],p[index]) for p in samples],fill=colour,width=3)
        d.line([xy(0,-2.5),xy(length,-2.5)],fill='#318eaf',width=2)
        for s,p in marks:
            x,y=xy(s,lo);d.line([(x,90),(x,425)],fill='#ddd3c1')
            district=city.district_for(*p)
            label=city.REGIONS[district][0] if district else 'rive/eau'
            label_width=d.textlength(label,font=small)
            d.text((min(x,1480-label_width),440),label,fill='#514c43',font=small)
        d.text((65,15),name.replace('-',' '),font=font,fill='#243239')
        d.text((65,47),'Gris : avant · Bourgogne : après · Bleu : eau. Altitudes absolues, ouvrages exclus.',font=font,fill='#243239')
        d.text((65,485),f'Distance en plan : {length:.0f} m. Échelles horizontale et verticale différentes ; lire les altitudes.',font=small,fill='#243239')
        image.save(OUT/f'coupe-{name}.png');sections.append({'name':name,'lengthMetres':length,'samples':samples})
    walkpath=CURRENT/'runtime-walk.json'
    walk=json.loads(walkpath.read_text()) if walkpath.exists() else None
    result={'districts':records,'sections':sections,'runtimeWalk':walk,
            'provenance':'Book/map give uses and neighbors, no metric elevations. Heights are reversible art proposals.',
            'beforeSnapshot':'Saved/Jadg/capital-relief-revision/before',
            'comparisonCameras':'scripts/maps/capital_comparison_shots.json',
            'limits':['Secondary institutions retain generic assemblies','Underground entrances not invented',
                      'Visual horizon skirt has no collision; only the single Landscape is gameplay terrain',
                      '12–20% route targets are design choices by use, not universal accessibility limits']}
    (OUT/'relief-revision.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    def esc(s):
        return html.escape(str(s))
    blocks=['<section><h2>Reprise du relief — comparaison avec la version sauvegardée</h2>',
            '<p><button onclick="hour(\'1200\')">Comparer à midi</button><button onclick="hour(\'2200\')">Comparer à 22 h</button></p>',
            '<p>Les deux rendus emploient les mêmes positions de caméra, à midi et à 22 h. Les vues « proche » suivent les nouveaux niveaux de rue. Les anciennes vues proches peuvent être masquées par les nouvelles collines : leur caméra a été conservée pour la comparaison.</p>']
    for shot in ['ensemble','riviere','market-gate-old-bridge','palais','scholarnest-dweomer']:
        blocks.append('<h3>'+esc(shot)+'</h3><div class="gallery">')
        for prefix,label in [('../capital-relief-revision/before/Saved/Captures/capital-landscape/final/','Avant'),('../../Captures/capital-landscape/final/','Après')]:
            src=prefix+shot+'-1200.png';blocks.append(f'<figure><a href="{src}"><img loading="lazy" class="capture" src="{src}"></a><figcaption>{label}</figcaption></figure>')
        blocks.append('</div>')
    blocks.append('<details><summary>Les 16 cadrages historiques aux deux heures</summary><table><tr><th>Cadrage</th><th>Avant midi</th><th>Après midi</th><th>Avant 22 h</th><th>Après 22 h</th></tr>')
    for shot in json.loads((ROOT/'scripts/maps/capital_comparison_shots.json').read_text()):
        blocks.append('<tr><td>'+esc(shot['id'])+'</td>')
        for hour in ('1200','2200'):
            for prefix in ('../capital-relief-revision/before/Saved/Captures/capital-landscape/final/','../../Captures/capital-landscape/final/'):
                blocks.append('<td><a href="'+prefix+shot['id']+'-'+hour+'.png">Ouvrir</a></td>')
        blocks.append('</tr>')
    blocks.append('</table><p>La caméra historique joueur-universite est masquée par la colline révisée. La vue proche-universite montre le nouveau parvis et la cour sans modifier cette comparaison.</p></details>')
    blocks.append('<div class="gallery">')
    for name in ['hauteurs-comparaison','pentes-comparaison']+['coupe-'+k for k in city.SECTIONS]:
        src='../capital-relief-revision/'+name+'.png';blocks.append(f'<figure><a href="{src}"><img loading="lazy" src="{src}"></a></figure>')
    blocks.append('</div><h3>Relief réellement présent dans les quartiers</h3><table><tr><th>Quartier</th><th>Avant P10–P90 (m)</th><th>Après P10–P90 (m)</th><th>Pente médiane après</th></tr>')
    for r in records:blocks.append(f'<tr><td>{esc(r["name"])}</td><td>{r["before"]["p10"]:.1f}–{r["before"]["p90"]:.1f}</td><td>{r["after"]["p10"]:.1f}–{r["after"]["p90"]:.1f}</td><td>{r["after"]["medianSlopeDegrees"]:.1f}°</td></tr>')
    blocks.append('</table><p>Les percentiles portent sur toute la surface de chaque quartier, sans les sommets périphériques. <a href="../capital-relief-revision/relief-revision.json">Données comparatives complètes</a>.</p></section>')
    (OUT/'review-fragment.html').write_text(''.join(blocks),encoding='utf8')
    print(json.dumps([{k:v for k,v in r.items() if k in ('id','name')}|{'before':round(r['before']['reliefP90P10'],1),'after':round(r['after']['reliefP90P10'],1)} for r in records],ensure_ascii=False))


if __name__=='__main__':main()
