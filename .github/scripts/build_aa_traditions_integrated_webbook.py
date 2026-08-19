from pathlib import Path
import hashlib, shutil

ROOT=Path.cwd(); SRC=Path('/tmp/aa-integrated.md'); TARGET=ROOT/'초기불교'/'aa'/'traditions-detailed'
EXPECTED='b4d64ad1899b1de37548283fefbb3f4dd99844d8603844e03e0d9bee645183c7'
if not SRC.exists() or hashlib.sha256(SRC.read_bytes()).hexdigest()!=EXPECTED:
    raise SystemExit('integrated source verification failed')
if TARGET.exists():
    raise SystemExit(f'target already exists: {TARGET}')
TARGET.mkdir(parents=True)
shutil.copyfile(SRC,TARGET/'book.md')
assert (TARGET/'book.md').read_bytes()==SRC.read_bytes()
(TARGET/'book.yaml').write_text('''title: "AA Twelve Traditions 상세 분석·해설"
category: "회복·AA"
collection: "AA 12단계·12전통"
series: "Twelve Traditions"
description: "AA Twelve Traditions를 세부 주제별로 읽을 수 있도록 구성한 상세 분석·해설 웹북."
language: "ko"
status: "complete"
source_sha256: "b4d64ad1899b1de37548283fefbb3f4dd99844d8603844e03e0d9bee645183c7"
content_file: "book.md"
''',encoding='utf-8')
(TARGET/'README.md').write_text('''# AA Twelve Traditions 상세 분석·해설 웹북

- 범위: Tradition One 1.1 ~ Tradition Twelve 12.6 + Long Form A.1 ~ A.4
- 본문: 원본 전체 통합 MD를 바이트 단위로 변경 없이 복사
- 목차·검색·이동·다크 모드는 웹북 화면에서 제공
''',encoding='utf-8')
(TARGET/'index.html').write_text('''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="AA Twelve Traditions 상세 분석·해설 웹북"><title>AA Twelve Traditions 상세 분석·해설</title><link rel="stylesheet" href="./style.css"><script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script></head><body><header><button id="menu">☰</button><div class="brand"><strong>AA Twelve Traditions</strong><span>상세 분석·해설</span></div><div class="right"><a href="./book.md">원문 MD</a><button id="theme">◐</button></div></header><div class="layout"><aside><input id="search" type="search" placeholder="목차 검색"><nav id="toc"></nav></aside><main><article id="content">웹북을 불러오는 중입니다…</article><nav class="pager"><button id="prev">← 이전</button><span id="pos"></span><button id="next">다음 →</button></nav></main></div><button id="top">↑</button><script src="./app.js"></script></body></html>''',encoding='utf-8')
(TARGET/'style.css').write_text(''':root{color-scheme:light;--bg:#f5f3ee;--paper:#fffdfa;--text:#282720;--muted:#77736b;--line:#ded9cf;--accent:#31594d;--soft:#e8efec;--top:64px;--side:330px}html[data-theme=dark]{color-scheme:dark;--bg:#151815;--paper:#1d211e;--text:#ecece5;--muted:#b4b4ac;--line:#363b37;--accent:#9bc6b7;--soft:#26352f}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,"Noto Sans KR",sans-serif;line-height:1.78}a{color:var(--accent)}button,input{font:inherit}header{position:fixed;z-index:30;inset:0 0 auto;height:var(--top);display:flex;align-items:center;gap:12px;padding:0 16px;border-bottom:1px solid var(--line);background:var(--paper)}header button,header a,.pager button{border:1px solid var(--line);border-radius:10px;background:var(--paper);color:var(--text);padding:8px 11px;text-decoration:none;cursor:pointer}.brand{display:flex;flex-direction:column;line-height:1.2}.brand strong{font-size:15px}.brand span{font-size:12px;color:var(--muted)}.right{margin-left:auto;display:flex;gap:8px}.layout{padding-top:var(--top);min-height:100vh}aside{position:fixed;top:var(--top);bottom:0;left:0;width:var(--side);overflow:auto;border-right:1px solid var(--line);background:var(--paper);padding:18px 16px 42px;z-index:20}#search{width:100%;padding:10px;border:1px solid var(--line);border-radius:9px;background:var(--bg);color:var(--text)}#toc a{display:block;padding:7px 9px;border-radius:8px;text-decoration:none;color:var(--text);font-size:13px;line-height:1.4}#toc a:hover,#toc a.active{background:var(--soft);color:var(--accent)}main{margin-left:var(--side);padding:30px 36px 90px}article{width:min(100%,900px);margin:auto;padding:46px 52px 70px;border:1px solid var(--line);border-radius:18px;background:var(--paper)}article h1{font-size:clamp(1.8rem,4vw,2.7rem);line-height:1.25}article h2{margin-top:2.4em}article h3{margin-top:2em}article blockquote{margin:22px 0;padding:10px 18px;border-left:4px solid var(--accent);background:var(--soft)}article table{display:block;overflow:auto;border-collapse:collapse}article th,article td{border:1px solid var(--line);padding:8px 10px}.pager{width:min(100%,900px);margin:18px auto;display:flex;align-items:center;justify-content:space-between;gap:10px}.pager button:disabled{opacity:.4}#pos{font-size:12px;color:var(--muted)}#top{position:fixed;right:20px;bottom:20px;width:44px;height:44px;border:1px solid var(--line);border-radius:50%;background:var(--paper);color:var(--text)}#menu{display:none}@media(max-width:900px){:root{--side:min(88vw,350px)}#menu{display:block}aside{transform:translateX(-105%);transition:.2s}aside.open{transform:translateX(0)}main{margin-left:0;padding:16px 10px 70px}article{padding:30px 20px 55px}.right a{display:none}}''',encoding='utf-8')
(TARGET/'app.js').write_text('''(()=>{const $=s=>document.querySelector(s),side=$('aside'),toc=$('#toc'),content=$('#content');let items=[],cur=0;const saved=localStorage.getItem('aa-td-theme');if(saved)document.documentElement.dataset.theme=saved;$('#theme').onclick=()=>{const n=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=n;localStorage.setItem('aa-td-theme',n)};$('#menu').onclick=()=>side.classList.toggle('open');$('#top').onclick=()=>scrollTo({top:0,behavior:'smooth'});function slug(s,i){return 's-'+i+'-'+s.toLowerCase().replace(/[^0-9a-z가-힣]+/g,'-').replace(/^-|-$/g,'').slice(0,55)}function go(i,push=true){if(i<0||i>=items.length)return;cur=i;items[i].el.scrollIntoView({behavior:'smooth',block:'start'});toc.querySelectorAll('a').forEach((a,j)=>a.classList.toggle('active',j===i));$('#prev').disabled=i===0;$('#next').disabled=i===items.length-1;$('#pos').textContent=`${i+1} / ${items.length}`;if(push)history.replaceState(null,'','#'+items[i].id);side.classList.remove('open')}$('#prev').onclick=()=>go(cur-1);$('#next').onclick=()=>go(cur+1);$('#search').oninput=()=>{const q=$('#search').value.trim().toLowerCase();toc.querySelectorAll('a').forEach(a=>a.hidden=!!q&&!a.textContent.toLowerCase().includes(q))};fetch('./book.md',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error(`HTTP ${r.status}`);return r.text()}).then(t=>{content.innerHTML=marked.parse(t);const hs=[...content.querySelectorAll('h2')].filter(h=>/(^|\s)(?:\d{1,2}\.\d+|A\.\d+)(?:\s|$)/.test(h.textContent));items=hs.map((el,i)=>{const id=slug(el.textContent,i);el.id=id;const a=document.createElement('a');a.href='#'+id;a.textContent=el.textContent;a.onclick=e=>{e.preventDefault();go(i)};toc.appendChild(a);return{el,id}});const wanted=decodeURIComponent(location.hash.slice(1)),i=Math.max(0,items.findIndex(x=>x.id===wanted));if(items.length){cur=i;$('#prev').disabled=i===0;$('#next').disabled=i===items.length-1;$('#pos').textContent=`${i+1} / ${items.length}`}}).catch(e=>content.innerHTML=`<h1>웹북을 불러오지 못했습니다</h1><p>${e.message}</p>`);})();''',encoding='utf-8')

