const books = [
  { n: 0, short: '서두', title: '0.1 작품 서두 — 사랑하는 영혼의 계시와 책의 탄생', parts: 1 },
  { n: 1, short: 'Buch I', title: '사랑에 붙잡힌 영혼과 하느님의 첫 만남', parts: 4 },
  { n: 2, short: 'Buch II', title: '사랑이 영혼을 변화시키는 방식', parts: 4 },
  { n: 3, short: 'Buch III', title: '갈망, 고통, 사랑과 영적 전투', parts: 5 },
  { n: 4, short: 'Buch IV', title: '순수한 사랑, 교회, 수도생활과 종말', parts: 5 },
  { n: 5, short: 'Buch V', title: '회개, 사랑, 교회와 마지막 길', parts: 6 },
  { n: 6, short: 'Buch VI', title: '공동체, 의지, 고통과 하느님의 응시', parts: 7 },
  { n: 7, short: 'Buch VII', title: '수도공동체의 일상에서 마지막 계시까지', parts: 10 }
];

const nav = document.getElementById('bookNav');
const content = document.getElementById('content');
const badge = document.getElementById('bookBadge');
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
  nav.innerHTML = books.map((b, i) => `
    <a class="chapter-link" data-index="${i}" href="#book=${b.n}">
      <span class="chapter-no">${b.short}</span>
      <span class="chapter-title">${b.title}</span>
    </a>
  `).join('');
}

function indexFromHash() {
  const m = location.hash.match(/book=(\d+)/);
  const n = m ? Number(m[1]) : 0;
  const idx = books.findIndex(b => b.n === n);
  return idx >= 0 ? idx : 0;
}

function setActiveNav(index) {
  document.querySelectorAll('.chapter-link').forEach(link => {
    const active = Number(link.dataset.index) === index;
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });
}

function pagerHTML(label, b) {
  if (!b) return '';
  return `<span class="pager-eyebrow">${label}</span><span class="pager-title">${b.short} · ${b.title}</span>`;
}

function updatePager(index) {
  const prev = books[index - 1];
  const next = books[index + 1];
  prevButton.disabled = !prev;
  nextButton.disabled = !next;
  prevButton.innerHTML = prev ? pagerHTML('← 이전', prev) : '<span class="pager-eyebrow">처음입니다</span>';
  nextButton.innerHTML = next ? pagerHTML('다음 →', next) : '<span class="pager-eyebrow">마지막입니다</span>';
  prevButton.onclick = prev ? () => { location.hash = `book=${prev.n}`; } : null;
  nextButton.onclick = next ? () => { location.hash = `book=${next.n}`; } : null;
}

function estimateMinutes(markdown) {
  const compact = markdown.replace(/[`#>*_\-|\[\]()]/g, '').replace(/\s+/g, '');
  return Math.max(1, Math.round(compact.length / 500));
}

function base64ToBytes(base64) {
  const clean = base64.replace(/\s+/g, '');
  const binary = atob(clean);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

async function gunzipBase64(base64) {
  if (!('DecompressionStream' in window)) {
    throw new Error('이 브라우저는 압축 본문 복원을 지원하지 않습니다. 최신 Chrome, Edge, Firefox 또는 Safari를 사용해 주세요.');
  }
  const compressed = base64ToBytes(base64);
  const stream = new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'));
  return await new Response(stream).text();
}

async function fetchEncodedBook(book) {
  const requests = [];
  for (let i = 1; i <= book.parts; i++) {
    const part = String(i).padStart(2, '0');
    requests.push(fetch(`./content/book-${book.n}/part-${part}.b64`, { cache: 'no-cache' }));
  }
  const responses = await Promise.all(requests);
  for (const response of responses) {
    if (!response.ok) throw new Error(`본문 파트 불러오기 실패: HTTP ${response.status}`);
  }
  const texts = await Promise.all(responses.map(r => r.text()));
  return texts.join('');
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

async function loadBook(index) {
  const book = books[index];
  setActiveNav(index);
  updatePager(index);
  badge.textContent = `${book.short} · ${index + 1} / ${books.length}`;
  statusEl.textContent = '불러오는 중…';
  document.title = `${book.short} · ${book.title} | 『신성의 흐르는 빛』`;
  content.innerHTML = '<div class="loading-card">본문을 불러오고 있습니다.</div>';
  closeMenu();
  try {
    const encoded = await fetchEncodedBook(book);
    const markdown = await gunzipBase64(encoded);
    if (!window.marked || !window.DOMPurify) throw new Error('Markdown renderer unavailable');
    marked.setOptions({ gfm: true, breaks: false });
    const rendered = marked.parse(markdown);
    content.innerHTML = DOMPurify.sanitize(rendered, { USE_PROFILES: { html: true } });
    enhanceRenderedContent();
    statusEl.textContent = `예상 읽기 ${estimateMinutes(markdown)}분 · 최종감수본`;
    window.scrollTo({ top: 0, behavior: 'auto' });
    requestAnimationFrame(updateProgress);
  } catch (error) {
    console.error(error);
    content.innerHTML = `<div class="error-card"><strong>본문을 불러오지 못했습니다.</strong><br>${error.message || '새로고침해 주세요.'}</div>`;
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
  const doc = document.documentElement;
  const max = Math.max(1, doc.scrollHeight - window.innerHeight);
  progress.style.width = `${Math.min(100, Math.max(0, window.scrollY / max * 100))}%`;
}
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem('mechthild-theme', theme);
}
function toggleTheme() {
  applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
}

navMarkup();
menuButton?.addEventListener('click', openMenu);
closeMenuButton?.addEventListener('click', closeMenu);
scrim?.addEventListener('click', closeMenu);
themeButton?.addEventListener('click', toggleTheme);
window.addEventListener('scroll', updateProgress, { passive: true });
window.addEventListener('resize', updateProgress);
window.addEventListener('hashchange', () => loadBook(indexFromHash()));

const savedTheme = localStorage.getItem('mechthild-theme');
if (savedTheme === 'dark' || savedTheme === 'light') applyTheme(savedTheme);
else applyTheme(window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');

loadBook(indexFromHash());
