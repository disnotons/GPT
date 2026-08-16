from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

STEPS_ZIP = Path(sys.argv[1])
TRAD_ZIP = Path(sys.argv[2])
OUT = Path(sys.argv[3])


def md_entries(z: zipfile.ZipFile):
    return [n for n in z.namelist() if not n.endswith('/') and n.lower().endswith('.md')]


def num_key(name: str):
    base = Path(name).name
    pats = [r'(?:STEP|step)[ _-]*0?(\d{1,2})', r'(?:TRADITION|Tradition|tradition)[ _-]*0?(\d{1,2})', r'(?<!\d)(\d{1,2})(?!\d)']
    for p in pats:
        m = re.search(p, base)
        if m:
            return int(m.group(1))
    return 999


def first_text(raw: bytes) -> str:
    return raw.decode('utf-8', errors='replace')[:4000]


OUT.mkdir(parents=True, exist_ok=True)
content = OUT / 'content'
content.mkdir(parents=True, exist_ok=True)

manifest = []
hashes = {}

with zipfile.ZipFile(STEPS_ZIP) as z:
    names = md_entries(z)
    if len(names) != 12:
        raise SystemExit(f'Expected 12 step markdown files, got {len(names)}')
    names = sorted(names, key=lambda n: (num_key(n), n))
    for i, n in enumerate(names, 1):
        raw = z.read(n)
        dst = content / f'step-{i:02d}.md'
        dst.write_bytes(raw)
        hashes[dst.name] = hashlib.sha256(raw).hexdigest()
        manifest.append({'group': '12단계', 'label': f'{i}단계', 'file': dst.name})

with zipfile.ZipFile(TRAD_ZIP) as z:
    names = md_entries(z)
    if len(names) != 13:
        raise SystemExit(f'Expected 13 tradition markdown files, got {len(names)}')
    longform = []
    regular = []
    for n in names:
        raw = z.read(n)
        probe = (Path(n).name + '\n' + first_text(raw)).lower()
        if ('long form' in probe or 'longform' in probe or '롱 폼' in probe or 'long-form' in probe):
            longform.append((n, raw))
        else:
            regular.append((n, raw))
    if len(longform) != 1 or len(regular) != 12:
        # Fallback: the entry without a 1–12 tradition number is the Long Form.
        longform = []
        regular = []
        for n in names:
            raw = z.read(n)
            k = num_key(n)
            if 1 <= k <= 12:
                regular.append((n, raw))
            else:
                longform.append((n, raw))
    if len(longform) != 1 or len(regular) != 12:
        raise SystemExit(f'Could not identify 12 traditions + long form: regular={len(regular)}, long={len(longform)}')
    regular.sort(key=lambda x: (num_key(x[0]), x[0]))
    for i, (n, raw) in enumerate(regular, 1):
        dst = content / f'tradition-{i:02d}.md'
        dst.write_bytes(raw)
        hashes[dst.name] = hashlib.sha256(raw).hexdigest()
        manifest.append({'group': '12전통', 'label': f'{i}전통', 'file': dst.name})
    n, raw = longform[0]
    dst = content / 'traditions-long-form.md'
    dst.write_bytes(raw)
    hashes[dst.name] = hashlib.sha256(raw).hexdigest()
    manifest.append({'group': '부록', 'label': '12전통 Long Form', 'file': dst.name})

