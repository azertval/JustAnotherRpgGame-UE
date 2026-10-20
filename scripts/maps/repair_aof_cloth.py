import unreal as u
import json
from pathlib import Path
E=u.EditorAssetLibrary;rows=[]
for i in [71,81,89,90,192]:
 a=E.load_asset(f'/Game/Bibliotheque/ArenaFate/Rigged/SK_AOF_{i:03d}')
 result=u.JadgArenaPhysicsBuild.build_cloth(a,400,True)
 if result.startswith('ERROR'):raise RuntimeError(result)
 if not E.save_loaded_asset(a,False):raise RuntimeError('save')
 rows.append({'id':i,'result':result});print('CLOTH_REBOUND',i,result,flush=True)
Path(u.Paths.project_saved_dir(),'Jadg/aof-extension/cloth-repair.json').write_text(json.dumps(rows,indent=2))
