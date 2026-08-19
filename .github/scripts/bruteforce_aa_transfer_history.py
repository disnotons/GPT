from __future__ import annotations

from pathlib import Path
from itertools import product
import base64, bz2, hashlib, io, os, shutil, subprocess, tarfile

STAGE=Path('.webbook-upload/aa-traditions-detailed')
EXPECTED='f924aacf39ebf5b78002a4a24921997483b93d3227cc0ea43606bd99a74c2b5a'
NAMES=[f'part-{i:02d}.b64' for i in range(9)]

def sh(*args:str)->bytes:
    return subprocess.check_output(args,stderr=subprocess.DEVNULL)

def versions(name:str)->list[tuple[str,str]]:
    path=f'{STAGE.as_posix()}/{name}'
    commits=sh('git','log','--all','--format=%H','--',path).decode().splitlines()
    out=[]; seen=set()
    for c in commits:
        try: txt=sh('git','show',f'{c}:{path}').decode('ascii')
        except Exception: continue
        txt=''.join(txt.split())
        h=hashlib.sha256(txt.encode()).hexdigest()
        if h in seen: continue
        seen.add(h); out.append((c,txt))
    print(name,'unique_versions=',len(out),[(c[:8],len(t),t.count('=')) for c,t in out])
    return out

def check_archive(raw:bytes,label:str)->Path|None:
    if not raw.startswith(b'BZh'): return None
    try: tarbytes=bz2.decompress(raw)
    except Exception: return None
    root=Path('/tmp/aa-bruteforce-hit'); shutil.rmtree(root,ignore_errors=True); root.mkdir(parents=True)
    try:
        with tarfile.open(fileobj=io.BytesIO(tarbytes),mode='r:') as tf: tf.extractall(root,filter='data')
    except Exception: return None
    files=sorted(root.rglob('*.md'),key=lambda p:p.name.encode('utf-8'))
    if len(files)!=75: return None
    payload=b''.join(hashlib.sha256(p.read_bytes()).hexdigest().encode()+b'\n' for p in files)
    got=hashlib.sha256(payload).hexdigest()
    print(label,'md_count=',len(files),'digest=',got)
    return root if got==EXPECTED else None

def write_valid(parts:list[str],source:Path)->None:
    for name,txt in zip(NAMES,parts): (STAGE/name).write_text(txt,encoding='ascii')
    print('VALIDATED exact current source; canonical historical parts written.')

allv=[versions(n) for n in NAMES]
# Base64 stream slices: padding may occur only in the final slice.
pruned=[]
for i,vs in enumerate(allv):
    if i<8: vs=[x for x in vs if '=' not in x[1]]
    pruned.append(vs)
print('combination_space=',__import__('math').prod(len(v) for v in pruned))
tried=0
for combo in product(*pruned):
    tried+=1
    texts=[x[1] for x in combo]
    joined=''.join(texts)
    if len(joined)%4: continue
    if '=' in joined[:-4]: continue
    try: raw=base64.b64decode(joined,validate=True)
    except Exception: continue
    hit=check_archive(raw,'concat '+','.join(x[0][:8] for x in combo))
    if hit:
        write_valid(texts,hit); raise SystemExit(0)
print('concat_tried=',tried)

# Fallback: each text part may have been independently base64 encoded binary slices.
pruned2=[]
for vs in allv:
    good=[]
    for c,t in vs:
        try: good.append((c,t,base64.b64decode(t,validate=True)))
        except Exception: pass
    pruned2.append(good)
print('per_part_combination_space=',__import__('math').prod(len(v) for v in pruned2))
tried=0
for combo in product(*pruned2):
    tried+=1
    raw=b''.join(x[2] for x in combo)
    hit=check_archive(raw,'perpart '+','.join(x[0][:8] for x in combo))
    if hit:
        texts=[x[1] for x in combo]
        # Re-encode validated binary into a canonical single base64 stream split 9 ways.
        enc=base64.b64encode(raw).decode('ascii'); q,r=divmod(len(enc),9); pos=0; canon=[]
        for i in range(9):
            n=q+(i<r); canon.append(enc[pos:pos+n]); pos+=n
        write_valid(canon,hit); raise SystemExit(0)
print('perpart_tried=',tried)
raise SystemExit('No combination of historical transfer-part versions reproduces the current uploaded 75-MD digest.')
