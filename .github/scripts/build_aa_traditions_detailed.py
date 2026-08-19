from __future__ import annotations

from pathlib import Path
import base64
import bz2
import hashlib
import io
import json
import re
import shutil
import tarfile

ROOT = Path.cwd()
STAGE = ROOT / '.webbook-upload' / 'aa-traditions-detailed'
TARGET = ROOT / '초기불교' / 'aa' / 'traditions-detailed'
EXPECTED = 'f924aacf39ebf5b78002a4a24921997483b93d3227cc0ea43606bd99a74c2b5a'

CANDIDATES = [
    ['part-00.b64','part-01.b64','part-02.b64','part-03.b64','part-04.b64','part-05.b64','part-06.b64','part-07.b64','part-08.b64'],
    ['part-00.b64','part-01.b64','part-02.b64','part-03.b64','part-04-new.b64','part-05-new.b64','part-06-new.b64','part-07.b64','part-08.b64'],
]

def digest_md(root: Path) -> str:
    files = sorted(root.rglob('*.md'), key=lambda p: p.name.encode('utf-8'))
    if len(files) != 75:
        return ''
    payload = b''.join(hashlib.sha256(p.read_bytes()).hexdigest().encode() + b'\n' for p in files)
    return hashlib.sha256(payload).hexdigest()

def extract_source() -> Path:
    work = Path('/tmp/aa-traditions-validated')
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    for n, names in enumerate(CANDIDATES, 1):
        try:
            encoded = ''.join((STAGE / name).read_text(encoding='ascii') for name in names)
            raw = base64.b64decode(''.join(encoded.split()), validate=True)
            tar_bytes = bz2.decompress(raw)
            out = work / f'candidate-{n}'
            out.mkdir()
            with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode='r:') as tf:
                tf.extractall(out, filter='data')
            got = digest_md(out)
            print(f'candidate {n} digest: {got}')
            if got == EXPECTED:
                return out
        except Exception as exc:
            print(f'candidate {n} rejected: {exc}')
    raise SystemExit('No staged source matches the uploaded 75-MD source digest.')

def safe_filename(raw: str) -> str:
    raw = re.sub(r'[\\/:*?"<>|#%「」『』‘’“”]', '', raw)
    raw = re.sub(r'\s+', '_', raw).strip('_')
    return raw

