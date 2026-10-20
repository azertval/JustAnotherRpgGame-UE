"""Retire the previous main world only after its complete on-disk backup is verified."""
from pathlib import Path
import hashlib
import unreal as u
P=Path(u.Paths.project_dir()).resolve()
# The verified copy of the map being replaced, passed as -JadgBackup=<folder holding Content/...>.
import sys  # noqa: E402
B=Path(next(a.split('=',1)[1] for a in sys.argv[1:]+u.SystemLibrary.get_command_line().split() if a.startswith('-JadgBackup=')))
paths=[Path('Content/Capitale/Cartes/Capitale.umap'),Path('Content/__ExternalActors__/Capitale/Cartes/Capitale'),Path('Content/__ExternalObjects__/Capitale/Cartes/Capitale')]
count=0
for rel in paths:
 src=P/rel
 for f in ([src] if src.is_file() else src.rglob('*')):
  if not f.is_file():continue
  backup=B/f.relative_to(P)
  assert backup.is_file(),str(backup)
  assert f.stat().st_size==backup.stat().st_size,str(f)
  assert hashlib.sha256(f.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest(),str(f)
  count+=1
assert count>100,count
u.EditorLoadingAndSavingUtils.new_blank_map(False)
assert u.EditorAssetLibrary.delete_asset('/Game/Capitale/Cartes/Capitale')
print('PREVIOUS_CAPITALE_RETIRED_BACKUP_VERIFIED',count,flush=True)
