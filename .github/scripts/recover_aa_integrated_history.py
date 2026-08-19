from __future__ import annotations

from pathlib import Path
from itertools import product
import base64, bz2, hashlib, io, shutil, subprocess, tarfile

STAGE=Path('.webbook-upload/aa-traditions-detailed')
EXPECTED='b4d64ad1899b1de37548283fefbb3f4dd99844d8603844e03e0d9bee645183c7'
OUT=Path('/tmp/aa-integrated.md')

def sh(*args:str)->bytes:
    return subprocess.check_output(args,stderr=subprocess.DEVNULL)

def find_integrated(raw:bytes,label:str)->bool:
    if not raw.startswith(b'BZh'): return False
    try: tarbytes=bz2.decompress(raw)
    except Exception: return False
    root=Path('/tmp/aa-integrated-probe'); shutil.rmtree(root,ignore_errors=True); root.mkdir()
    try:
        with tarfile.open(fileobj=io.BytesIO(tarbytes),mode='r:') as tf: tf.extractall(root,filter='data')
    except Exception:
        return False
    for p in root.rglob('*.md'):
        h=hashlib.sha256(p.read_bytes()).hexdigest()
        if h==EXPECTED:
            shutil.copyfile(p,OUT)
            print('VALIDATED_INTEGRATED',label,p.name,h)
            return True
    return False

def historical_texts(name:str):
    path=f'{STAGE.as_posix()}/{name}'
    commits=sh('git','log','--all','--format=%H','--',path).decode().splitlines()
    out=[]; seen=set()
    for c in commits:
        try: txt=sh('git','show',f'{c}:{path}').decode('ascii')
        except Exception: continue
        txt=''.join(txt.split())
        h=hashlib.sha256(txt.encode()).hexdigest()
        if h not in seen:
            seen.add(h); out.append((c,txt))
    print(name,'versions',[(c[:8],len(t),t.count('=')) for c,t in out])
    return out

def current_text(name:str):
    p=STAGE/name
    if not p.is_file(): raise SystemExit(f'missing exact source slice: {name}')
    return ''.join(p.read_text(encoding='ascii').split())

# Exact transfer was completed later with corrected slices 04 and 06-09.
# For slices 00-03 and 05, try the small set of historical versions retained by git.
fixed={
    4: current_text('current-part-04.b64'),
    6: current_text('current-part-06.b64'),
    7: current_text('current-part-07.b64'),
    8: current_text('current-part-08.b64'),
    9: current_text('current-part-09.b64'),
}
variable_indices=[0,1,2,3,5]
variable=[historical_texts(f'part-{i:02d}.b64') for i in variable_indices]
if not all(variable): raise SystemExit('missing historical source slice versions')

for combo in product(*variable):
    chosen={i:item for i,item in zip(variable_indices,combo)}
    pieces=[]; labels=[]
    for i in range(10):
        if i in fixed:
            pieces.append(fixed[i]); labels.append(f'current-{i:02d}')
        else:
            c,t=chosen[i]; pieces.append(t); labels.append(f'{i:02d}:{c[:8]}')
    txt=''.join(pieces)
    if len(txt)%4 or '=' in txt[:-4]: continue
    try: raw=base64.b64decode(txt,validate=True)
    except Exception: continue
    if find_integrated(raw,'ten-slice '+','.join(labels)):
        raise SystemExit(0)

# Legacy fallback: exhaustively test the original nine-slice transfer history.
allv=[historical_texts(f'part-{i:02d}.b64') for i in range(9)]
for combo in product(*allv):
    txt=''.join(x[1] for x in combo)
    if len(txt)%4 or '=' in txt[:-4]: continue
    try: raw=base64.b64decode(txt,validate=True)
    except Exception: continue
    if find_integrated(raw,'legacy-concat '+','.join(x[0][:8] for x in combo)):
        raise SystemExit(0)

raise SystemExit('No stored transfer combination contains the exact current integrated MD.')
