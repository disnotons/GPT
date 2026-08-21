const p=new URLSearchParams(location.search);
const n=Math.max(1,Math.min(50,Number(p.get('vol')||1)));
const v=SA_VOLUMES.find(x=>x[0]===n);
const content=document.getElementById('content');
const meta=document.getElementById('meta');
const nav=document.getElementById('volNav');
const theme=document.getElementById('themeButton');
const prog=document.getElementById('readProgress');

const SPLIT_VOLUMES={
  7:['07.seg1.mdpart','07.seg2.mdpart','07.seg3a.mdpart','07.seg3b.mdpart'],
  8:['08.seg1.mdpart','08.seg2.mdpart','08.seg3.mdpart'],
  9:['09.seg1.mdpart','09.seg2.mdpart','09.seg3.mdpart'],
  10:['10.seg1.mdpart','10.seg2.mdpart','10.seg3.mdpart']
};

function navHtml(){
  return SA_VOLUMES.map(x=>x[4]==='published'
    ?`<a class="${x[0]===n?'active':''}" href="?vol=${x[0]}"><b>제${x[0]}권</b><span>${x[1]}~${x[2]}경</span></a>`
    :`<span class="disabled"><b>제${x[0]}권</b><span>${x[1]}~${x[2]}경</span></span>`).join('');
}
nav.innerHTML=navHtml();
meta.innerHTML=`<span>제${v[0]}권 / 50권</span><b>제${v[1]}~${v[2]}경 · ${v[3]}경 수록</b>`;
document.getElementById('barTitle').textContent=`제${v[0]}권 · 잡아함경 쉬운 완전읽기`;
document.title=`제${v[0]}권 | 잡아함경 쉬운 완전읽기`;

async function fetchText(path){
  const r=await fetch(`./volumes/${path}`,{cache:'no-cache'});
  if(!r.ok)throw new Error(`${path}: ${r.status}`);
  return r.text();
}

async function load(){
  if(v[4]!=='published'){
    content.innerHTML='<div class="loading">이 권의 통합 해설은 아직 준비 중입니다.</div>';
    return;
  }
  try{
    const parts=SPLIT_VOLUMES[v[0]];
    const md=parts
      ?(await Promise.all(parts.map(fetchText))).join('\n')
      :await fetchText(`${String(v[0]).padStart(2,'0')}.md`);
    marked.setOptions({gfm:true});
    content.innerHTML=DOMPurify.sanitize(marked.parse(md),{USE_PROFILES:{html:true}});
  }catch(e){
    console.error(e);
    content.innerHTML='<div class="loading">본문을 불러오지 못했습니다.</div>';
  }
}

function pager(id,label,x){
  const el=document.getElementById(id);
  if(!x){el.className='disabled-link';el.textContent=label;return;}
  el.href=`?vol=${x[0]}`;
  el.innerHTML=`<small>${label}</small><b>제${x[0]}권 · 제${x[1]}~${x[2]}경</b>`;
}
const published=SA_VOLUMES.filter(x=>x[4]==='published');
const i=published.findIndex(x=>x[0]===n);
pager('prev','← 이전 공개 권',published[i-1]);
pager('next','다음 공개 권 →',published[i+1]);

theme.addEventListener('click',()=>{
  document.body.classList.toggle('dark');
  localStorage.setItem('sa-volume-theme',document.body.classList.contains('dark')?'dark':'light');
});
if(localStorage.getItem('sa-volume-theme')==='dark')document.body.classList.add('dark');
addEventListener('scroll',()=>{
  const m=document.documentElement.scrollHeight-innerHeight;
  prog.style.width=(m>0?Math.min(100,scrollY/m*100):0)+'%';
},{passive:true});
load();
