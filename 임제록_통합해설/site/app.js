const parts = [
  { n: 1, title: '시중(示衆) — 핵심 가르침', range: '1.1–1.18', file: '임제록_제1부_시중_1.1-1.18_최종감수본.md' },
  { n: 2, title: '상당(上堂) — 선문답의 작동', range: '2.1–2.13', file: '임제록_제2부_상당_2.1-2.13_최종감수본.md' },
  { n: 3, title: '감변(勘辨) — 이해 점검', range: '3.1–3.13', file: '임제록_제3부_감변_3.1-3.13_최종감수본.md' },
  { n: 4, title: '행록(行錄) — 구도와 법맥', range: '4.1–4.15', file: '임제록_제4부_행록_4.1-4.15_최종감수본.md' },
  { n: 5, title: '전체 통합', range: '5.1–5.12', file: '임제록_제5부_전체통합_5.1-5.12_최종감수본.md' }
];

const nav = document.getElementById('partNav');
const content = document.getElementById('content');
const badge = document.getElementById('partBadge');
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
  nav.innerHTML = parts.map(part => `
    <a class="chapter-link" data-part="${part.n}" href="#part=${part.n}">
      <span class="chapter-no">제${part.n}부</span>
      <span class="chapter-title">${part.title}<small>${part.range}</small></span>
    </a>
  `).join('');
}

function partFromHash() {
  const match = location.hash.match(/part=(\d+)/);
  const n = match ? Number(match[1]) : 1;
  return Math.min(parts.length, Math.max(1, Number.isFinite(n) ? n : 1));
}

function setActiveNav(n) {
  document.querySelectorAll('.chapter-link').forEach(link => {
    const active = Number(link.dataset.part) === n;
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });
}

function pagerHTML(label, part) {
  if (!part) return '';
  return `<span class="pager-eyebrow">${label}</span><span class="pager-title">제${part.n}부 · ${part.title}</span>`;
}

function updatePager(n) {
  const prev = parts[n - 2];
  const next = parts[n];

  prevButton.disabled = !prev;
  nextButton.disabled = !next;
  prevButton.innerHTML = prev ? pagerHTML('← 이전 부', prev) : '<span class="pager-eyebrow">처음입니다</span>';
  nextButton.innerHTML = next ? pagerHTML('다음 부 →', next) : '<span class="pager-eyebrow">마지막입니다</span>';

  prevButton.onclick = prev ? () => { location.hash = `part=${prev.n}`; } : null;
  nextButton.onclick = next ? () => { location.hash = `part=${next.n}`; } : null;
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

  content.querySelectorAll('table').forEach(table => {
    if (table.parentElement?.classList.contains('table-wrap')) return;
    const wrap = document.createElement('div');
    wrap.className = 'table-wrap';
    table.parentNode.insertBefore(wrap, table);
    wrap.appendChild(table);
  });
}

async function loadPart(n) {
  const part = parts[n - 1];
  setActiveNav(n);
  updatePager(n);
  badge.textContent = `제${n}부 / ${parts.length}부`;
  statusEl.textContent = '불러오는 중…';
  document.title = `제${n}부 · ${part.title} | 『임제록』 통합 해설`;
  content.innerHTML = '<div class="loading-card">본문을 불러오고 있습니다.</div>';
  closeMenu();

  try {
    const url = `./content/${encodeURIComponent(part.file)}`;
    const response = await fetch(url, { cache: 'no-cache' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const markdown = await response.text();

    if (!window.marked || !window.DOMPurify) {
      throw new Error('Markdown renderer unavailable');
    }

    marked.setOptions({ gfm: true, breaks: false });
    const rendered = marked.parse(markdown);
    content.innerHTML = DOMPurify.sanitize(rendered, { USE_PROFILES: { html: true } });
    enhanceRenderedContent();
    statusEl.textContent = `예상 읽기 ${estimateMinutes(markdown)}분 · 최종감수본 원문 그대로`;

    window.scrollTo({ top: 0, behavior: 'auto' });
    requestAnimationFrame(updateProgress);
  } catch (error) {
    console.error(error);
    content.innerHTML = `
      <div class="error-card">
        <strong>본문을 불러오지 못했습니다.</strong><br />
        새로고침하거나 GitHub 원문에서 확인해 주세요.
      </div>`;
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

function updateProgress() {
  const root = document.documentElement;
  const max = root.scrollHeight - window.innerHeight;
  const value = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
  progress.style.transform = `scaleX(${value})`;
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem('linji-theme', theme);
  themeButton.textContent = theme === 'dark' ? '☀' : '◐';
  themeButton.title = theme === 'dark' ? '밝은 화면으로' : '어두운 화면으로';
}

function initTheme() {
  const saved = localStorage.getItem('linji-theme');
  if (saved === 'dark' || saved === 'light') {
    applyTheme(saved);
    return;
  }
  const dark = window.matchMedia?.('(prefers-color-scheme: dark)').matches;
  applyTheme(dark ? 'dark' : 'light');
}

function handleHash() {
  loadPart(partFromHash());
}

navMarkup();
initTheme();
handleHash();

window.addEventListener('hashchange', handleHash);
window.addEventListener('scroll', updateProgress, { passive: true });
window.addEventListener('resize', updateProgress);
menuButton?.addEventListener('click', openMenu);
closeMenuButton?.addEventListener('click', closeMenu);
scrim?.addEventListener('click', closeMenu);
themeButton?.addEventListener('click', () => {
  const current = document.documentElement.dataset.theme || 'light';
  applyTheme(current === 'dark' ? 'light' : 'dark');
});

document.addEventListener('keydown', event => {
  if (event.key === 'Escape') closeMenu();
  if (!event.altKey) return;
  const n = partFromHash();
  if (event.key === 'ArrowLeft' && n > 1) location.hash = `part=${n - 1}`;
  if (event.key === 'ArrowRight' && n < parts.length) location.hash = `part=${n + 1}`;
});
