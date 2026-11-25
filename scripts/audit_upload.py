"""Inspect Git's publication set, including compressed evidence, without printing secrets."""
from pathlib import Path
import gzip,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
paths=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
secret=re.compile(rb'(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')
binary={'.safetensors','.png','.jpg','.jpeg','.pdf','.zip'}
bad=[]
for name in filter(None,paths):
 p=ROOT/name
 if name=='.env' or name.startswith(('.venv/','.cache/','runs/','checkpoints/')):
  bad.append((name,'private/local artifact'));continue
 if not p.is_file() or p.suffix in binary:continue
 opener=gzip.open if p.suffix=='.gz' else open
 with opener(p,'rb') as f:
  tail=b''
  while block:=f.read(524288):
   if secret.search(tail+block):bad.append((name,'possible credential'));break
   tail=(tail+block)[-512:]
print(f'Inspected {len(list(filter(None,paths)))} publishable files, including compressed text')
for name,why in bad:print('BLOCKED',name+':',why)
print('PASS: no detected private artifacts or credential patterns' if not bad else 'FAIL: review flagged files')
sys.exit(bool(bad))
