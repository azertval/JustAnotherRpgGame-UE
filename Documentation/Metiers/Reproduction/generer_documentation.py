"""Transmet l'étude V3 en documentation lisible ; ne modifie pas ses valeurs."""
import csv,hashlib,json,os,re,shutil,sys
from collections import Counter,defaultdict
from pathlib import Path
from html import escape
import figures
import guides

HERE=Path(__file__).resolve().parent
OLD=HERE/'Etude'
OUT=HERE.parent
M=json.loads((OUT/'Donnees/metiers-tanares-modele.json').read_text(encoding='utf-8'))
F=json.loads((OUT/'Donnees/metiers-tanares-alimentation-v3.json').read_text(encoding='utf-8'))
B={b['id']:b for b in M['bases']};O={o['id']:o for o in M['occupations']};P={p['id']:p for p in M['profiles']}
R={r['id']:r for r in M['regions']}; RULE=M['rationale_rule_registry']
REGP={r:next((p for p in M['profiles'] if p['region']==r and p['kind'] in ['region','region_relative']),None)for r in R}
LABELS={'empire':'Empire central','freelands':'République des Freelands','bennet':'Ben’net impérial','kolbjorn':'Royaume de Kolbjörn','magocracy':'Magocratie de Mage Tower','seashores':'Seashores','sindile':'Forêt de Sindile','stravian':'Domaines stravians','storm':'Îles des Tempêtes','taiimaku':'Cités de Taii’Maku','kepesh':'Théocratie de Kepesh','tsvetan':'Tsvetan','yama':'Yama','undertanares':'Undertanares','darkall':'Darkall','mystical':'Mystical et Wasteland'}
SECTORS={'vivrier':'Production vivrière','extractif':'Ressources et extraction','alimentaire':'Transformation alimentaire','manufacture':'Artisanat et manufacture','construction':'Construction','logistique':'Transport et logistique','services':'Services quotidiens','savant':'Savoirs et transmission','magique':'Services magiques','religieux':'Cultes et rites','protection':'Protection et combat','administratif':'Administration et justice','arts':'Arts et spectacles','clandestin':'Activités clandestines'}
EVID={'atteste':'A — activité attestée','deduit':'D — activité déduite','propose':'P — activité proposée'}
BOOKS={'SB':('Tanares Sourcebook','Tanares_Sourcebook'),'PG':('Player’s Guide to Tanares','Players_Guide_to_Tanares_Version_20231218'),'MJ':('Manuel des Joueurs','Manuel-Des-Joueurs'),'BR':('Basic Rules','Basic-Rules-FR'),'CC':('Character Compendium','Character Compendium - High'),'GM':('Guide du Maître','Guide-Du-Maitre-text'),'MM':('Manuel des Monstres','Manuel-Des-Monstres')}
ENR={'bases':{},'occupations':{}}

def n(x,d=2):
    if x is None:return 'non établi'
    return f'{x:,.{d}f}'.replace(',',' ').replace('.',',')
def pct(x,d=3):return n(x,d)+' %'if x is not None else 'non établi'
def clean(s):return str(s).replace('|',' / ').replace('\r',' ').replace('\n',' ').strip()
def link(src,target,label):return '['+clean(label)+']('+os.path.relpath(OUT/target,(OUT/src).parent).replace('\\','/')+')'
def write(name,text):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.rstrip()+'\n',encoding='utf-8')
def table(head,rows):return '\n'.join(['| '+' | '.join(head)+' |','|'+'|'.join(['---']*len(head))+'|']+['| '+' | '.join(clean(v)for v in row)+' |'for row in rows])
def refs(ids,src):
    result=[]
    for ref in sorted(set(ids)):
        match=re.fullmatch(r'([A-Z]+)(\d+)',ref)
        if match and match[1]in BOOKS:result.append(link(src,'Sources/'+match[1].lower()+'.md#p-'+match[2],BOOKS[match[1]][0]+' p. '+match[2]))
    return ', '.join(result)or 'Voir les sources et la méthode du modèle.'
def nav(src,extra=None):
    xs=[link(src,'README.md','Accueil'),link(src,'arbre-metiers.md','Arbre des métiers')]+(extra or[])
    return ' · '.join(xs)+'\n\n'
def skills(rows):return table(['Savoir-faire proposé','À quoi il sert','Acquisition'],[[s['name'],s['application'],s['learning']]for s in rows])
def ruletext(rule):
    parts=[]
    for k in ['discipline','mechanism','text','scope']:
        if rule.get(k):parts.append(rule[k])
    for k in ['mechanisms','social_constraints','requirements']:
        if rule.get(k):parts.append('; '.join(rule[k]))
    return ' '.join(parts)
def justification(p,k):
    o=O[k];c=p['cell_justifications'].get(k,{})
    group=M['rationale_rules'].get(o['economic_group'],{})
    chunks=[ruletext(RULE.get(p.get('rationale_rule_ref'),{})),ruletext(RULE.get('leaf:'+k,{}))]
    calc=p.get('allocation_calculation')or{}
    if c.get('rule')=='civil':
        chunks.append('Budget civil '+n(p.get('civilian_group_budget_percent_employed',{}).get(o['economic_group'],0))+' % ; coefficient '+n(calc.get('raw_occupation_weights',{}).get(k,0),6)+' ; part de filière '+pct(calc.get('normalized_within_group_weights',{}).get(k,0)*100)+'.')
    elif c.get('rule')=='food-v3':chunks.append(M['justification_calculation_rules'].get('food-v3','Réaffectation vivrière proposée, total conservé.'))
    elif c.get('rule')=='military':chunks.append('Garnison incluse dans les résidents par convention proposée, comptée une seule fois.')
    z=c.get('zero_reason_id')
    if z:chunks.append('Zéro proposé : '+M['zero_reason_pool'].get(z,z))
    chunks.append(group.get('training',''))
    return clean(' '.join(x for x in chunks if x))

