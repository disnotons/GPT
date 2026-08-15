const chapters = [
  { n:1, title:'하느님 나라와 회개 — 예수님 가르침의 출발점', file:'1강_하느님_나라와_회개_통합정제본.md' },
  { n:2, title:'팔복 — 예수님이 말하는 ‘복된 사람’', file:'2강_팔복_예수님이_말하는_복된_사람.md' },
  { n:3, title:'보복을 넘어서는 사랑', file:'3강_보복을_넘어서는_사랑_통합정제본.md' },
  { n:4, title:'기도와 아버지', file:'4강_기도와_아버지_통합정제본.md' },
  { n:5, title:'재물·염려·마음의 방향', file:'5강_재물_염려_마음의_방향_통합정제본.md' },
  { n:6, title:'판단·자기성찰·황금률', file:'6강_판단_자기성찰_황금률.md' },
  { n:7, title:'온유함과 쉼', file:'7강_온유함과_쉼.md' },
  { n:8, title:'용서는 어디까지인가', file:'8강_용서는_어디까지인가_통합정제본.md' },
  { n:9, title:'가장 큰 계명과 ‘이웃’', file:'9강_가장_큰_계명과_이웃.md' },
  { n:10, title:'밖이 아니라 마음에서 시작되는 것', file:'10강_밖이_아니라_마음에서_시작되는_것.md' },
  { n:11, title:'제자가 된다는 것', file:'11강_제자가_된다는_것_통합정제본.md' },
  { n:12, title:'돌아옴·진리·사랑·성령·평화', file:'12강_돌아옴_진리_사랑_성령_평화_통합정제본.md' }
];

const $ = id => document.getElementById(id);
const nav=$('chapterNav'), content=$('content'), badge=$('chapterBadge'), statusEl=$('readingStatus');
const prevButton=$('prevButton'), nextButton=$('nextButton'), sidebar=$('sidebar'), scrim=$('scrim');
const menuButton=$('menuButton'), closeMenuButton=$('closeMenuButton'), themeButton=$('themeButton'), progress=$('progress');

