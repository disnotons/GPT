#!/usr/bin/env python3
from __future__ import annotations
import json,re,shutil,sys,zipfile
from pathlib import Path

if len(sys.argv)!=4:
    raise SystemExit('usage: build_aa_site.py STEPS.zip TRADITIONS.zip TARGET')
steps_zip=Path(sys.argv[1]); traditions_zip=Path(sys.argv[2]); target=Path(sys.argv[3])
site=Path(__file__).resolve().parent/'site'
target.mkdir(parents=True,exist_ok=True)
(target/'content').mkdir(exist_ok=True)
for name in ('index.html','style.css','app.js'):
    shutil.copy2(site/name,target/name)

def repair_name(name:str)->str:
    candidates=[name]
    for enc in ('cp949','utf-8'):
        try:candidates.append(name.encode('cp437').decode(enc))
        except Exception:pass
    def score(s):
        return sum('가'<=c<='힣' for c in s)*10 - s.count('�')*20
    return max(candidates,key=score)

def text_for_title(raw:bytes)->str:
    for enc in ('utf-8-sig','utf-8','cp949'):
        try:return raw.decode(enc)
        except Exception:pass
    return ''

def heading(raw:bytes,fallback:str)->str:
    txt=text_for_title(raw)
    for line in txt.splitlines():
        m=re.match(r'^#\s+(.+?)\s*$',line)
        if m:return m.group(1).strip()
    return fallback

def step_no(name:str,title:str):
    s=name+' '+title
    pats=[r'(?i)STEP\s*0?(\d{1,2})',r'(?:제\s*)?(\d{1,2})\s*단계',r'단계[_\-\s]*0?(\d{1,2})']
    for p in pats:
        m=re.search(p,s)
        if m:
            n=int(m.group(1))
            if 1<=n<=12:return n
    return None

def tradition_no(name:str,title:str):
    s=name+' '+title
    pats=[r'(?i)TRADITION\s*0?(\d{1,2})',r'(?:제\s*)?(\d{1,2})\s*전통',r'전통[_\-\s]*0?(\d{1,2})']
    for p in pats:
        m=re.search(p,s)
        if m:
            n=int(m.group(1))
            if 1<=n<=12:return n
    m=re.search(r'[_\-]0?([1-9]|1[0-2])(?:[_\-.])',name)
    return int(m.group(1)) if m else None

def docs_from_zip(path:Path):
    out=[]
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            if info.is_dir():continue
            fixed=repair_name(info.filename)
            if not fixed.lower().endswith('.md'):continue
            if '__MACOSX' in fixed or Path(fixed).name.startswith('._'):continue
            raw=z.read(info)
            out.append({'name':Path(fixed).name,'raw':raw,'title':heading(raw,Path(fixed).stem)})
    return out

steps=docs_from_zip(steps_zip)
trad=docs_from_zip(traditions_zip)
if len(steps)!=12: raise SystemExit(f'expected 12 step docs, got {len(steps)}: {[d["name"] for d in steps]}')
if len(trad)!=13: raise SystemExit(f'expected 13 tradition docs, got {len(trad)}: {[d["name"] for d in trad]}')

for d in steps:d['n']=step_no(d['name'],d['title'])
if sorted(d['n'] for d in steps if d['n'] is not None)!=list(range(1,13)):
    steps.sort(key=lambda d:d['name']);
    for i,d in enumerate(steps,1):d['n']=i
else:steps.sort(key=lambda d:d['n'])

for d in trad:d['n']=tradition_no(d['name'],d['title'])
numbered=[d for d in trad if d['n'] is not None]
longs=[d for d in trad if d['n'] is None or re.search(r'(?i)long\s*form|longform|롱\s*폼',d['name']+' '+d['title'])]
# Prefer an explicit Long Form document when present.
explicit=[d for d in trad if re.search(r'(?i)long\s*form|longform|롱\s*폼',d['name']+' '+d['title'])]
if explicit:
    longdoc=explicit[0]; numbered=[d for d in trad if d is not longdoc]
else:
    candidates=[d for d in trad if d['n'] is None]
    if len(candidates)!=1: raise SystemExit('could not identify Long Form tradition document')
    longdoc=candidates[0]; numbered=[d for d in trad if d is not longdoc]
if sorted(d['n'] for d in numbered if d['n'] is not None)!=list(range(1,13)):
    numbered.sort(key=lambda d:d['name'])
    for i,d in enumerate(numbered,1):d['n']=i
else:numbered.sort(key=lambda d:d['n'])

sections=[{'title':'12단계','items':[]},{'title':'12전통','items':[]},{'title':'Long Form','items':[]}]
for d in steps:
    fn=f'step-{d["n"]:02d}.md'; (target/'content'/fn).write_bytes(d['raw']); sections[0]['items'].append({'file':fn,'title':d['title']})
for d in numbered:
    fn=f'tradition-{d["n"]:02d}.md'; (target/'content'/fn).write_bytes(d['raw']); sections[1]['items'].append({'file':fn,'title':d['title']})
fn='traditions-long-form.md'; (target/'content'/fn).write_bytes(longdoc['raw']); sections[2]['items'].append({'file':fn,'title':longdoc['title']})
manifest={'title':'AA 12단계 · 12전통','documentCount':25,'sections':sections}
(target/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(target/'health.txt').write_text('aa-route-ok\n',encoding='utf-8')
print('AA_WEBBOOK_BUILD_OK',sum(len(s['items']) for s in sections))