p=ROOT/'.github'/'workflows'/'deploy-pages.yml'; s=p.read_text(encoding='utf-8')
if 'Stage AA Twelve Traditions detailed web book' not in s:
    marker='      - name: Stage Hawkins mobile web books\n'
    insert='''      - name: Stage AA Twelve Traditions detailed web book\n        shell: bash\n        run: |\n          set -euo pipefail\n          src="초기불교/aa/traditions-detailed"\n          target="_site_src/publish_site/aa/traditions-detailed"\n          test -f "$src/index.html"\n          test -f "$src/book.md"\n          test -f "$src/book.yaml"\n          rm -rf "$target"\n          mkdir -p "$target"\n          cp -R "$src/." "$target/"\n\n'''
    if marker not in s: raise SystemExit('Pages staging marker missing')
    s=s.replace(marker,insert+marker,1)
if 'Verify AA Twelve Traditions detailed in built artifact' not in s:
    marker='      - name: Ensure CW11 in final Pages artifact\n'
    insert='''      - name: Verify AA Twelve Traditions detailed in built artifact\n        shell: bash\n        run: |\n          set -euo pipefail\n          test -f _site/aa/traditions-detailed/index.html\n          test -f _site/aa/traditions-detailed/book.md\n          test -f _site/aa/traditions-detailed/book.yaml\n\n'''
    if marker not in s: raise SystemExit('Pages verify marker missing')
    s=s.replace(marker,insert+marker,1)
p.write_text(s,encoding='utf-8')
print('built exact integrated AA webbook')