(OUT / 'content-sha256.json').write_text(json.dumps(hashes, ensure_ascii=False, indent=2), encoding='utf-8')
(OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

index_html = r'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AA 12단계 · 12전통 원전해설</title>
<link rel="stylesheet" href="style.css">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify/dist/purify.min.js"></script>
</head>
<body>
<div id="progress"></div>
<header><button id="menuBtn" aria-label="목차 열기">☰</button><div><strong>AA 12단계 · 12전통</strong><span>원전해설 웹북</span></div><button id="themeBtn" aria-label="테마 전환">◐</button></header>
<div class="layout">
<aside id="sidebar"><div class="side-title">목차</div><nav id="nav"></nav></aside>
<main><article id="article"><p class="loading">문서를 불러오는 중입니다.</p></article><div class="pager"><button id="prevBtn">← 이전</button><button id="nextBtn">다음 →</button></div></main>
</div>
<script src="app.js"></script>
</body>
</html>'''

style_css = r''':root{--bg:#f7f4ed;--paper:#fffdf8;--text:#292720;--muted:#777166;--line:#ddd6c8;--accent:#70593d;--header:#f0eadf;--shadow:0 10px 30px rgba(50,40,20,.08)}
:root.dark{--bg:#191816;--paper:#22201d;--text:#eee9df;--muted:#aaa397;--line:#3c3832;--accent:#d1b184;--header:#201e1b;--shadow:none}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,"Noto Sans KR",sans-serif;line-height:1.78}#progress{position:fixed;top:0;left:0;height:3px;background:var(--accent);width:0;z-index:100}header{height:64px;position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--header) 94%,transparent);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);display:flex;align-items:center;gap:14px;padding:0 18px}header div{display:flex;flex-direction:column;line-height:1.25}header span{font-size:.78rem;color:var(--muted)}header button{border:1px solid var(--line);background:var(--paper);color:var(--text);border-radius:9px;width:38px;height:38px;font-size:1.05rem;cursor:pointer}#themeBtn{margin-left:auto}.layout{display:grid;grid-template-columns:270px minmax(0,1fr);max-width:1320px;margin:auto}aside{position:sticky;top:64px;height:calc(100vh - 64px);overflow:auto;border-right:1px solid var(--line);padding:22px 14px;background:var(--bg)}.side-title{font-weight:750;margin:0 8px 14px}.group{margin:18px 0 7px;padding:0 8px;font-size:.78rem;color:var(--muted);font-weight:750}.navitem{display:block;width:100%;text-align:left;border:0;background:transparent;color:var(--text);padding:8px 10px;border-radius:8px;cursor:pointer}.navitem:hover,.navitem.active{background:var(--header);color:var(--accent)}main{min-width:0;padding:34px clamp(18px,5vw,74px) 70px}article{max-width:850px;margin:auto;background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:clamp(24px,5vw,58px);box-shadow:var(--shadow)}article h1{font-size:clamp(1.7rem,4vw,2.35rem);line-height:1.3;margin-top:0}article h2{margin-top:2.4em;padding-top:.35em;border-top:1px solid var(--line);font-size:1.4rem}article h3{margin-top:1.9em;font-size:1.18rem}article blockquote{margin:1.4em 0;padding:.35em 1em;border-left:4px solid var(--accent);background:var(--bg);color:var(--muted)}article code{background:var(--bg);padding:.12em .35em;border-radius:5px}article pre{overflow:auto;background:var(--bg);padding:14px;border-radius:10px}article table{border-collapse:collapse;width:100%;display:block;overflow:auto}article th,article td{border:1px solid var(--line);padding:8px 10px}article a{color:var(--accent)}.loading{color:var(--muted)}.pager{max-width:850px;margin:22px auto 0;display:flex;justify-content:space-between;gap:12px}.pager button{border:1px solid var(--line);background:var(--paper);color:var(--text);border-radius:10px;padding:10px 15px;cursor:pointer}.pager button:disabled{opacity:.35;cursor:default}@media(max-width:820px){.layout{display:block}aside{position:fixed;z-index:30;top:64px;left:0;width:min(86vw,330px);transform:translateX(-105%);transition:.22s;box-shadow:var(--shadow)}aside.open{transform:translateX(0)}main{padding:20px 12px 55px}article{border-radius:12px;padding:24px 19px}header{padding:0 12px}}'''

app_js = r'''const docs=[];for(let i=1;i<=12;i++)docs.push({group:'12단계',label:`${i}단계`,file:`step-${String(i).padStart(2,'0')}.md`});for(let i=1;i<=12;i++)docs.push({group:'12전통',label:`${i}전통`,file:`tradition-${String(i).padStart(2,'0')}.md`});docs.push({group:'부록',label:'12전통 Long Form',file:'traditions-long-form.md'});
const nav=document.querySelector('#nav'),article=document.querySelector('#article'),side=document.querySelector('#sidebar'),prev=document.querySelector('#prevBtn'),next=document.querySelector('#nextBtn');let current=0;
function buildNav(){let g='';docs.forEach((d,i)=>{if(d.group!==g){g=d.group;const h=document.createElement('div');h.className='group';h.textContent=g;nav.appendChild(h)}const b=document.createElement('button');b.className='navitem';b.textContent=d.label;b.dataset.i=i;b.onclick=()=>load(i);nav.appendChild(b)})}
async function load(i,push=true){current=Math.max(0,Math.min(docs.length-1,i));const d=docs[current];article.innerHTML='<p class="loading">문서를 불러오는 중입니다.</p>';try{const r=await fetch(`content/${d.file}`);if(!r.ok)throw new Error(r.status);const md=await r.text();article.innerHTML=DOMPurify.sanitize(marked.parse(md));document.title=`${d.label} · AA 12단계 · 12전통`;document.querySelectorAll('.navitem').forEach((x,j)=>x.classList.toggle('active',j===current));prev.disabled=current===0;next.disabled=current===docs.length-1;if(push)history.replaceState(null,'',`#${d.file.replace('.md','')}`);window.scrollTo({top:0,behavior:'instant'});side.classList.remove('open')}catch(e){article.innerHTML='<p>문서를 불러오지 못했습니다.</p>'}}
prev.onclick=()=>load(current-1);next.onclick=()=>load(current+1);document.querySelector('#menuBtn').onclick=()=>side.classList.toggle('open');document.querySelector('#themeBtn').onclick=()=>{document.documentElement.classList.toggle('dark');localStorage.setItem('aa-theme',document.documentElement.classList.contains('dark')?'dark':'light')};if(localStorage.getItem('aa-theme')==='dark')document.documentElement.classList.add('dark');window.addEventListener('scroll',()=>{const h=document.documentElement;const max=h.scrollHeight-h.clientHeight;document.querySelector('#progress').style.width=(max?100*h.scrollTop/max:0)+'%'});buildNav();const hash=location.hash.slice(1);const idx=docs.findIndex(d=>d.file.replace('.md','')===hash);load(idx>=0?idx:0,false);'''

(OUT / 'index.html').write_text(index_html, encoding='utf-8')
(OUT / 'style.css').write_text(style_css, encoding='utf-8')
(OUT / 'app.js').write_text(app_js, encoding='utf-8')
(OUT / 'health.txt').write_text('AA_WEBBOOK_OK\n', encoding='utf-8')
print(f'Built {len(manifest)} documents at {OUT}')
