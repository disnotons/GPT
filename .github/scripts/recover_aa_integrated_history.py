from __future__ import annotations

from pathlib import Path
from itertools import product
import base64, bz2, hashlib, io, shutil, subprocess, tarfile

STAGE=Path('.webbook-upload/aa-traditions-detailed')
EXPECTED='b4d64ad1899b1de37548283fefbb3f4dd99844d8603844e03e0d9bee645183c7'
NAMES=[f'part-{i:02d}.b64' for i in range(9)]
OUT=Path('/tmp/aa-integrated.md')

def sh(*args:str)->bytes:
    return subprocess.check_output(args,stderr=subprocess.DEVNULL)

def versions(name:str):
    path=f'{STAGE.as_posix()}/{name}'
    commits=sh('git','log','--all','--format=%H','--',path).decode().splitlines()
    out=[]; seen=set()
    for c in commits:
        try: txt=sh('git','show',f'{c}:{path}').decode('ascii')
        except Exception: continue
        txt=''.join(txt.split()); h=hashlib.sha256(txt.encode()).hexdigest()
        if h not in seen:
            seen.add(h); out.append((c,txt))
    print(name,'versions',[(c[:8],len(t),t.count('=')) for c,t in out])
    return out

def find_integrated(raw:bytes,label:str)->bool:
    if not raw.startswith(b'BZh'): return False
    try: tarbytes=bz2.decompress(raw)
    except Exception: return False
    root=Path('/tmp/aa-integrated-probe'); shutil.rmtree(root,ignore_errors=True); root.mkdir()
    try:
        with tarfile.open(fileobj=io.BytesIO(tarbytes),mode='r:') as tf: tf.extractall(root,filter='data')
    except Exception:
        return False
    files=list(root.rglob('*.md'))
    print(label,'md_count',len(files))
    for p in files:
        h=hashlib.sha256(p.read_bytes()).hexdigest()
        print(' ',p.name,h)
        if h==EXPECTED:
            shutil.copyfile(p,OUT)
            print('VALIDATED_INTEGRATED',label,p.name)
            return True
    return False

allv=[versions(n) for n in NAMES]
# Try every historical version combination as slices of one Base64 stream.
for combo in product(*allv):
    txt=''.join(x[1] for x in combo)
    if len(txt)%4 or '=' in txt[:-4]: continue
    try: raw=base64.b64decode(txt,validate=True)
    except Exception: continue
    if find_integrated(raw,'concat '+','.join(x[0][:8] for x in combo)):
        raise SystemExit(0)
# Also try each part independently encoded before binary concatenation.
valid=[]
for vs in allv:
    vv=[]
    for c,t in vs:
        try: vv.append((c,t,base64.b64decode(t,validate=True)))
        except Exception: pass
    valid.append(vv)
if all(valid):
    for combo in product(*valid):
        raw=b''.join(x[2] for x in combo)
        if find_integrated(raw,'perpart '+','.join(x[0][:8] for x in combo)):
            raise SystemExit(0)
raise SystemExit('No historical transfer combination contains the exact current integrated MD.')
