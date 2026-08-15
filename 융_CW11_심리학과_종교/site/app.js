const chapters = [
  { n: 1, title: '심리학과 종교 — 1.1–1.3', file: 'CW11_1_심리학과종교_1.1-1.3_통합정제본.md' },
  { n: 2, title: '삼위일체 교리에 대한 심리학적 접근', file: 'CW11_2_삼위일체_교리에_대한_심리학적_접근_통합정제본.md' },
  { n: 3, title: '미사에서의 변환 상징', file: 'CW11_3_미사에서의_변환_상징_통합정제본.md' },
  { n: 4, title: '기독교·악·종교심리학', file: 'CW11_4_기독교_악_종교심리학_통합정제본.md' },
  { n: 5, title: '심리치료와 종교', file: 'CW11_5_심리치료와_종교_통합정제본.md' },
  { n: 6, title: '욥에게 답하다', file: 'CW11_6_욥에게_답하다_통합정제본.md' },
  { n: 7, title: '티베트 종교문헌에 대한 심리학적 주석', file: 'CW11_7_티베트_종교문헌_심리학적주석_통합정제본.md' },
  { n: 8, title: '요가·선·명상·인도 성자', file: 'CW11_8_요가_선_명상_인도성자_통합정제본.md' },
  { n: 9, title: '주역과 동시성', file: 'CW11_9_주역과_동시성_통합정제본.md' }
];

const nav = document.getElementById('chapterNav');
const content = document.getElementById('content');
const badge = document.getElementById('chapterBadge');
const statusEl = document.getElementById('readingStatus');
const prevButton = document.getElementById('prevButton');
const nextButton = document.getElementById('nextButton');
const sidebar = document.getElementById('sidebar');
const scrim = document.getElementById('scrim');
const menuButton = document.getElementById('menuButton');
const closeMenuButton = document.getElementById('closeMenuButton');
const themeButton = document.getElementById('themeButton');
const progress = document.getElementById('progress');

function navMarkup() {
  nav.innerHTML = chapters.map(ch => `
    <a class="chapter-link" data-chapter="${ch.n}" href="#chapter=${ch.n}">
      <span class="chapter-no">${String(ch.n).padStart(2, '0')}</span>
      <span class="chapter-title">${ch.title}</span>
    </a>
  `).join('');
}

function chapterFromHash() {
  const match = location.hash.match(/chapter=(\d+)/);
  const n = match ? Number(match[1]) : 1;
  return Math.min(chapters.length, Math.max(1, Number.isFinite(n) ? n : 1));
}

function setActiveNav(n) {
  document.querySelectorAll('.chapter-link').forEach(link => {
    const active = Number(link.dataset.chapter) === n;
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });
}

function pagerHTML(label, chapter) {
  if (!chapter) return '';
  return `<span class="pager-eyebrow">${label}</span><span class="pager-title">${chapter.n}부 · ${chapter.title}</span>`;
}

function updatePager(n) {
  const prev = chapters[n - 2];
  const next = chapters[n];
  prevButton.disabled = !prev;
  nextButton.disabled = !next;
  prevButton.innerHTML = prev ? pagerHTML('← 이전', prev) : '<span class="pager-eyebrow">처음입니다</span>';
  nextButton.innerHTML = next ? pagerHTML('다음 →', next) : '<span class="pager-eyebrow">마지막입니다</span>';
  prevButton.onclick = prev ? () => { location.hash = `chapter=${prev.n}`; } : null;
  nextButton.onclick = next ? () => { location.hash = `chapter=${next.n}`; } : null;
}

function estimateMinutes(markdown) {
  const compact = markdown.replace(/[`#>*_\-|\[\]()]/g, '').replace(/\s+/g, '');
  return Math.max(1, Math.round(compact.length / 500));
}

function enhanceRenderedContent() {
  content.querySelectorAll('a').forEach(a => {
    if (/^https?:\/\//i.test(a.getAttribute('href') || '')) {
      a.target = '_blank';
      a.rel = 'noopener';
    }
  });
  content.querySelectorAll('table').forEach(table => table.setAttribute('role', 'table'));
}

async function loadChapter(n) {
  const chapter = chapters[n - 1];
  setActiveNav(n);
  updatePager(n);
  badge.textContent = `${n}부 / ${chapters.length}부`;
  statusEl.textContent = '불러오는 중…';
  document.title = `${n}부 · ${chapter.title} | C. G. Jung CW 11`;
  content.innerHTML = '<div class="loading-card">본문을 불러오고 있습니다.</div>';
  closeMenu();

  try {
    const response = await fetch(`./content/${encodeURIComponent(chapter.file)}`, { cache: 'no-cache' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const markdown = await response.text();
    if (!window.marked || !window.DOMPurify) throw new Error('Markdown renderer unavailable');
    marked.setOptions({ gfm: true, breaks: false });
    const rendered = marked.parse(markdown);
    content.innerHTML = DOMPurify.sanitize(rendered, { USE_PROFILES: { html: true } });
    enhanceRenderedContent();
    statusEl.textContent = `예상 읽기 ${estimateMinutes(markdown)}분 · 원문 보존`;
    window.scrollTo({ top: 0, behavior: 'auto' });
    requestAnimationFrame(updateProgress);
  } catch (error) {
    console.error(error);
    content.innerHTML = '<div class="error-card"><strong>본문을 불러오지 못했습니다.</strong><br>새로고침하거나 GitHub 원문에서 확인해 주세요.</div>';
    statusEl.textContent = '불러오기 실패';
  }
}

function openMenu() {
  sidebar.classList.add('open');
  scrim.hidden = false;
  menuButton?.setAttribute('aria-expanded', 'true');
  document.body.style.overflow = 'hidden';
}

function closeMenu() {
  sidebar.classList.remove('open');
  scrim.hidden = true;
  menuButton?.setAttribute('aria-expanded', 'false');
  document.body.style.overflow = '';
}

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem('cw11-theme', theme);
}

function toggleTheme() {
  const current = document.documentElement.dataset.theme || 'light';
  setTheme(current === 'dark' ? 'light' : 'dark');
}

function updateProgress() {
  const max = document.documentElement.scrollHeight - window.innerHeight;
  const value = max > 0 ? Math.min(100, Math.max(0, (window.scrollY / max) * 100)) : 0;
  progress.style.width = `${value}%`;
}

navMarkup();
setTheme(localStorage.getItem('cw11-theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
menuButton?.addEventListener('click', openMenu);
closeMenuButton?.addEventListener('click', closeMenu);
scrim?.addEventListener('click', closeMenu);
themeButton?.addEventListener('click', toggleTheme);
window.addEventListener('hashchange', () => loadChapter(chapterFromHash()));
window.addEventListener('scroll', updateProgress, { passive: true });
window.addEventListener('resize', updateProgress);
loadChapter(chapterFromHash());
