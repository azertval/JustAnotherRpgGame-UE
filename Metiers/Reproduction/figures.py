"""Figures SVG textuelles, sans image du corpus ni dépendance tierce."""
from html import escape
import textwrap

BG='#fbf8f0'; INK='#25201a'; MUTED='#6a6152'; GRID='#d6c9a8'
COLORS=['#3f6b34','#2f7f86','#9a7420','#8a2233','#6a6152']

def text(x,y,s,size=16,fill=INK,anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}">{escape(str(s))}</text>'

def canvas(width,height,title,description,parts):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img"><title>{escape(title)}</title><desc>{escape(description)}</desc><rect width="100%" height="100%" fill="{BG}"/><g font-family="Segoe UI, sans-serif">'+''.join(parts)+'</g></svg>'

def number(x,d=1):
    return f'{x:,.{d}f}'.replace(',',' ').replace('.',',')

def bars(path,title,subtitle,labels,values,unit,reference=None,maximum=None,colors=None):
    width=1100; left=330; right=90; top=120; step=40; h=top+len(labels)*step+95
    maxv=maximum or max(max(values,default=1),reference or 0)*1.13 or 1
    plot=width-left-right
    parts=[text(28,37,title,23),text(28,68,subtitle,14,MUTED)]
    for i in range(6):
        v=maxv*i/5; x=left+plot*i/5
        parts+=[f'<path d="M{x},{top-15} V{h-65}" stroke="{GRID}"/>',text(x,top-30,number(v,0 if maxv>100 else 1),12,MUTED,'middle')]
    for i,(label,v)in enumerate(zip(labels,values)):
        y=top+i*step; fill=(colors or [COLORS[0]]*len(values))[i]
        parts+=[text(left-15,y+21,label,15,INK,'end'),f'<rect x="{left}" y="{y}" width="{max(0,v)/maxv*plot}" height="28" rx="3" fill="{fill}"/>',text(left+max(0,v)/maxv*plot+8,y+21,number(v,1)+' '+unit,14)]
    if reference is not None:
        x=left+reference/maxv*plot
        parts +=[f'<path d="M{x},{top-15} V{h-65}" stroke="{COLORS[3]}" stroke-width="2" stroke-dasharray="6 4"/>',text(x,h-37,'Référence '+number(reference,0)+' '+unit,13,COLORS[3],'middle')]
    parts+=[text(28,h-12,'Les valeurs exactes et les hypothèses figurent dans le tableau adjacent.',13,MUTED)]
    path.write_text(canvas(width,h,title,subtitle,parts),encoding='utf-8')

def stacked(path,title,subtitle,labels,series,legend):
    width=1100; left=320; top=135; step=42; plot=670; h=top+step*len(labels)+100
    parts=[text(28,35,title,23),text(28,65,subtitle,14,MUTED)]
    for j,name in enumerate(legend):
        x=28+j*310; parts += [f'<rect x="{x}" y="86" width="16" height="16" fill="{COLORS[j]}"/>',text(x+24,100,name,14)]
    for i,label in enumerate(labels):
        y=top+i*step; parts.append(text(left-15,y+21,label,15,INK,'end')); x=left
        for j,v in enumerate(series[i]):
            w=max(0,v)*plot/100
            parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="28" fill="{COLORS[j]}"/>')
            if v>8:parts.append(text(x+w/2,y+20,number(v)+' %',13,BG,'middle'))
            x+=w
    for tick in range(0,101,20):parts.append(text(left+plot*tick/100,h-40,str(tick)+' %',12,MUTED,'middle'))
    parts.append(text(28,h-12,'Chaque ligne totalise 100 %. Les catégories ne sont pas des effectifs additionnels.',13,MUTED))
    path.write_text(canvas(width,h,title,subtitle,parts),encoding='utf-8')

def lines(path,title,subtitle,series,labels,unit):
    width=1100; height=560; left=100; top=145; plotw=935; ploth=300
    maximum=max(max(v)for _,v in series)*1.15 or 1
    minimum=min(0,min(min(v)for _,v in series)); span=maximum-minimum
    Y=lambda v:top+ploth*(maximum-v)/span
    X=lambda i:left+plotw*i/11
    parts=[text(28,36,title,23),text(28,65,subtitle,14,MUTED)]
    for j,(name,values)in enumerate(series):
        parts +=[f'<path d="M{30+j*330},92 h22" stroke="{COLORS[j]}" stroke-width="3"/>',text(60+j*330,98,name,14)]
    for i in range(6):
        v=minimum+span*i/5; y=Y(v)
        parts +=[f'<path d="M{left},{y} H{left+plotw}" stroke="{GRID}"/>',text(left-12,y+4,number(v,0),12,MUTED,'end')]
    for j,(_,values)in enumerate(series):
        pts=' '.join(f'{X(i)},{Y(v)}' for i,v in enumerate(values))
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{COLORS[j]}" stroke-width="3"/>')
        for i,v in enumerate(values):parts.append(f'<circle cx="{X(i)}" cy="{Y(v)}" r="3" fill="{COLORS[j]}"/>')
    for i,s in enumerate(labels):parts.append(text(X(i),height-80,s,12,MUTED,'middle'))
    parts +=[text(28,height-35,unit+' ; M1 début été, M4 début automne, M7 début hiver, M10 début printemps.',14,MUTED)]
    path.write_text(canvas(width,height,title,subtitle,parts),encoding='utf-8')

def tree(path,title,root,children):
    width=1100; top=125; step=72; h=max(245,top+len(children)*step+45)
    parts=[text(28,36,title,23),text(28,68,'Hiérarchie proposée ; généraliste et spécialisation sont des activités terminales distinctes.',14,MUTED),f'<rect x="30" y="110" width="325" height="80" rx="8" fill="#ece4d1" stroke="{GRID}"/>']
    for i,line in enumerate(textwrap.wrap(root,30)):parts.append(text(50,141+i*23,line,18))
    for i,(name,kind,target)in enumerate(children):
        y=top+i*step
        parts +=[f'<path d="M355,150 H385 V{y+20} H415" fill="none" stroke="{COLORS[1]}"/>',f'<a href="{escape(target,quote=True)}"><rect x="415" y="{y-6}" width="650" height="57" rx="5" fill="#ece4d1" stroke="{GRID}"/>{text(435,y+16,name,16)}{text(435,y+38,kind,12,MUTED)}</a>']
    path.write_text(canvas(width,h,title,'Arbre local cliquable, une feuille par activité principale.',parts),encoding='utf-8')
