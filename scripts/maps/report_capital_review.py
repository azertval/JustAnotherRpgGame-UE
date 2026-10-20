"""Assemble the delivered evidence; never substitutes an old capture for a new one."""
from pathlib import Path
import json
import html
import sys
import hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent))
import capital_city_layout as city
import capital_landscape_layout as layout

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Saved/Jadg/capital-landscape'
CAP=ROOT/'Saved/Captures/capital-landscape/final'


def read(path,default=None):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else default


def esc(value):return html.escape(str(value))


def table(headers,rows):
    return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(c)+'</td>' for c in r)+'</tr>' for r in rows)+'</tbody></table></div>'


def main():
    import report_capital_relief_revision
    report_capital_relief_revision.main()
    built=read(OUT/'build.json',{});geo=read(OUT/'geography-review.json',{})
    engine=read(OUT/'engine-built.json',{});refs=read(OUT/'references-80.json',[])
    heights=read(OUT/'heights-design.json',[]);nav=read(OUT/'navigation-review.json',{})
    placements=read(OUT/'urban-placement.json',{})
    audit=read(OUT/'audit-after/engine-after.json',{})
    names={r['id']:r['name'] for r in refs}
    final=[]
    for row in heights:
        key=row['id'];bounds=[b for b in engine.get('measuredBounds',[]) if b['reference']==key]
        positions=[o['position'][2] for o in placements.get('objects',[]) if o['folder']==key or o['id']==key]
        top=max((b['maximumZMetres'] for b in bounds),default=None)
        threshold=min(positions) if positions else None
        # Ground at an anchor is not a surveyed street level: do not relabel it.
        final.append({**row,'name':names[key],'thresholdPlacedMetres':threshold,
                      'thresholdStatus':'placed ensemble floor; exact door sill not individually surveyed',
                      'topMeasuredAbsoluteMetres':round(top,3) if top is not None else None,
                      'heightMeasuredAboveAnchorMetres':round(top-row['terrainMetres'],3) if top is not None else None,
                      'streetLevelStatus':'sampled separately on the approach; see streetSamplePlan and road profiles'})
    (OUT/'heights-final.json').write_text(json.dumps(final,ensure_ascii=False,indent=2),encoding='utf8')
    measures=[];measure_files=[]
    for file in sorted(CAP.rglob('mesure.json')) if CAP.exists() else []:
        d=read(file,{})
        if d.get('measures'):measure_files.append(file)
        for m in d.get('measures',[]):measures.append({**m,'shot':d.get('measureShot','ensemble'),
                         'resolution':d.get('resolution'),'gpu':d.get('gpu'),'source':str(file.relative_to(ROOT))})
    (OUT/'performance-final.json').write_text(json.dumps(measures,ensure_ascii=False,indent=2),encoding='utf8')
    walk=read(OUT/'runtime-walk.json',{})
    walk_matches=(walk.get('sceneDigest')==built.get('digest')
                  and walk.get('terrainSha256')==hashlib.sha256((OUT/'hauteurs.r16').read_bytes()).hexdigest()
                  and walk.get('routeSha256')==hashlib.sha256((OUT/'runtime-route.json').read_bytes()).hexdigest())
    level_saved=(ROOT/'Content/Maps/Levels/capital-landscape/ensemble.umap').stat().st_mtime
    checks={'geographyAssertions':geo.get('assertions',{}),'referenceCount':len(refs),
            'maxMeasuredRoadGradePercent':max((r['maximumGradePercent'] for r in geo.get('roadGrades',[])),default=None),
            'roadSamplesOver12Percent':sum(r['above12Percent'] for r in geo.get('roadGrades',[])),
            'navigationDestinations':len(nav.get('points',[])),
            'reachableDestinations':sum(p['reachable'] for p in nav.get('points',[])),
            'unrealAuditErrors':audit.get('errors',[]),'emptyMaterialSlots':audit.get('emptySlots',[]),
            'requiredMainCaptures':len(layout.SHOTS)*2,
            'missingMainCaptures':[s['id']+'-'+h+'.png' for s in layout.SHOTS for h in ('1200','2200')
                                   if not (CAP/(s['id']+'-'+h+'.png')).is_file()],
            'mainCapturesOlderThanSavedLevel':[p.name for s in layout.SHOTS for h in ('1200','2200')
                                             if (p:=CAP/(s['id']+'-'+h+'.png')).is_file() and p.stat().st_mtime<level_saved],
            'requiredCityBuffers':12,
            'missingOrOldCityBuffers':[str(p.relative_to(CAP)) for b in ('BaseColor','Roughness','WorldNormal','Metallic')
                                      for s in ('proche-palais','proche-universite','proche-arching')
                                      if not (p:=CAP/'channels'/b/(s+'-1200.png')).is_file() or p.stat().st_mtime<level_saved],
            'performanceSamples':len(measures),
            'performanceFilesOlderThanSavedLevel':[str(p.relative_to(CAP)) for p in measure_files if p.stat().st_mtime<level_saved],
            'performanceTargetFps':60,'allMeasuredViewsMeetAverageTarget':bool(measures) and all(m['fps']>=60 for m in measures),
            'artisticFidelityValidated':False,'runtimeWalkValidated':bool(walk.get('completed')) and walk_matches,
            'runtimeWalkMatchesScene':walk_matches,
            'runtimeRoutePointCount':nav.get('runtimeRoutePointCount'),'strictRuntimeRouteProjectionFailures':nav.get('strictRuntimeRouteProjectionFailures',[]),
            'unreachableRuntimeRouteIndices':nav.get('unreachableRuntimeRouteIndices',[]),
            'partialRuntimeLegs':[p['toIndex'] for p in nav.get('runtimeLegs',[]) if p.get('partial') or not p.get('valid',True)],
            'runtimeWalkReached':walk.get('pointsReached'),'runtimeWalkPlanned':walk.get('pointsPlanned'),
            'scope':'Built level, terrain checks, exterior Recast reachability and separately identified physical traversal; not a whole-city artistic or gameplay acceptance.'}
    (OUT/'verification-final.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
    parts=['''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Capitale impériale — contrôle de réalisation</title>
<style>body{margin:0;background:#eee9dd;color:#243239;font:16px/1.55 system-ui}header,main{max-width:1400px;margin:auto;padding:32px}header{border-bottom:5px solid #8e2335}h1{font-size:40px}h2{margin-top:48px}a{color:#862638}section,.card{background:#fffdf7;padding:22px;margin:20px 0;border:1px solid #d6cdbb}small{color:#6c695f}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:9px;text-align:left;border-bottom:1px solid #d6cdbb;vertical-align:top}th{background:#e7dfce;position:sticky;top:0}img{max-width:100%;display:block}.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:18px}.gallery figure{margin:0;background:#fffdf7}figcaption{padding:12px}.warn{border-left:6px solid #a56b28;padding-left:16px}details{padding:10px}button{padding:10px 18px;margin-right:10px;background:#fffdf7;border:1px solid #8e2335;cursor:pointer}.numbers{display:flex;gap:30px;flex-wrap:wrap}.numbers b{font-size:30px;display:block}code{font-size:13px}</style>
<header><small>UNREAL ENGINE 5.8 · 13–14 OCTOBRE 2026 · PROPOSITIONS RÉVERSIBLES</small><h1>La capitale impériale</h1><p>Reprise du relief intérieur, des accès et des principaux ensembles civiques. Les hauteurs restent des propositions réversibles ; la correspondance des 80 fiches ne vaut pas validation artistique individuelle.</p></header><main>''']
    parts.append('<div class="numbers">'+''.join(f'<div><b>{esc(v)}</b>{esc(k)}</div>' for k,v in [
        ('objets placés',engine.get('placedObjects','?')),('maillages distincts',engine.get('uniqueMeshes','?')),
        ('fiches reliées',len(refs)),('terrain conservé','3 024 × 2 016 m')])+'</div>')
    parts.append((ROOT/'Saved/Jadg/capital-relief-revision/review-fragment.html').read_text(encoding='utf8'))
    parts.append('<section><h2>Marche réelle dans le jeu</h2><p>'+esc(
        f"{walk.get('pointsReached','non mesuré')}/{walk.get('pointsPlanned','?')} étapes. " + ('Parcours aller simple terminé.' if walk.get('completed') and not walk.get('return') else walk.get('reason','Essai non exécuté sur cette version.'))
        )+'</p><p><a href="runtime-route.json">Parcours prévu</a> · <a href="runtime-walk.json">Échantillons physiques et résultat</a>. Vitesse normale, collision active, sans téléportation. Le résultat concerne ce parcours seulement.</p></section>')
    if not walk_matches:parts.append('<p class="warn">Le dernier essai enregistré appartient à une version antérieure du niveau ou du parcours. Il ne valide pas cette version.</p>')
    if walk_matches and (ROOT/'Saved/Jadg/capital-relief-revision/parcours-physique.png').exists():
        parts.append('<section><h2>Trace du déplacement</h2><img src="../capital-relief-revision/parcours-physique.png"><p><a href="../capital-relief-revision/walking-summary.json">Distance réellement parcourue, durée et altitudes</a>. Le tracé rouge vient des positions des pieds du personnage, pas de la ligne de navigation prévue.</p></section>')
        summary=read(ROOT/'Saved/Jadg/capital-relief-revision/walking-summary.json',{})
        if summary:
            parts.append('<p>'+esc(f"Distance mesurée : {summary['measuredTravelMetres']/1000:.2f} km ; marche : {summary['walkingSeconds']/60:.2f} min ; altitude maximale des pieds : {summary['maximumFeetMetres']:.2f} m. Les seuils individuels des bâtiments ne font pas tous partie de ce parcours.")+'</p>')
    parts.append('<section><h2>Niveaux et reproduction</h2><p><code>/Game/Maps/Levels/capital-landscape/ensemble</code><br><code>/Game/Maps/Levels/capital-landscape/material-witness</code></p><p>Un seul Landscape, 1 512 × 1 008 quads de 2 m ; eau à −2,5 m. Les sources des quartiers sont translatées par ensembles rigides, sans étirer leur architecture. Leurs anciennes rues locales ne sont pas superposées aux voies globales.</p><p>Procédure : <code>pwsh scripts/maps/review_capital_landscape.ps1</code>. Audit : <code>audit_capital_landscape.py -JadgAuditAfter</code> dans le commandlet Python Unreal. <a href="../../../Planning/referentiels/central-empire/capitale-relief-reprise-20261013.md">Notes de réalisation et limites</a>.</p></section>')
    parts.append('<section><h2>Géographie et parcours</h2><p>Droite du plan = nord géographique ; bas = est. Le repère technique reste X/Y de l’image. Water Gate conserve un accès sec ; Natural Pool est séparé ; l’aqueduc garde son propre franchissement.</p>')
    parts.append('<p><a href="geography-review.json">Mesures du relief et des profils</a> · <a href="navigation-review.json">Chemins sur les collisions Unreal</a></p>')
    tests=read(ROOT/'Saved/Jadg/capital-relief-revision/tests-summary.json',{})
    if tests:
        parts.append('<section><h2>Contrôles des sources</h2><p>'+esc(tests['date'])+' : '+esc(tests['python']['passed'])+' tests Python et '+esc(tests['unreal']['passed'])+' tests moteur réussis. Lecture du contenu sans erreur. Six tests Python ont été relancés avec un dossier temporaire explicite après une erreur de création de dossier ; les six passent.</p><p><a href="../capital-relief-revision/tests-summary.json">Bilan et journaux</a> · <a href="../capital-relief-revision/automation/index.html">Rapport des tests moteur</a></p></section>')
    if nav:
        parts.append(table(['Cible','Chemin Recast depuis le seuil'],[(p['id'],'atteignable' if p['reachable'] else 'non atteint — à corriger') for p in nav.get('points',[])]))
    parts.append('<p class="warn">La recherche de chemin extérieure ne valide pas une marche jouée, les escaliers intérieurs ni chaque seuil secondaire. Les profils suivent les axes des routes : ils ne constituent pas un contrôle de toute leur largeur.</p></section>')
    parts.append('<h2>Captures du niveau</h2><p><button onclick="hour(\'1200\')">Midi</button><button onclick="hour(\'2200\')">22 h</button>Images du jeu lancé, 1 920 × 1 080. Cliquer pour ouvrir la capture entière.</p><div class="gallery">')
    for shot in layout.SHOTS:
        if not (CAP/(shot['id']+'-1200.png')).exists():continue
        src='../../Captures/capital-landscape/final/'+shot['id']+'-1200.png'
        parts.append(f'<figure><a class="capturelink" href="{src}"><img loading="lazy" class="capture" src="{src}"></a><figcaption>{esc(shot["id"])}</figcaption></figure>')
    parts.append('</div><h2>Relief et implantation</h2><div class="gallery">')
    for name in ['heights','slopes','source-map-placements']+list(city.SECTIONS):
        found=next((p for p in OUT.rglob(name+'.*') if p.suffix in ('.png','.jpg')),None)
        if found:parts.append(f'<figure><a href="{found.relative_to(OUT).as_posix()}"><img loading="lazy" src="{found.relative_to(OUT).as_posix()}"></a><figcaption>{esc(name)}</figcaption></figure>')
    parts.append('</div><section><h2>Hauteurs</h2><p>Mètres par rapport au seuil de l’arène. Le sommet et la hauteur au-dessus du point d’implantation sont mesurés sur les bounds des maillages Unreal. Façade et toiture restent des propositions séparées, non un découpage mesuré des maillages.</p>')
    parts.append('<p>La rue est échantillonnée séparément au point d’approche indiqué dans la table détaillée. Le « seuil posé » est le plancher de l’ensemble : chaque porte n’a pas fait l’objet d’un relevé individuel.</p>')
    parts.append(table(['Fiche','Lieu','Terrain','Rue échantillonnée','Seuil posé','Façade proposée','Toiture proposée','Sommet mesuré','Hauteur mesurée'],
        [[r['id'],r['name'],r['terrainMetres'],r['streetMetres'],None if r['thresholdPlacedMetres'] is None else round(r['thresholdPlacedMetres'],2),r['facadeProposalMetres'],r['roofProposalMetres'],r['topMeasuredAbsoluteMetres'],r['heightMeasuredAboveAnchorMetres']] for r in final]))
    parts.append('<a href="heights-final.json">Table complète avec statuts</a></section><section><h2>Matériaux et canaux</h2><p>Les parents restent spécialisés : SenseiTerrain porté au Landscape ; M_Scenery et M_SceneryMasked pour les décors ; M_Eau pour quatre milieux ; M_CapitalFoliage pour la transmission des feuilles ; M_CapitalDisplacementTest réservé au témoin.</p>')
    parts.append(table(['Famille','Réglages','Contrat'],[
        ['Landscape','Size = 0,5 ; répétition proche 2 m ; normales 0,50–0,65 ; déplacement 0','B–E sont des recouvrements empilés, pas des poids normalisés'],
        ['Terre, pavés, sol humide','3 variantes × BC/N/ORM/H ; 1K / 2m ; normales 0,35–0,45','BC sRGB ; N DirectX sans inversion ; ORM R=AO/G=roughness/B=metal ; H R16F, neutre 0,5, plage 2cm'],
        ['Décors peints','Palette du témoin réutilisée ; normalScale réellement câblé dans M_Scenery','BC7 couleur et ORM ; Normalmap glTF avec inversion OpenGL, une seule fois'],
        ['Eau','Bay 0,07 ; river 0,09 ; creek 0,12 ; pool 0,08 de roughness','Single Layer Water ; maillages non Nanite ; vagues, absorption et diffusion par instance'],
        ['Végétation','Two Sided Foliage, roughness 0,86, transmission réglable','Feuilles géométriques ; pas de masque alpha ; mouvement du vent non livré'],
        ['Horizon visuel','M_CapitalHorizon / MI_Horizon, mêmes textures physiques que le Landscape','Recouvrements du bord par RGBA des sommets ; fondu sur 100 m ; sans collision ni ombre portée'],
        ['Hauteurs manquantes','Herbe A et sous-bois C : 127grey de secours','Ces couches ne possèdent pas de vraie carte Height ; le rapport ne les compte pas comme complètes'],
    ]))
    parts.append('<p><a href="audit-after/engine-after.json">Inventaire Unreal : chemins, textures, paramètres, parents et usage réel</a> · <a href="audit/packs/">Audits des packs sources</a> · <a href="../../../Source/Elements/Assets/Built/capital-surfaces/manifest.json">Provenance procédurale des nouvelles textures</a></p>')
    parts.append('<details><summary>Configuration réellement lue dans le moteur</summary><pre>'+esc(json.dumps(audit.get('runtimeConfiguration',{}),indent=2))+'</pre></details></section>')
    parts.append('<section><h2>Lecture séparée des canaux</h2><p>Couleur, rugosité, normale, métal et hauteur des trois familles de sols. Les 36 textures sont inspectées dans le <a href="../capital-relief-revision/surface-channel-review.json">relevé des canaux</a>. Les cartes de hauteur sont des données sources linéaires ; elles ne prouvent pas un déplacement géométrique actif.</p><img src="../capital-relief-revision/canaux-sources.png"><div class="gallery">')
    for buffer in ('BaseColor','Roughness','WorldNormal','Metallic'):
        for shot in ('proche-palais','proche-universite','proche-arching'):
            p=CAP/'channels'/buffer/(shot+'-1200.png')
            if p.exists():
                src='../../Captures/capital-landscape/final/channels/'+buffer+'/'+p.name
                parts.append(f'<figure><a href="{src}"><img loading="lazy" src="{src}"></a><figcaption>{esc(shot)} — {esc(buffer)}</figcaption></figure>')
    parts.append('</div></section>')
    parts.append('<h2>Scène témoin — captures historiques conservées</h2><p>Le témoin et ses textures ne sont pas modifiés dans cette reprise. Ses captures proviennent du premier passage ; les vues de la capitale et leurs canaux ci-dessus sont régénérés. Plan, pente, réponse sur volume arrondi, murs et angles, contacts sec/humide, trois pavages, bois/pierre et rive. Deux éprouvettes comparent le déplacement désactivé et une plage de 2 cm. Leur collision reste celle du maillage.</p><div class="gallery">')
    witness=CAP/'witness'
    if witness.exists():
        for p in sorted(witness.glob('*-1200.png')):
            src='../../Captures/capital-landscape/final/witness/'+p.name
            parts.append(f'<figure><a href="{src}"><img loading="lazy" src="{src}"></a><figcaption>{esc(p.stem)}</figcaption></figure>')
        for buffer in ('BaseColor','Roughness','WorldNormal','Metallic'):
            p=witness/buffer/'atelier-1200.png'
            if p.exists():
                src='../../Captures/capital-landscape/final/witness/'+buffer+'/'+p.name
                parts.append(f'<figure><a href="{src}"><img loading="lazy" src="{src}"></a><figcaption>Buffer {esc(buffer)} — témoin</figcaption></figure>')
        parts.append('<figure class="card"><p>Le déplacement est désactivé dans la capitale. Le témoin surcharge AllowTessellation à 1 pour son seul processus. <a href="../../Captures/capital-landscape/final/witness/displacement-off/deplacement-1200.png">Même cadrage avec tessellation désactivée</a>. Les deux rendus ont terminé ; leur écart reste subtil et ne valide pas encore amplitude, raccords et coût du déplacement.</p><p>Les quatre buffers couvrent cette scène témoin ; ils ne valident pas chaque matériau de quartier. Le masque Height source reste accessible dans le manifeste des textures.</p></figure>')
    parts.append('</div><section><h2>Performances observées</h2><p>Mesures de cette réalisation, caméra en rotation, 1080p, RTX 4060 Ti. La cible du projet reste 60 images/s. Ces mesures ne couvrent pas toute la capitale ni les parcours de jeu.</p>')
    if measures:
        parts.append('<p>'+esc(f"Plage mesurée : {min(m['fps'] for m in measures):.1f}–{max(m['fps'] for m in measures):.1f} images/s. {sum(m['fps']>=60 for m in measures)}/{len(measures)} mesures atteignent 60 images/s en moyenne. Le p99 rend visibles les ralentissements que cette moyenne ne décrit pas.")+'</p>')
    parts.append(table(['Vue','Heure','Images/s','Trame moyenne ms','p99 ms','GPU ms'],[[m['shot'],m['hour'],m['fps'],m['frameMs'],m['p99FrameMs'],m['gpuMs']] for m in measures]))
    parts.append('<a href="performance-final.json">Mesures et chemins des fichiers sources</a> · <a href="verification-final.json">Résultats des contrôles et limites</a></section><section><h2>Les 80 références</h2><p>Une zone de terrain, un ensemble, un quartier et un souterrain restent des objets différents. Les faits et incertitudes de chaque fiche sont conservés dans le fichier détaillé.</p>')
    parts.append(table(['Fiche','Nom','Nature','Éléments placés','État'],[[r['id'],r['name'],r['sceneKind'],len(r.get('placementIds',[])),r['status']] for r in refs]))
    parts.append('<a href="references-80.json">Correspondance détaillée, faits, relations et propositions</a></section><section class="warn"><h2>Éléments provisoires</h2><p>Les institutions secondaires réemploient encore des volumes génériques. Les silhouettes reprises du palais, de l’université, du musée, du forum et de la forge restent des propositions à affiner par lieu. La fidélité individuelle des 80 fiches, les intérieurs, les rues secondaires et le traitement détaillé de chaque métier ne sont pas achevés. Praharebaagh n’a pas de statue livrée. Sanctuary of Defiance et les cavernes sous le palais sont référencés, sans accès inventé.</p><p>RVT, World Partition/HLOD, vent de végétation, tests complets de déplacement et buffers de chaque matériau restent à éprouver. Aucune conversion générale n’a été engagée. Le témoin sec/humide est un contact comparatif, pas encore une transition continue. Le volume arrondi est une éprouvette, pas un rocher final.</p><p>Un avertissement préexistant concerne le pack SenseiTerrain : MPD_SenseiTerrain référence M_SenseiTerrain_NaniteEx dans le dossier Examples absent. Il est déjà présent dans les journaux sauvegardés avant cette reprise ; ce matériau exemple ne fait pas partie des surfaces employées ici. Le contrôle des sorties conserve les 78 orphelins préexistants de Tutorial/Sensei/NewMap, sans ajout.</p><p>Les façades, jardins et raccords demandent encore une validation artistique au cadrage du joueur. Le prolongement périphérique est un décor non parcourable ; sa transition de matière reste à affiner. La zone jouable demeure le Landscape.</p></section></main><script>function hour(h){document.querySelectorAll(".capture").forEach(i=>{i.src=i.src.replace(/-(1200|2200)[.]png/,"-"+h+".png");i.parentElement.href=i.src})}</script></html>')
    (OUT/'review.html').write_text('\n'.join(parts),encoding='utf8')
    print(OUT/'review.html')


if __name__=='__main__':main()
