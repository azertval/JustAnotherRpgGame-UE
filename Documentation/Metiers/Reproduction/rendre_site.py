"""Rend la documentation avec le moteur du projet et joint ses annexes locales."""
import argparse,importlib.util,json,shutil,sys
from pathlib import Path

def main():
    metiers=Path(__file__).resolve().parents[1];docs=metiers.parent
    args=argparse.ArgumentParser(description=__doc__);args.add_argument('--out',type=Path,default=metiers/'generated/site');opts=args.parse_args()
    out=opts.out.resolve();scope=(metiers/'generated').resolve()
    if not out.is_relative_to(scope)or out==scope:raise ValueError('Le rendu doit rester dans Metiers/generated, dans son propre sous-dossier.')
    spec=importlib.util.spec_from_file_location('docs_site',docs/'outils/build_docs_site.py');mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    if not any(k=='Metiers'for k,_ in mod.SECTIONS):mod.SECTIONS.append(('Metiers','Métiers de Tanares'))
    mod.SKIPPED_DIRS.add('Etude')
    site=mod.Site(docs,out);site.build()
    for source in metiers.rglob('*'):
        rel=source.relative_to(metiers)
        if any(p in rel.parts for p in ['generated','__pycache__'])or not source.is_file():continue
        target=out/'Metiers'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    print(json.dumps({'pages':len(site.pages),'sortie':str(out)},ensure_ascii=False))

if __name__=='__main__':main()
