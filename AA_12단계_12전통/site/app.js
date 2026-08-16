const state={manifest:null,docs:[],index:0};
const $=s=>document.querySelector(s);
const article=$('#article'),toc=$('#toc'),prev=$('#prevBtn'),next=$('#nextBtn');
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function fallback(md){return '<pre>'+esc(md)+'</pre>';}
function renderMarkdown(md){try{return window.marked?marked.parse(md,{gfm:true,breaks:false}):fallback(md)}catch(e){return fallback(md)}}
function makeToc(filter=''){
  toc.innerHTML=''; const q=filter.trim().toLowerCase();
  for(const section of state.manifest.sections){
    const items=section.items.filter(x=>!q||x.title.toLowerCase().includes(q)); if(!items.length)continue;
    const h=document.createElement('div');h.className='toc-section';h.textContent=section.title;toc.appendChild(h);
    for(const item of items){const i=state.docs.findIndex(d=>d.file===item.file);const a=document.createElement('a');a.href='#'+encodeURIComponent(item.file);a.textContent=item.title;a.dataset.index=i;a.onclick=e=>{e.preventDefault();openDoc(i);closeMenu()};toc.appendChild(a)}
  }
}
async function openDoc(i,push=true){
  if(i<0||i>=state.docs.length)return;state.index=i;const d=state.docs[i];article.innerHTML='<div class="loading">불러오는 중입니다…</div>';
  try{const r=await fetch('./content/'+encodeURIComponent(d.file));if(!r.ok)throw new Error(r.status);const md=await r.text();article.innerHTML=renderMarkdown(md);document.title=d.title+' · AA 웹북';if(push)history.replaceState(null,'','#'+encodeURIComponent(d.file));window.scrollTo({top:0,behavior:'instant'})}catch(e){article.innerHTML='<h1>문서를 불러오지 못했습니다</h1><p>페이지를 새로고침해 주세요.</p>'}
  [...toc.querySelectorAll('a')].forEach(a=>a.classList.toggle('active',Number(a.dataset.index)===i));prev.disabled=i===0;next.disabled=i===state.docs.length-1;updateProgress();
}
function updateProgress(){const de=document.documentElement;const max=de.scrollHeight-innerHeight;const pct=max>0?scrollY/max*100:0;$('#progress').style.width=Math.max(0,Math.min(100,pct))+'%'}
function openMenu(){$('#sidebar').classList.add('open');$('#scrim').classList.add('show')}
function closeMenu(){$('#sidebar').classList.remove('open');$('#scrim').classList.remove('show')}
function theme(t){document.documentElement.dataset.theme=t;localStorage.setItem('aa-theme',t)}
async function init(){
  const r=await fetch('./manifest.json');state.manifest=await r.json();state.docs=state.manifest.sections.flatMap(s=>s.items);makeToc();
  const hash=decodeURIComponent(location.hash.slice(1));let i=state.docs.findIndex(d=>d.file===hash);if(i<0)i=0;openDoc(i,false);
}
$('#filter').addEventListener('input',e=>makeToc(e.target.value));$('#menuBtn').onclick=openMenu;$('#closeBtn').onclick=closeMenu;$('#scrim').onclick=closeMenu;prev.onclick=()=>openDoc(state.index-1);next.onclick=()=>openDoc(state.index+1);$('#themeBtn').onclick=()=>theme(document.documentElement.dataset.theme==='dark'?'light':'dark');window.addEventListener('scroll',updateProgress,{passive:true});theme(localStorage.getItem('aa-theme')||((matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light'));init().catch(()=>article.innerHTML='<h1>웹북을 시작하지 못했습니다</h1><p>잠시 후 다시 열어 주세요.</p>');