def build(source: Path) -> None:
    if TARGET.exists():
        raise SystemExit(f'target already exists: {TARGET}')
    (TARGET / 'content').mkdir(parents=True)
    files = list(source.rglob('*.md'))
    integrated = [p for p in files if p.name == 'AA_12전통_상세분석해설_전체통합본_친절한설명조.md']
    if len(integrated) != 1:
        raise SystemExit(f'integrated source count: {len(integrated)}')
    individual = [p for p in files if p.name.startswith('AA_12전통_상세분석해설_') and p.name != integrated[0].name]
    if len(individual) != 74:
        raise SystemExit(f'individual source count: {len(individual)}')

    rows = []
    for p in individual:
        m = re.match(r'AA_12전통_상세분석해설_((?:\d+|A)\.(\d+))_(.+)_친절한설명조\.md$', p.name)
        if not m:
            raise SystemExit(f'unexpected filename: {p.name}')
        code, sub, raw_title = m.group(1), m.group(2), m.group(3)
        major = code.split('.')[0]
        if major == 'A':
            out_id, key = f'A-{int(sub):02d}', (99, int(sub))
        else:
            out_id, key = f'{int(major):02d}-{int(sub):02d}', (int(major), int(sub))
        text = p.read_text(encoding='utf-8')
        h2 = next((line[3:].strip() for line in text.splitlines() if line.startswith('## ')), None)
        if not h2 or code not in h2:
            raise SystemExit(f'cannot resolve title: {p.name}')
        title = h2.split('—', 1)[-1].strip()
        rows.append((key, out_id, title, f'{out_id}_{safe_filename(raw_title)}.md', p))
    rows.sort(key=lambda x: x[0])

    chapters = []
    for _, out_id, title, out_name, src in rows:
        dst = TARGET / 'content' / out_name
        shutil.copyfile(src, dst)
        if dst.read_bytes() != src.read_bytes():
            raise SystemExit(f'byte mismatch: {src.name}')
        chapters.append({'id': out_id, 'title': title, 'file': f'content/{out_name}', 'source_file': src.name})
    shutil.copyfile(integrated[0], TARGET / 'book.md')
    if (TARGET / 'book.md').read_bytes() != integrated[0].read_bytes():
        raise SystemExit('integrated book byte mismatch')

    meta = {
        'title': 'AA Twelve Traditions 상세 분석·해설',
        'category': '회복·AA',
        'collection': 'AA 12단계·12전통',
        'series': 'Twelve Traditions',
        'description': 'AA Twelve Traditions를 세부 주제별로 읽을 수 있도록 구성한 상세 분석·해설 웹북.',
        'language': 'ko', 'status': 'complete', 'chapters': chapters,
    }
    (TARGET / 'book.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    q = lambda s: json.dumps(s, ensure_ascii=False)
    yaml_lines = [
        f'title: {q(meta["title"])}', f'category: {q(meta["category"])}',
        f'collection: {q(meta["collection"])}', f'series: {q(meta["series"])}',
        f'description: {q(meta["description"])}', f'language: {q(meta["language"])}',
        f'status: {q(meta["status"])}', 'chapters:'
    ]
    for c in chapters:
        yaml_lines += [f'  - id: {q(c["id"])}', f'    title: {q(c["title"])}', f'    file: {q(c["file"])}', f'    source_file: {q(c["source_file"])}']
    (TARGET / 'book.yaml').write_text('\n'.join(yaml_lines) + '\n', encoding='utf-8')
    (TARGET / 'README.md').write_text(
        '# AA Twelve Traditions 상세 분석·해설 웹북\n\n'
        '- 범위: Tradition One 1.1 ~ Tradition Twelve 12.6 + Long Form A.1 ~ A.4\n'
        '- 개별 해설: 74개\n'
        '- `content/`의 본문은 원본 MD에서 바이트 단위로 동일하게 복사했습니다.\n'
        '- `book.md`는 원본 전체 통합본을 그대로 복사했습니다.\n', encoding='utf-8')

    (TARGET / 'index.html').write_text('''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="AA Twelve Traditions 상세 분석·해설 웹북"><title>AA Twelve Traditions 상세 분석·해설</title><link rel="stylesheet" href="./style.css"><script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script></head><body><header><button id="menu">☰</button><div class="brand"><strong>AA Twelve Traditions</strong><span>상세 분석·해설</span></div><div class="right"><a href="./book.md">통합 MD</a><button id="theme">◐</button></div></header><div class="layout"><aside><input id="search" type="search" placeholder="목차 검색"><nav id="toc"></nav></aside><main><article id="content">웹북을 불러오는 중입니다…</article><nav class="pager"><button id="prev">← 이전</button><span id="pos"></span><button id="next">다음 →</button></nav></main></div><button id="top">↑</button><script src="./app.js"></script></body></html>''', encoding='utf-8')
    (TARGET / 'style.css').write_text(''':root{color-scheme:light;--bg:#f5f3ee;--paper:#fffdfa;--text:#282720;--muted:#77736b;--line:#ded9cf;--accent:#31594d;--soft:#e8efec;--top:64px;--side:330px}html[data-theme=dark]{color-scheme:dark;--bg:#151815;--paper:#1d211e;--text:#ecece5;--muted:#b4b4ac;--line:#363b37;--accent:#9bc6b7;--soft:#26352f}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,"Noto Sans KR",sans-serif;line-height:1.78}a{color:var(--accent)}button,input{font:inherit}header{position:fixed;z-index:30;inset:0 0 auto;height:var(--top);display:flex;align-items:center;gap:12px;padding:0 16px;border-bottom:1px solid var(--line);background:var(--paper)}header button,header a,.pager button{border:1px solid var(--line);border-radius:10px;background:var(--paper);color:var(--text);padding:8px 11px;text-decoration:none;cursor:pointer}.brand{display:flex;flex-direction:column;line-height:1.2}.brand strong{font-size:15px}.brand span{font-size:12px;color:var(--muted)}.right{margin-left:auto;display:flex;gap:8px}.layout{padding-top:var(--top);min-height:100vh}aside{position:fixed;top:var(--top);bottom:0;left:0;width:var(--side);overflow:auto;border-right:1px solid var(--line);background:var(--paper);padding:18px 16px 42px;z-index:20}#search{width:100%;padding:10px;border:1px solid var(--line);border-radius:9px;background:var(--bg);color:var(--text)}#toc h3{font-size:12px;color:var(--muted);margin:18px 8px 6px}#toc a{display:block;padding:7px 9px;border-radius:8px;text-decoration:none;color:var(--text);font-size:13px;line-height:1.4}#toc a:hover,#toc a.active{background:var(--soft);color:var(--accent)}main{margin-left:var(--side);padding:30px 36px 90px}article{width:min(100%,900px);margin:auto;padding:46px 52px 70px;border:1px solid var(--line);border-radius:18px;background:var(--paper)}article h1{font-size:clamp(1.8rem,4vw,2.7rem);line-height:1.25}article h2{margin-top:2.2em}article blockquote{margin:22px 0;padding:10px 18px;border-left:4px solid var(--accent);background:var(--soft)}article table{display:block;overflow:auto;border-collapse:collapse}article th,article td{border:1px solid var(--line);padding:8px 10px}.pager{width:min(100%,900px);margin:18px auto;display:flex;align-items:center;justify-content:space-between;gap:10px}.pager button:disabled{opacity:.4}#pos{font-size:12px;color:var(--muted)}#top{position:fixed;right:20px;bottom:20px;width:44px;height:44px;border:1px solid var(--line);border-radius:50%;background:var(--paper);color:var(--text)}#menu{display:none}@media(max-width:900px){:root{--side:min(88vw,350px)}#menu{display:block}aside{transform:translateX(-105%);transition:.2s}aside.open{transform:translateX(0)}main{margin-left:0;padding:16px 10px 70px}article{padding:30px 20px 55px}.right a{display:none}}''', encoding='utf-8')
    (TARGET / 'app.js').write_text('''(()=>{const $=s=>document.querySelector(s),toc=$('#toc'),content=$('#content'),side=$('aside');let cs=[],cur=0;const group=id=>id.startsWith('A-')?'Long Form 부록':`Tradition ${Number(id.slice(0,2))}`;const saved=localStorage.getItem('aa-td-theme');if(saved)document.documentElement.dataset.theme=saved;$('#theme').onclick=()=>{const n=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=n;localStorage.setItem('aa-td-theme',n)};$('#menu').onclick=()=>side.classList.toggle('open');$('#top').onclick=()=>scrollTo({top:0,behavior:'smooth'});function build(){toc.innerHTML='';let g='';cs.forEach((c,i)=>{const ng=group(c.id);if(ng!==g){g=ng;const h=document.createElement('h3');h.textContent=g;toc.appendChild(h)}const a=document.createElement('a');a.href=`#${c.id}`;a.textContent=`${c.id.replace('-','.')} ${c.title}`;a.dataset.i=i;a.dataset.s=a.textContent.toLowerCase();toc.appendChild(a)})}$('#search').oninput=()=>{const q=$('#search').value.trim().toLowerCase();toc.querySelectorAll('a').forEach(a=>a.hidden=!!q&&!a.dataset.s.includes(q))};async function open(i,push=true){if(i<0||i>=cs.length)return;cur=i;const c=cs[i],r=await fetch('./'+encodeURI(c.file),{cache:'no-store'});if(!r.ok)throw Error(`HTTP ${r.status}`);content.innerHTML=marked.parse(await r.text());document.title=`${c.id.replace('-','.')} ${c.title} · AA Twelve Traditions`;toc.querySelectorAll('a').forEach(a=>a.classList.toggle('active',Number(a.dataset.i)===i));$('#prev').disabled=i===0;$('#next').disabled=i===cs.length-1;$('#pos').textContent=`${i+1} / ${cs.length}`;if(push)history.replaceState(null,'',`#${c.id}`);side.classList.remove('open');scrollTo({top:0})}$('#prev').onclick=()=>open(cur-1);$('#next').onclick=()=>open(cur+1);fetch('./book.json',{cache:'no-store'}).then(r=>r.json()).then(m=>{cs=m.chapters;build();toc.onclick=e=>{const a=e.target.closest('a');if(a){e.preventDefault();open(Number(a.dataset.i))}};const id=decodeURIComponent(location.hash.slice(1)),i=Math.max(0,cs.findIndex(c=>c.id===id));return open(i,false)}).catch(e=>content.innerHTML=`<h1>웹북을 불러오지 못했습니다</h1><p>${e.message}</p>`);})();''', encoding='utf-8')

    count = len(list((TARGET / 'content').glob('*.md')))
    if count != 74:
        raise SystemExit(f'published content count: {count}')

def patch_pages() -> None:
    p = ROOT / '.github' / 'workflows' / 'deploy-pages.yml'
    s = p.read_text(encoding='utf-8')
    if 'Stage AA Twelve Traditions detailed web book' not in s:
        marker = '      - name: Stage Hawkins mobile web books\n'
        insert = '''      - name: Stage AA Twelve Traditions detailed web book\n        shell: bash\n        run: |\n          set -euo pipefail\n          src="초기불교/aa/traditions-detailed"\n          target="_site_src/publish_site/aa/traditions-detailed"\n          test -f "$src/index.html"\n          test -f "$src/book.yaml"\n          test -f "$src/book.json"\n          test "$(find "$src/content" -maxdepth 1 -type f -name '*.md' | wc -l | tr -d ' ')" = "74"\n          rm -rf "$target"\n          mkdir -p "$target"\n          cp -R "$src/." "$target/"\n\n'''
        if marker not in s:
            raise SystemExit('Pages stage marker missing')
        s = s.replace(marker, insert + marker, 1)
    if 'Verify AA Twelve Traditions detailed in built artifact' not in s:
        marker = '      - name: Ensure CW11 in final Pages artifact\n'
        insert = '''      - name: Verify AA Twelve Traditions detailed in built artifact\n        shell: bash\n        run: |\n          set -euo pipefail\n          test -f _site/aa/traditions-detailed/index.html\n          test -f _site/aa/traditions-detailed/book.json\n          test -f _site/aa/traditions-detailed/book.yaml\n          test "$(find _site/aa/traditions-detailed/content -maxdepth 1 -type f -name '*.md' | wc -l | tr -d ' ')" = "74"\n\n'''
        if marker not in s:
            raise SystemExit('Pages verify marker missing')
        s = s.replace(marker, insert + marker, 1)
    p.write_text(s, encoding='utf-8')

if __name__ == '__main__':
    src = extract_source()
    build(src)
    patch_pages()
    print('AA Twelve Traditions detailed webbook built and Pages workflow patched.')