function navMarkup(){
  nav.innerHTML=chapters.map(ch=>`<a class="chapter-link" data-chapter="${ch.n}" href="#chapter=${ch.n}"><span class="chapter-no">${String(ch.n).padStart(2,'0')}강</span><span class="chapter-title">${ch.title}</span></a>`).join('');
}
function chapterFromHash(){
  const m=location.hash.match(/chapter=(\d+)/); const n=m?Number(m[1]):1;
  return Math.min(12,Math.max(1,Number.isFinite(n)?n:1));
}
function setActiveNav(n){document.querySelectorAll('.chapter-link').forEach(a=>{const active=Number(a.dataset.chapter)===n;a.classList.toggle('active',active);active?a.setAttribute('aria-current','page'):a.removeAttribute('aria-current')})}
function pagerHTML(label,ch){return ch?`<span class="pager-eyebrow">${label}</span><span class="pager-title">${ch.n}강 · ${ch.title}</span>`:''}
function updatePager(n){
  const prev=chapters[n-2], next=chapters[n];
  prevButton.disabled=!prev; nextButton.disabled=!next;
  prevButton.innerHTML=prev?pagerHTML('← 이전 강',prev):'<span class="pager-eyebrow">처음입니다</span>';
  nextButton.innerHTML=next?pagerHTML('다음 강 →',next):'<span class="pager-eyebrow">마지막 강입니다</span>';
  prevButton.onclick=prev?()=>location.hash=`chapter=${prev.n}`:null;
  nextButton.onclick=next?()=>location.hash=`chapter=${next.n}`:null;
}
function estimateMinutes(md){const compact=md.replace(/[`#>*_\-|\[\]()]/g,'').replace(/\s+/g,'');return Math.max(1,Math.round(compact.length/500))}

// 저장소의 원문 Markdown은 바꾸지 않습니다. 아래 변환은 웹에서 읽을 때만 적용됩니다.
// 성경 인용·프로젝트 번역·시리아어·제목·표·코드는 그대로 두고, 해설 문장만 자연스러운 존댓말로 정리합니다.
const rules = [
  ['말씀하신다.','말씀하십니다.'],['말씀하셨다.','말씀하셨습니다.'],['요청하신다.','요청하십니다.'],['가르치신다.','가르치십니다.'],
  ['것이다.','것입니다.'],['때문이다.','때문입니다.'],['의미다.','의미입니다.'],['문제다.','문제입니다.'],['핵심이다.','핵심입니다.'],['방향이다.','방향입니다.'],['구조다.','구조입니다.'],['방식이다.','방식입니다.'],['아니다.','아닙니다.'],['이다.','입니다.'],
  ['보여준다.','보여줍니다.'],['드러낸다.','드러냅니다.'],['설명한다.','설명합니다.'],['가르친다.','가르칩니다.'],['제시한다.','제시합니다.'],['말한다.','말합니다.'],['요청한다.','요청합니다.'],['강조한다.','강조합니다.'],['뜻한다.','뜻합니다.'],['포함한다.','포함합니다.'],['구분한다.','구분합니다.'],['묻는다.','묻습니다.'],['다룬다.','다룹니다.'],['가리킨다.','가리킵니다.'],['읽는다.','읽습니다.'],['살핀다.','살핍니다.'],['사용한다.','사용합니다.'],['이해한다.','이해합니다.'],['연결한다.','연결합니다.'],['만든다.','만듭니다.'],['한다.','합니다.'],
  ['이어진다.','이어집니다.'],['연결된다.','연결됩니다.'],['드러난다.','드러납니다.'],['나타난다.','나타납니다.'],['주어진다.','주어집니다.'],['달라진다.','달라집니다.'],['시작된다.','시작됩니다.'],['요구된다.','요구됩니다.'],['된다.','됩니다.'],['생긴다.','생깁니다.'],['나온다.','나옵니다.'],['보인다.','보입니다.'],['남는다.','남습니다.'],['나아간다.','나아갑니다.'],['돌아간다.','돌아갑니다.'],['간다.','갑니다.'],
  ['있다.','있습니다.'],['없다.','없습니다.'],['다르다.','다릅니다.'],['중요하다.','중요합니다.'],['필요하다.','필요합니다.'],['가능하다.','가능합니다.'],['분명하다.','분명합니다.'],['자연스럽다.','자연스럽습니다.'],['가깝다.','가깝습니다.'],['넓다.','넓습니다.'],['좁다.','좁습니다.'],['깊다.','깊습니다.']
];
const removable = new Set(['### 한 문장 핵심','### 핵심 해설']);
function protectInline(line){
  const saved=[]; let s=line;
  for(const p of [/`[^`]*`/g,/“[^”]*”/g,/‘[^’]*’/g,/"[^"\n]*"/g]) s=s.replace(p,m=>{const k=`\u0000${saved.length}\u0000`;saved.push(m);return k});
  return {s,saved};
}
function restoreInline(s,saved){return s.replace(/\u0000(\d+)\u0000/g,(_,i)=>saved[Number(i)])}
function polite(line){const {s,saved}=protectInline(line);let out=s;for(const [a,b] of rules)out=out.split(a).join(b);return restoreInline(out,saved)}
function naturalizeMarkdown(md){
  let fence=false;
  return md.split('\n').map(line=>{
    const t=line.trim();
    if(/^(```|~~~)/.test(t)){fence=!fence;return line}
    if(fence||!t)return line;
    if(removable.has(t))return '';
    if(t==='### 전체 가르침과의 연결')return '### 다른 가르침과 어떻게 연결되는가';
    if(/^#{1,6}\s/.test(t)||/^>/.test(t)||/^\|/.test(t)||/^[|:-]+$/.test(t)||/\[원문\]/.test(t))return line;
    // 시리아어 문자가 중심인 행도 그대로 둡니다.
    if(/[\u0700-\u074F]/.test(t) && !/[가-힣]/.test(t))return line;
    return polite(line);
  }).join('\n').replace(/\n{3,}/g,'\n\n');
}
function enhance(){content.querySelectorAll('a').forEach(a=>{if(/^https?:\/\//i.test(a.getAttribute('href')||'')){a.target='_blank';a.rel='noopener'}});content.querySelectorAll('table').forEach(t=>t.setAttribute('role','table'))}

async function loadChapter(n){
  const ch=chapters[n-1]; setActiveNav(n); updatePager(n); badge.textContent=`${n}강 / 12강`; statusEl.textContent='불러오는 중…';
  document.title=`${n}강 · ${ch.title} | 예수 그리스도의 가르침 완전입문`; content.innerHTML='<div class="loading-card">본문을 불러오고 있습니다.</div>'; closeMenu();
  try{
    const r=await fetch(`./content/${encodeURIComponent(ch.file)}`,{cache:'no-cache'}); if(!r.ok)throw new Error(`HTTP ${r.status}`);
    const md=await r.text(); if(!window.marked||!window.DOMPurify)throw new Error('Markdown renderer unavailable');
    marked.setOptions({gfm:true,breaks:false});
    content.innerHTML=DOMPurify.sanitize(marked.parse(naturalizeMarkdown(md)),{USE_PROFILES:{html:true}}); enhance();
    statusEl.textContent=`예상 읽기 ${estimateMinutes(md)}분 · 자연스러운 해설체`; window.scrollTo({top:0,behavior:'auto'}); requestAnimationFrame(updateProgress);
  }catch(e){console.error(e);content.innerHTML='<div class="error-card"><strong>본문을 불러오지 못했습니다.</strong><br>새로고침하거나 GitHub 원문에서 확인해 주세요.</div>';statusEl.textContent='불러오기 실패'}
}
function openMenu(){sidebar.classList.add('open');scrim.hidden=false;menuButton?.setAttribute('aria-expanded','true');document.body.style.overflow='hidden'}
function closeMenu(){sidebar.classList.remove('open');scrim.hidden=true;menuButton?.setAttribute('aria-expanded','false');document.body.style.overflow=''}
function applyTheme(theme){document.documentElement.dataset.theme=theme;localStorage.setItem('jesus-book-theme',theme);themeButton.textContent=theme==='dark'?'☀':'◐'}
function toggleTheme(){applyTheme(document.documentElement.dataset.theme==='dark'?'light':'dark')}
function updateProgress(){const h=document.documentElement;const max=h.scrollHeight-h.clientHeight;progress.style.width=`${max>0?Math.min(100,(h.scrollTop/max)*100):0}%`}

navMarkup();
menuButton?.addEventListener('click',openMenu); closeMenuButton?.addEventListener('click',closeMenu); scrim?.addEventListener('click',closeMenu); themeButton?.addEventListener('click',toggleTheme);
window.addEventListener('hashchange',()=>loadChapter(chapterFromHash())); window.addEventListener('scroll',updateProgress,{passive:true}); window.addEventListener('resize',()=>{updateProgress();if(innerWidth>900)closeMenu()});
const savedTheme=localStorage.getItem('jesus-book-theme');applyTheme(savedTheme||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'));
if(!location.hash)location.hash='chapter=1';else loadChapter(chapterFromHash());