def data_and_sources():
    (OUT/'Donnees').mkdir(parents=True,exist_ok=True)
    for path in (OLD/'reports').glob('metiers-tanares-*.json'):
        shutil.copy2(path,OUT/'Donnees'/path.name)
    used=defaultdict(set)
    for o in O.values():
        for ref in o['sources']:
            mat=re.fullmatch(r'([A-Z]+)(\d+)',ref)
            if mat and mat[1]in BOOKS:used[mat[1]].add(int(mat[2]))
    for v in RULE.values():
        for ref in v.get('sources',[]):
            mat=re.fullmatch(r'([A-Z]+)(\d+)',ref)
            if mat and mat[1]in BOOKS:used[mat[1]].add(int(mat[2]))
    for code,ps in {'SB':[100,135,176,177,253,254,255,344,346],'PG':[39],'MJ':[205,217,230,231],'MM':[153,154,155,342,345],'GM':[111]}.items():used[code].update(ps)
    corpus={};source_records=[]
    sourcepath=OLD/'Tools/Worldbuilding/Tanares/Metiers/Cache'
    for code,(title,stem)in BOOKS.items():
        p=sourcepath/(stem+'.json')
        if not p.exists():continue
        pages=json.loads(p.read_text(encoding='utf-8'))
        pages=[re.sub(r'Valentin Eloy \(Order #\d+\)','',x).strip()for x in pages]
        corpus_name=code.lower()+'.json'
        dst=OUT/'Sources/Corpus'/corpus_name;dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_text(json.dumps(pages,ensure_ascii=False),encoding='utf-8');corpus[code]={'title':title,'pages':pages}
        record={'book':title,'file':corpus_name,'pdf_pages':len(pages),'raw_text_origin_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'documentary_copy_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'transformation':'Retrait du filigrane nominatif de commande dans la copie textuelle ; texte extrait conservé.'}
        source_records.append(record)
        src='Sources/'+code.lower()+'.md'
        txt='# '+title+'\n\n'+nav(src)+'Ce livre fournit les activités, règles ou contextes cités ci-dessous. Les pourcentages professionnels, la hiérarchie des métiers et les compétences proposées ne sont pas des statistiques ou des règles publiées dans ce livre.\n\n'
        txt+='Le '+link(src,'Sources/lecture-corpus.html','lecteur des extraits textuels')+' permet la recherche plein texte dans les pages PDF. La pagination imprimée des citations et l’indice PDF diffèrent ; SB/PG présentent deux pages imprimées par page PDF. Les extractions peuvent comporter des erreurs de mise en page. Le registre complet est disponible en '+link(src,'Sources/Corpus/'+corpus_name,'JSON textuel')+'.\n\n'
        for page in sorted(used[code]):
            leaves=[o for o in O.values() if code+str(page)in o['sources']]
            txt+='## Page '+str(page)+' {#p-'+str(page)+'}\n\nRéférence imprimée : '+title+', p. '+str(page)+'.\n\n'
            if leaves:txt+='Activités associées dans le catalogue : '+', '.join(link(src,'Specialisations/'+o['parent']+'/'+o['id']+'.md',o['label'])for o in leaves)+'.\n\n'
            else:txt+='Référence de contexte régional ou de mécanique du bilan. '+link(src,'../Metiers/choix-et-sources.md','La méthode et la portée des citations')+' expliquent les usages retenus.\n\n'
            if code in ['SB','PG']:txt+='Correspondance de lecture : page PDF '+str(page//2+1)+' ; double page imprimée '+str(page//2*2)+'–'+str(page//2*2+1)+'.\n\n'
        write(src,txt)
    write('Sources/registre-corpus.json',json.dumps(source_records,ensure_ascii=False,indent=2))
    payload=json.dumps(corpus,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
    viewer='''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Sources textuelles de Tanares</title><link rel="stylesheet" href="../../../Site/theme.css"><body><main><h1>Sources textuelles de Tanares</h1><p>Copies textuelles des livres fournis. Les numéros ci-dessous sont les pages PDF, pas toujours les pages imprimées des références. Aucun dessin du corpus n’est reproduit.</p><p><a href="index.html">Retour à la documentation des sources</a></p><label>Livre <select id="book"></select></label> <label>Page PDF <input id="page" type="number" min="1" value="1"></label> <button id="show">Afficher</button><p><label>Rechercher <input id="query"></label> <button id="search">Rechercher dans ce livre</button></p><div id="results"></div><h2 id="title"></h2><pre id="text"></pre></main><script id="data" type="application/json">PAYLOAD</script><script>const D=JSON.parse(document.getElementById('data').textContent),$=id=>document.getElementById(id);for(const [k,v]of Object.entries(D)){const o=document.createElement('option');o.value=k;o.textContent=v.title;$('book').appendChild(o)}function show(){const b=D[$('book').value],n=Math.max(1,Math.min(b.pages.length,Number($('page').value)||1));$('page').value=n;$('title').textContent=b.title+' — page PDF '+n;$('text').textContent=b.pages[n-1];$('page').max=b.pages.length}$('show').onclick=show;$('book').onchange=show;$('search').onclick=()=>{const b=D[$('book').value],q=$('query').value.toLocaleLowerCase(),xs=b.pages.map((s,i)=>[s,i]).filter(([s])=>q&&s.toLocaleLowerCase().includes(q));$('results').replaceChildren();for(const [s,i]of xs){const button=document.createElement('button');button.textContent='PDF '+(i+1);button.onclick=()=>{$('page').value=i+1;show()};$('results').appendChild(button)}};show();</script></body></html>'''.replace('PAYLOAD',payload)
    write('Sources/lecture-corpus.html',viewer)
    src='Sources/README.md'
    write(src,'# Sources et portée des preuves\n\n'+nav(src)+'Les liens des fiches renvoient aux **pages imprimées**. Un même passage peut attester une activité ou une ressource sans prouver une spécialisation autonome, une fréquence professionnelle ou un niveau de compétence.\n\n'+table(['Livre','Ce qu’il établit'],[[link(src,'Sources/'+k.lower()+'.md',v[0]),'Activités, institutions, règles ou contexte ; portée précise dans chaque fiche.']for k,v in BOOKS.items()])+'\n\n'+link(src,'Sources/lecture-corpus.html','Lire et rechercher les extraits')+' · '+link(src,'Sources/registre-corpus.json','Registre des extractions et empreintes')+'\n\nLes corpus textuels servent à vérifier les citations sans dépendre de l’ancien disque. Ils proviennent des références fournies ; ils ne sont pas une nouvelle édition et aucune image de livre n’est affichée. Les analyses agronomiques conservent leurs références primaires externes dans les archives et le guide alimentaire.\n')
    # Conserve l’explorateur éprouvé, mais remplace ses liens vers l’ancien disque.
    h=(OLD/'reports/metiers-tanares-exploration.html').read_text(encoding='utf-8')
    for code,source in M['sources'].items():h=h.replace(source['path'].replace('\\','/'),'Sources/'+code.lower()+'.md').replace(json.dumps(source['path'],ensure_ascii=False)[1:-1],'Sources/'+code.lower()+'.md')
    h=h.replace('D:/JustAnotherDnDGame/reports/','Donnees/').replace('Alimentation et échanges de Tanares.md','alimentation.md')
    write('explorateur.html',h)

def métier_pages():
    for b in B.values():
        src='Bases/'+b['id']+'.md';c=ENR['bases'][b['id']]
        txt='# '+b['label']+'\n\n'+nav(src)+c['purpose']+'\n\n**Métier de base proposé.** Cette famille rassemble les disciplines communes de ses branches ; elle n’ajoute pas une profession à chaque personne. Un généraliste est une feuille précise, distincte de la somme statistique de la base.\n\n'
        txt+='## Fonctions\n\n'+'\n'.join('- '+x for x in c['functions'])+'\n\n## Compétences nécessaires proposées\n\n'+skills(c['skills'])+'\n\n'+c['training']+'\n\n## Outils et chaînes de travail\n\n'+', '.join(c['tools'])+'.\n\n'+'\n'.join('- '+x for x in c['dependencies'])+'\n\n'
        fig='Figures/arbres/'+b['id']+'.svg';(OUT/fig).parent.mkdir(parents=True,exist_ok=True)
        children=[(O[k]['label'],'Généraliste'if O[k]['kind']=='generaliste'else'Spécialisation','../../Specialisations/'+b['id']+'/'+k+'.md')for k in b['children']]
        figures.tree(OUT/fig,'Branches de '+b['label'],b['label'],children)
        txt+='## Arbre de cette famille\n\n!['+clean('Base et descendants de '+b['label'])+'](../'+fig+')\n\n'+table(['Branche','Nature','Fonction distinctive'],[[link(src,'Specialisations/'+b['id']+'/'+k+'.md',O[k]['label']),'Généraliste'if O[k]['kind']=='generaliste'else'Spécialisation',ENR['occupations'][k]['distinction']]for k in b['children']])+'\n\n'
        txt+='## Implantation et parts de population\n\nLes deux colonnes changent de dénominateur. Les effectifs régionaux proposés servent à dimensionner les filières ; ils ne prouvent pas une compétence individuelle. Les valeurs relatives ne donnent aucun effectif absolu.\n\n'
        txt+=table(['Région','% des habitants','% des actifs','Portée'],[[link(src,'Regions/'+rid+'.md',LABELS[rid]),pct(p['base_percent_residents'].get(b['id'],0))if p else'non applicable',pct(p['base_percent_active'].get(b['id'],0))if p else'non applicable','scénario relatif'if p and p['population']is None else'proportion proposée'if p else'absence de dénominateur civil']for rid,p in REGP.items()])+'\n\n'
        txt+='## Choix et sources\n\n'+c['source_scope']+'\n\nLa parenté entre branches et les savoir-faire de cette fiche sont des propositions de conception. Appui des activités : '+refs(RULE['base:'+b['id']].get('sources',[]),src)+'.\n'
        write(src,txt)
    for o in O.values():
        src='Specialisations/'+o['parent']+'/'+o['id']+'.md';c=ENR['occupations'][o['id']];rule=RULE['leaf:'+o['id']]
        txt='# '+o['label']+'\n\n'+nav(src,[link(src,'Bases/'+o['parent']+'.md',B[o['parent']]['label'])])+c['purpose']+'\n\n**'+('Branche généraliste proposée'if o['kind']=='generaliste'else'Spécialisation proposée')+'** de '+B[o['parent']]['label']+'. Appui de l’activité : **'+EVID[o['occupation_evidence']]+'**. Les fonctions et compétences détaillées ci-dessous décrivent un fonctionnement proposé pour le jeu.\n\n'
        txt+='## Ce qui distingue cette branche\n\n'+c['distinction']+'\n\n## Fonctions\n\n'+'\n'.join('- '+x for x in c['functions'])+'\n\n## Compétences nécessaires proposées\n\n'+skills(c['skills'])+'\n\nCes savoir-faire complètent ceux du '+link(src,'Bases/'+o['parent']+'.md','métier de base')+'. Aucun bonus de dé, niveau de classe ou coût d’expérience n’est imposé par cette fiche.\n\n## Formation et moyens\n\n'+c['training']+'\n\nOutils et moyens : '+', '.join(c['tools'])+'.\n\n'
        req=o.get('requirements',[])+c.get('conditions',[])
        txt+='## Conditions d’exercice\n\n'+('\n'.join('- '+x for x in req)if req else'Le scénario ne fixe pas d’habilitation individuelle supplémentaire. Les ressources, autorisations et usages locaux peuvent néanmoins limiter l’exercice.')+'\n\n'
        if rule.get('availability_regions'):txt+='Filière régionale ciblée : '+', '.join(link(src,'Regions/'+r+'.md',LABELS.get(r,r))for r in rule['availability_regions'])+'. Une implantation hors de ces contextes demande un choix de conception.\n\n'
        if rule.get('availability_sites'):txt+='Sites particuliers : '+', '.join(rule['availability_sites'])+'.\n\n'
        if o.get('secondary_skills'):txt+='Savoirs transversaux utiles : '+', '.join(link(src,'Bases/'+k+'.md',B[k]['label'])for k in o['secondary_skills']if k in B)+'. Ils ne constituent pas un second métier principal.\n\n'
        txt+='## Choix et sources\n\n'+c['source_scope']+'\n\n'+refs(o['sources'],src)+'. L’appui documentaire porte sur l’activité et son contexte ; l’arbre et les compétences détaillées restent proposés.\n\n'
        positive=sorted([(p['percent_residents'].get(o['id'],0),r,p)for r,p in REGP.items()if p and p['population']is not None],reverse=True)
        txt+='## Parts régionales proposées\n\n'+table(['Région chiffrée','% des habitants','% des actifs'],[[link(src,'Regions/'+r+'.md',LABELS[r]),pct(v),pct(p['percent_active'].get(o['id'],0))]for v,r,p in positive])+'\n\nLes zéros expriment le scénario, pas une impossibilité universelle. '+link(src,'explorateur.html','L’explorateur')+' donne les villes, la contribution de chaque milieu social, les justifications et les valeurs relatives non additionnables.\n'
        write(src,txt)

def population_pages():
    for p in M['profiles']:
        src='Localites/'+p['id']+'.md';rid=p['region'];pop=p['population'];filename='Tableaux/'+p['id']+'.csv'
        rows=[]
        strata=p['social_strata']; heads=['Métier','Base','% habitants','% actifs','Effectif attendu','Appui activité','Références','Justification proposée']+[s['label']+' / % de tous habitants'for s in strata]
        for o in O.values():
            k=o['id'];rows.append([o['label'],B[o['parent']]['label'],p['percent_residents'].get(k,0),p['percent_active'].get(k,0),''if pop is None else pop*p['percent_residents'].get(k,0)/100,EVID[o['occupation_evidence']],'; '.join(o['sources']),justification(p,k)]+[p['occupation_social_joint_percent_residents'].get(k,{}).get(s['id'],0)for s in strata])
        for k,label in [('sans-metier-actif','Sans métier actif'),('hors-activite','Hors activité')]:rows.append([label,'Statut',p['percent_residents'].get(k,0),p['percent_active'].get(k,0),''if pop is None else pop*p['percent_residents'].get(k,0)/100,'P','',M['definitions'].get('active'if k=='sans-metier-actif'else'residents','')]+[p['occupation_social_joint_percent_residents'].get(k,{}).get(s['id'],0)for s in strata])
        fp=OUT/filename;fp.parent.mkdir(parents=True,exist_ok=True)
        with fp.open('w',encoding='utf-8-sig',newline='')as stream:writer=csv.writer(stream,delimiter=';');writer.writerow(heads);writer.writerows(rows)
        txt='# '+p['name']+'\n\n'+nav(src,[link(src,'Regions/'+rid+'.md',LABELS[rid])])
        txt+=('**Référence relative** : population absolue inconnue ; les pourcentages portent sur le scénario de référence, aucun habitant fictif n’est ajouté.'if pop is None else'Population retenue : **'+n(pop,0)+' habitants**, statut '+p['population_status']+'.')+'\n\n'
        txt+=ruletext(RULE.get(p.get('rationale_rule_ref'),{}))+'\n\n'
        txt+='## Population et activité\n\n'+table(['Indicateur','Valeur','Dénominateur'],[['Actifs',pct(p['activity_rate']),'tous habitants'],['Occupés',pct(p['employed_percent_residents']),'tous habitants'],['Sans emploi',pct(p['unemployment_percent_active']),'population active'],['Hors activité',pct(p['percent_residents']['hors-activite']),'tous habitants'],['Mendicité',pct(p['mendicity_percent_residents']),'tous habitants, chevauche les statuts']])+'\n\n'
        if p.get('parent'):txt+='Inclus dans '+link(src,'Localites/'+p['parent']+'.md',P[p['parent']]['name'])+'. Ne pas additionner ce profil à son parent.\n\n'
        if p.get('children'):txt+='Sous-profils inclus : '+', '.join(link(src,'Localites/'+k+'.md',P[k]['name'])for k in p['children'])+'.\n\n'
        txt+='## Différenciation sociale\n\n'+table(['Milieu','% habitants','Actifs dans ce milieu','Noblesse','Privilégié'],[[s['label'],pct(s['resident_percent']),pct(s['activity_rate']),'oui'if s['noble']is True else'non'if s['noble']is False else'non établi','oui'if s['elite']else'non']for s in strata])+'\n\n'
        txt+='Noblesse : '+p['nobility_status']+'. Les milieux privilégiés et les nobles peuvent se chevaucher ; leurs parts ne s’additionnent pas. Les enfants et personnes sans activité restent dans leur milieu.\n\n'
        txt+='## Espèces présentes\n\n'+table(['Espèce','% habitants'],[[M['species_labels_fr'].get(k,k),pct(v)]for k,v in p.get('species_percent_residents',{}).items()])+'\n\nLes marges emplois–espèces et emplois–milieux sont indépendantes dans le modèle : elles ne suffisent pas à connaître le métier de chaque espèce dans chaque strate. L’activité égale par espèce au sein d’un lieu est une hypothèse proposée.\n\n'
        best=sorted(p['base_percent_residents'].items(),key=lambda x:x[1],reverse=True)[:12]
        txt+='## Principales familles professionnelles\n\n'+table(['Base','% habitants','% actifs'],[[link(src,'Bases/'+k+'.md',B[k]['label']),pct(v),pct(p['base_percent_active'][k])]for k,v in best if v>0])+'\n\n'
        txt+='Le '+link(src,filename,'tableau complet des 267 branches et des deux statuts')+' contient les parts de chaque milieu, les références et les justifications. '+link(src,'explorateur.html','L’explorateur interactif')+' permet de filtrer les deux dénominateurs et de lire les motifs des zéros.\n\n'
        txt+='## Approvisionnement\n\n'
        food=p.get('food_v3',{})
        if pop is None:txt+='Pas de bilan territorial absolu sans total de population, terres et réseaux chiffrés. La référence alimentaire est relative.\n'
        else:
            txt+='Le besoin local et les échanges de l’arrière-pays sont inclus une seule fois dans le bilan de '+link(src,'Regions/'+rid+'.md',LABELS[rid])+'. Les transferts intérieurs déplacent les produits sans créer de nourriture.\n\n'+table(['Paramètre','Valeur'],[[k,n(food.get(k,0)/1e9,3)+' milliards kcal/an']for k in ['demand_kcal','hinterland_in_kcal','hinterland_out_kcal']if k in food])+'\n'
        write(src,txt)

def region_pages():
    for rid,r in R.items():
        src='Regions/'+rid+'.md';p=REGP[rid];x=F['regions'].get(rid)
        txt='# '+LABELS[rid]+'\n\n'+nav(src)+RULE.get('region:'+rid,{}).get('scope','Contexte regional et répartitions proposées.')+'\n\n'
        if p:txt+=link(src,'Localites/'+p['id']+'.md','Profil régional détaillé')+' : '+('population absolue inconnue, référence relative'if p['population']is None else n(p['population'],0)+' habitants au total régional')+'.\n\n'
        else:txt+='Aucun dénominateur civil vivant ordinaire ne permet ici un pourcentage professionnel territorial. Les communautés et capacités non ordinaires restent dans le registre du modèle.\n\n'
        for heading,key in [('Activités communes','common_attested'),('Activités caractéristiques','distinctive_attested'),('Usages et contraintes sociales','social_constraints')]:txt+='## '+heading+'\n\n'+'\n'.join('- '+v for v in r.get(key,[]))+'\n\n'
        txt+='## Expertises et portée\n\n'
        if r['expertise_evidence']:
            for e in r['expertise_evidence']:txt+='- '+e.get('text',e.get('domain',e.get('field','')))+(' '+e['limits']if e.get('limits')else'')+' '+refs(['SB'+str(q)for q in e.get('printed_pages',[])],src)+'.\n'
        else:txt+='Aucune expertise reconnue précise n’est établie dans les passages recensés. Cela ne signifie pas qu’aucun professionnel compétent n’y vit.\n'
        txt+='\n## Villes et communautés\n\n'+table(['Profil','Population retenue','Portée'],[[link(src,'Localites/'+q['id']+'.md',q['name']),n(q['population'],0),'référence relative'if q['population']is None else q['population_status']]for q in M['profiles']if q['region']==rid and q['id']!=rid])+'\n\n'
        txt+='## Raisonnement des répartitions\n\nLes fréquences ne proviennent pas d’un recensement de métiers : elles sont distribuées selon filières locales, disponibilité de ressources, habilitations, demande urbaine et contraintes sociales. Les emplois vivriers sont recalibrés à effectifs, espèces et strates conservés ; les raisons et les deltas sont enregistrés, y compris les zéros.\n\n'+refs(RULE.get('region:'+rid,{}).get('sources',[]),src)+'.\n\n'
        if x:
            st='Figures/stocks-'+rid+'.svg';figures.lines(OUT/st,'Stocks alimentaires — '+LABELS[rid],'Scénario central proposé, stocks de travail et réserves initiales explicites.',[('Stock de fin de mois',[a['net_end_kcal']/1e9 for a in x['stocks']['monthly']]),('Réserve initiale de sécurité',[x['stocks']['initial_emergency_stock_kcal_P']/1e9]*12)],['M'+str(i)for i in range(1,13)],'Milliards kcal')
            txt+='## Alimentation et échanges\n\n'+table(['Indicateur proposé','Résultat'],[['Besoin annuel',n(x['demand']['demand_kcal']/1e9,3)+' milliards kcal'],['Production naturelle',n(x['natural_production_kcal']/1e9,3)+' milliards kcal'],['Apport magique direct',n(x['magic_food_kcal']/1e9,3)+' milliards kcal'],['Imports livrés',n(x['imports_kcal']/1e9,3)+' milliards kcal'],['Exports chargés',n(x['exports_kcal']/1e9,3)+' milliards kcal'],['Couverture énergétique',pct(x['coverage_annual']*100)],['Surface cultivée',n(x['cropped_ha'],0)+' ha'],['Surface en rotation',n(x['rotation_ha'],0)+' ha'],['Part des lipides',pct(x['products']['fat_fraction_energy_P']*100)],['Solde du budget public',n(x['finance']['public_balance_gp_year_P'],0)+' po/an']])+'\n\n!['+clean('Stock saisonnier et seuil de sécurité de '+LABELS[rid])+'](../'+st+')\n\n'
            txt+='Les coûts, rendements, bassins d’eau et infrastructures sont des paramètres proposés. Une couverture calorique ne valide pas tous les nutriments ni l’accès marchand de chaque habitant.\n\n'
            txt+='### Crises à stocks fixes\n\n'+table(['Épreuve','Couverture annuelle','Déficit après stock initial'],[[{'bad_harvest':'Récoltes −30 %','magic_halved':'Magie divisée par deux','route_closed_90_days':'Route E7 fermée 90 jours','giants_energy_16':'Besoin géants énergie×16'}[s],pct(sc['regions'][rid]['coverage_annual']*100),n(sc['regions'][rid]['stress_unmet_kcal_after_initial_stock']/1e9,3)+' milliards kcal']for s,sc in F['stress_scenarios'].items()])+'\n\nUn déficit nul après réserve initiale ne garantit pas une deuxième année identique : les stocks peuvent s’être réduits.\n'
        write(src,txt)

def figures_and_overview():
    folder=OUT/'Figures';folder.mkdir(parents=True,exist_ok=True)
    rid=list(F['regions']);labels=[LABELS[r]for r in rid]
    figures.bars(folder/'population.svg','Populations régionales chiffrées','Effectifs approximatifs des sources ; 13 régions, parents et villes non additionnés.',labels,[F['regions'][r]['population']/1000 for r in rid],'milliers')
    figures.stacked(folder/'activite.svg','Habitants occupés, sans emploi et hors activité','Scénario proposé ; chaque barre porte sur tous les habitants.',labels,[[REGP[r]['employed_percent_residents'],REGP[r]['percent_residents']['sans-metier-actif'],REGP[r]['percent_residents']['hors-activite']]for r in rid],['Occupés','Sans emploi actifs','Hors activité'])
    figures.bars(folder/'couverture.svg','Couverture des besoins énergétiques annuels','Scénario de réseaux construits proposé ; surplus disponibles après échanges.',labels,[F['regions'][r]['coverage_annual']*100 for r in rid],'%',100)
    figures.bars(folder/'imports.svg','Dépendance énergétique aux importations','Imports livrés / besoin annuel ; pertes de transport déjà retirées.',labels,[F['regions'][r]['imports_kcal']/F['regions'][r]['demand']['demand_kcal']*100 for r in rid],'%')
    figures.bars(folder/'lipides.svg','Lipides dans le panier proposé','Indicateur de composition ; micronutriments et adéquation individuelle non validés.',labels,[F['regions'][r]['products']['fat_fraction_energy_P']*100 for r in rid],'%')
    figures.bars(folder/'vivrier.svg','Travailleurs de production vivrière','Part parmi les occupés civils ; transformation, transport et soldats exclus.',labels,[REGP[r]['food_audit']['primary_food_percent_employed_civilians']for r in rid],'%')
    counts=Counter(o['occupation_evidence']for o in O.values())
    figures.bars(folder/'preuves.svg','Appui documentaire des activités du catalogue','Le statut de l’activité ne valide ni hiérarchie ni fréquence professionnelle.',[EVID[k]for k in ['atteste','deduit','propose']],[counts[k]for k in ['atteste','deduit','propose']],'branches')
    groups=defaultdict(list)
    for b in B.values():groups[b['sector']].append(b)
    figures.tree(folder/'arbre-familles.svg','Organisation du catalogue','Métiers de Tanares',[(SECTORS[k],str(len(bs))+' bases, '+str(sum(len(b['children'])for b in bs))+' branches','../arbre-metiers.md')for k,bs in groups.items()])
    src='arbre-metiers.md';txt='# Arbre des métiers\n\n'+nav(src)+'La hiérarchie est un choix de conception : les livres attestent des activités, sans publier cet arbre. **66 bases** regroupent **234 spécialisations** et **33 branches généralistes**. Une personne exerce une seule branche principale ; les familles servent au classement et aux totaux. Les niveaux d’apprentissage et les activités secondaires traversent l’arbre.\n\n![Organisation des métiers en filières](Figures/arbre-familles.svg)\n\n'
    for sector,bs in groups.items():
        txt+='## '+SECTORS[sector]+'\n\n'
        for b in bs:
            txt+='- '+link(src,'Bases/'+b['id']+'.md',b['label'])+'\n'
            for k in b['children']:txt+='    - '+link(src,'Specialisations/'+b['id']+'/'+k+'.md',O[k]['label'])+(' — généraliste'if O[k]['kind']=='generaliste'else' — spécialisation')+'\n'
        txt+='\n'
    write(src,txt)
    src='Regions/README.md';write(src,'# Régions de Tanares\n\n'+nav(src)+'Les régions chiffrées couvrent 11 081 000 habitants connus. Undertanares et Darkall n’obtiennent que des scénarios relatifs ; Mystical garde un registre non ordinaire.\n\n'+table(['Région','Population source','Dénominateur professionnel'],[[link(src,'Regions/'+r+'.md',LABELS[r]),n(x.get('population_source'),0),'relatif'if r in ['undertanares','darkall']else'non applicable'if r=='mystical'else'habitants et actifs']for r,x in R.items()]))
    src='Tableaux/README.md';write(src,'# Tableaux complets des professions\n\n'+nav(src)+'Chaque CSV contient 267 branches, deux statuts, les deux dénominateurs, les contributions des strates sociales, les références et le raisonnement local. Les CSV sont encodés en UTF-8 avec séparateur point-virgule. Les effectifs décimaux sont attendus dans un scénario, pas un recensement d’individus.\n\n'+table(['Profil','Région','Tableau complet'],[[link(src,'Localites/'+p['id']+'.md',p['name']),LABELS[p['region']],link(src,'Tableaux/'+p['id']+'.csv','CSV') ]for p in M['profiles']]))
    src='graphiques.md';txt='# Lire les graphiques\n\n'+nav(src)+'Les graphiques utilisent les valeurs publiées, sans recalibrage. Les couleurs ne signifient pas classement des races ou des milieux. Les dénominateurs, unités et portée des hypothèses sont écrits à côté de chaque figure.\n\n'
    captions={'population':'Les 13 populations régionales approximatives des sources','activite':'Les trois statuts parmi tous habitants, propositions de répartition','vivrier':'Les producteurs primaires parmi les occupés civils, proposition','preuves':'L’appui des activités attestées, déduites et proposées','couverture':'La couverture énergétique du réseau central proposé','imports':'Les calories importées livrées rapportées au besoin annuel','lipides':'La composition en lipides des paniers proposés'}
    for fig,caption in captions.items():txt+='## '+caption+'\n\n!['+caption+'](Figures/'+fig+'.svg)\n\n'
    txt+='## Valeurs numériques des régions\n\n'+table(['Région','Population','Actifs / habitants','Vivrier / occupés civils','Couverture','Imports / besoin','Lipides / énergie'],[[link(src,'Regions/'+r+'.md',LABELS[r]),n(F['regions'][r]['population'],0),pct(REGP[r]['activity_rate']),pct(REGP[r]['food_audit']['primary_food_percent_employed_civilians']),pct(F['regions'][r]['coverage_annual']*100),pct(F['regions'][r]['imports_kcal']/F['regions'][r]['demand']['demand_kcal']*100),pct(F['regions'][r]['products']['fat_fraction_energy_P']*100)]for r in rid])+'\n\nLes graphiques mensuels des stocks figurent dans chaque région, avec la réserve de sécurité distincte du stock de saison.\n'
    write(src,txt)

def archives():
    src='Archives/README.md';txt='# Analyses détaillées et registres\n\n'+nav(src)+'Ces analyses transmettent les passages, contraintes et décisions de calcul utilisés pendant l’étude. Les revues datées décrivent le modèle au moment du contrôle ; les livrables V3 et leurs résultats finaux priment sur un audit ancien.\n\n'
    for folder in ['Métiers et populations de Tanares','Alimentation et échanges de Tanares']:
        for p in sorted((OLD/'Tools/Worldbuilding/Tanares/Metiers/Notes'/folder).glob('*')):
            if p.suffix not in ['.md','.json']:continue
            prefix='population-'if folder.startswith('Métiers')else'alimentation-'
            target='Archives/'+prefix+p.name
            if p.suffix=='.md':
                text=p.read_text(encoding='utf-8')
                # Les anciens liens vers PDF deviennent des renvois au registre du livre.
                for code,(_,stem)in BOOKS.items():text=re.sub(r'\]\(<?D:[^)\n]*'+re.escape(stem)+r'\.pdf>?\)','](../Sources/'+code.lower()+'.md)',text,flags=re.I)
                text=text.replace('Tanares_Sourcebook.pdf','Tanares_Sourcebook.pdf')
                write(target,text)
            else:shutil.copy2(p,OUT/target)
            txt+='- '+link(src,target,p.stem+' ('+('analyse'if p.suffix=='.md'else'données')+')')+'\n'
    write(src,txt)
    # Rapports complets de la dernière version, normalisés pour des liens locaux.
    for name,target in [('Métiers et populations de Tanares.md','rapport-populations.md'),('Alimentation et échanges de Tanares.md','alimentation.md')]:
        text=(OLD/'reports'/name).read_text(encoding='utf-8')
        for code,(_,stem)in BOOKS.items():text=re.sub(r'\]\(<?D:[^)\n]*'+re.escape(stem)+r'\.pdf>?\)','](Sources/'+code.lower()+'.md)',text,flags=re.I)
        text=text.replace('(metiers-tanares-exploration.html)','(explorateur.html)')
        for raw in (OLD/'reports').glob('metiers-tanares-*.json'):text=text.replace('('+raw.name+')','(Donnees/'+raw.name+')').replace('(D:/JustAnotherDnDGame/reports/'+raw.name+')','(Donnees/'+raw.name+')')
        # Liens vers les notes sous leur nom transmis.
        text=re.sub(r'\]\(<?D:/JustAnotherDnDGame/research_notes/Alimentation et échanges de Tanares/([^)>]+)>?\)',lambda mt:'](Archives/alimentation-'+mt[1]+')',text)
        text=text.replace('!','!')
        write(target,text)

def normalise_links():
    # Références de cartes décrites textuellement, sans image du corpus.
    src='Sources/cartes.md'
    write(src,'# Références cartographiques\n\n'+nav(src)+'Les corridors sont contrôlés à partir des cartes fournies et du registre de relevé. Les images du corpus ne sont pas affichées dans la documentation. Les graphiques de ce dossier représentent les données calculées, sans décalquer les cartes.\n\n## Carte mondiale {#carte-monde}\n\nOriginal : `VTT/Map - World.jpg`, 9 933 × 7 016 pixels. Relevé de la barre : 500 miles sur environ 1 520 pixels ; facteur enregistré 0,5294105 km/pixel. La lecture est incertaine d’environ 1 %, les détours et trajets d’au moins 20 %. La projection et les reliefs ne permettent pas de transformer chaque pixel en surface cultivée certaine.\n\n## Carte de Capital {#carte-capital}\n\nOriginal : `VTT/Map - Capital.jpg`, vue oblique sans échelle physique visible. Quais, entrepôts, Tourmaline Bay, Rubicund River, Grain Road et Neckoffoods indiquent des fonctions et implantations ; ils ne donnent pas des hectares mesurés.\n\n## Convention de lecture {#convention}\n\nUn trait entre centres ne prouve pas une route praticable. Les corridors, modes, distances retenues, étapes et incertitudes sont consignés dans le '+link(src,'Archives/alimentation-cartes_echanges.json','registre de relevé')+'. Les investissements de voies et flottes restent proposés.\n')
    src='Regions/penumbral.md'
    annex=M.get('penumbral_annex',{})
    write(src,'# Annexe Penumbral\n\n'+nav(src)+'Penumbral n’est pas ajouté aux 16 régions de population. Les professions psychiques et de collecte associées à cet espace gardent leurs références et conditions particulières ; aucune population absolue ni filière de fret alimentaire ordinaire n’est inventée.\n\n'+table(['Activité','Portée'],[[link(src,'Specialisations/'+o['parent']+'/'+o['id']+'.md',o['label']),'branche proposée dans son contexte spécifique']for o in O.values()if 'penumbral'in RULE['leaf:'+o['id']].get('availability_regions',[])])+'\n\nLe registre de l’annexe reste dans '+link(src,'Donnees/metiers-tanares-modele.json','le modèle intégral')+'. Les transports particuliers ne deviennent pas une réserve ou un import illimité.\n')
    for p in OUT.rglob('*.md'):
        if any(x in p.relative_to(OUT).parts for x in ['Etude','generated']):continue
        source=p.relative_to(OUT).as_posix();s=p.read_text(encoding='utf-8')
        def replace(mt):
            label,target=mt[1],mt[2].strip('<>')
            dest=None
            if target.endswith('Map - World.jpg'):dest='Sources/cartes.md#carte-monde'
            elif target.endswith('Map - Capital.jpg'):dest='Sources/cartes.md#carte-capital'
            elif target.endswith('Planning/standards/cartographie.md'):dest='Sources/cartes.md#convention'
            elif target.endswith('Métiers et populations de Tanares.md'):dest='rapport-populations.md'
            elif target.endswith('Alimentation et échanges de Tanares.md'):dest='alimentation.md'
            elif target.startswith('D:/JustAnotherDnDGame/reports/metiers-tanares-'):dest='Donnees/'+target.rsplit('/',1)[-1]
            return link(source,dest,label)if dest else mt[0]
        s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',replace,s)
        p.write_text(s,encoding='utf-8')

def main():
    proposed=json.loads((OUT/'Donnees/competences-proposees.json').read_text(encoding='utf-8'))
    ENR.update(proposed)
    assert set(ENR['bases'])==set(B)and set(ENR['occupations'])==set(O),'Catalogue incomplet'
    for rows in ENR.values():
        for c in rows.values():
            c['source_scope']=c['source_scope'].replace('Activité atteste','Activité attestée').replace('Activité deduit','Activité déduite').replace('Activité propose','Activité proposée')
    OUT.mkdir(parents=True,exist_ok=True)
    for directory in ['Sources','Archives','Figures','Reproduction']: (OUT/directory).mkdir(exist_ok=True)
    write('Donnees/competences-proposees.json',json.dumps(ENR,ensure_ascii=False,indent=2))
    métier_pages();population_pages();region_pages();figures_and_overview()
    guides.make(write,table,link,refs,M,F,B,O,P,R,LABELS,REGP,n,pct)
    normalise_links()
    print(json.dumps({'bases':len(B),'branches':len(O),'profils':len(P),'regions':len(R),'markdown':len(list(OUT.rglob('*.md'))),'svg':len(list(OUT.rglob('*.svg')))},ensure_ascii=False))

if __name__=='__main__':main()
