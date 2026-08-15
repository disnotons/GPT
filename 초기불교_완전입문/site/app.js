const chapters = [
  { n: 1, title: '부처님은 무엇을 가르치려 했는가', file: '1강_부처님은_무엇을_가르치려_했는가_통합정제본.md' },
  { n: 2, title: '무엇을 믿고 무엇을 의심해야 하는가', file: '2강_무엇을_믿고_무엇을_의심해야_하는가_통합정제본.md' },
  { n: 3, title: '행동은 어떻게 판단하는가 — 윤리와 업', file: '3강_행동은_어떻게_판단하는가_윤리와_업_통합정제본.md' },
  { n: 4, title: '사성제와 중도 — 문제·원인·해결·길', file: '4강_사성제와_중도_통합정제본.md' },
  { n: 5, title: '연기 — 조건이 있으면 생기고 조건이 사라지면 사라진다', file: '5강_연기_조건이_있으면_생기고_조건이_사라지면_사라진다_통합정제본.md' },
  { n: 6, title: '나는 무엇을 ‘나’라고 붙잡는가 — 오온과 무아', file: '6강_나는_무엇을_나라고_붙잡는가_오온과_무아_통합정제본.md' },
  { n: 7, title: '수행의 전체 과정 — 점진적 훈련', file: '7강_수행의_전체_과정_점진적_훈련_통합정제본.md' },
  { n: 8, title: '호흡과 마음챙김 — 마음을 어떻게 훈련하는가', file: '8강_호흡과_마음챙김_마음을_어떻게_훈련하는가_통합정제본.md' },
  { n: 9, title: '자애와 분노 — 다른 존재를 어떻게 대하는가', file: '9강_자애와_분노_다른_존재를_어떻게_대하는가_통합정제본.md' },
  { n: 10, title: '재가자의 삶 — 가족·친구·경제·책임', file: '10강_재가자의_삶_가족_친구_경제_책임_통합정제본.md' },
  { n: 11, title: '열반 — 무엇이 끝나는가', file: '11강_열반_무엇이_끝나는가_통합정제본.md' },
  { n: 12, title: '본 것에서 단지 봄 — 집착 없는 인식', file: '12강_본_것에서_단지_봄_집착_없는_인식_통합정제본.md' },
  { n: 13, title: '전체 통합 — 초기불교 수행의 전체 지도', file: '13강_전체_통합_초기불교_수행의_전체_지도_통합정제본.md' }
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

let currentChapter = 1;

function navMarkup() {
  nav.innerHTML = chapters.map(ch => `
    <a class="chapter-link" data-chapter="${ch.n}" href="#chapter=${ch.n}">
      <span class="chapter-no">${String(ch.n).padStart(2, '0')}강</span>
      <span class="chapter-title">${ch.title}</span>
    </a>
  `).join('');
}

function chapterFromHash() {
  const match = location.hash.match(/chapter=(\d+)/);
  const n = match ? Number(match[1]) : 1;
  return Math.min(13, Math.max(1, Number.isFinite(n) ? n : 1));
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
  return `<span class="pager-eyebrow">${label}</span><span class="pager-title">${chapter.n}강 · ${chapter.title}</span>`;
}

function updatePager(n) {
  const prev = chapters[n - 2];
  const next = chapters[n];

  prevButton.disabled = !prev;
  nextButton.disabled = !next;
  prevButton.innerHTML = prev ? pagerHTML('← 이전 강', prev) : '<span class="pager-eyebrow">처음입니다</span>';
  nextButton.innerHTML = next ? pagerHTML('다음 강 →', next) : '<span class="pager-eyebrow">마지막 강입니다</span>';

  prevButton.onclick = prev ? () => { location.hash = `chapter=${prev.n}`; } : null;
  nextButton.onclick = next ? () => { location.hash = `chapter=${next.n}`; } : null;
}

function estimateMinutes(markdown) {
  const compact = markdown.replace(/[`#>*_\-|\[\]()]/g, '').replace(/\s+/g, '');
  return Math.max(1, Math.round(compact.length / 500));
}

// 원본 Markdown은 그대로 보존하고, 웹북에서 읽을 때만 문장을 부드러운 존댓말 해설체로 바꿉니다.
// 경전 인용, [원문] 표기, 코드, 표, 제목은 손대지 않습니다.
const endingRules = [
  ['것이다.', '것입니다.'], ['때문이다.', '때문입니다.'], ['구조다.', '구조입니다.'],
  ['과정이다.', '과정입니다.'], ['방향이다.', '방향입니다.'], ['방식이다.', '방식입니다.'],
  ['훈련이다.', '훈련입니다.'], ['문제다.', '문제입니다.'], ['사람이다.', '사람입니다.'],
  ['끝이다.', '끝입니다.'], ['뜻이다.', '뜻입니다.'], ['아니다.', '아닙니다.'], ['이다.', '입니다.'],
  ['있었다.', '있었습니다.'], ['배웠다.', '배웠습니다.'], ['않는다.', '않습니다.'],
  ['보여준다.', '보여줍니다.'], ['가르친다.', '가르칩니다.'], ['알아차린다.', '알아차립니다.'],
  ['설명한다.', '설명합니다.'], ['관찰한다.', '관찰합니다.'], ['훈련한다.', '훈련합니다.'],
  ['소멸한다.', '소멸합니다.'], ['제시한다.', '제시합니다.'], ['포함한다.', '포함합니다.'],
  ['연결한다.', '연결합니다.'], ['시작한다.', '시작합니다.'], ['이해한다.', '이해합니다.'],
  ['경험한다.', '경험합니다.'], ['답한다.', '답합니다.'], ['말한다.', '말합니다.'],
  ['존재한다.', '존재합니다.'], ['한다.', '합니다.'], ['이어진다.', '이어집니다.'],
  ['연결된다.', '연결됩니다.'], ['생긴다.', '생깁니다.'], ['일어난다.', '일어납니다.'],
  ['끝난다.', '끝납니다.'], ['된다.', '됩니다.'], ['변한다.', '변합니다.'],
  ['커진다.', '커집니다.'], ['나온다.', '나옵니다.'], ['보인다.', '보입니다.'],
  ['본다.', '봅니다.'], ['살핀다.', '살핍니다.'], ['묻는다.', '묻습니다.'],
  ['다룬다.', '다룹니다.'], ['가리킨다.', '가리킵니다.'], ['만든다.', '만듭니다.'],
  ['준다.', '줍니다.'], ['둔다.', '둡니다.'], ['닦는다.', '닦습니다.'],
  ['기른다.', '기릅니다.'], ['나아간다.', '나아갑니다.'], ['간다.', '갑니다.'],
  ['바란다.', '바랍니다.'], ['사용한다.', '사용합니다.'], ['안다.', '압니다.'],
  ['있다.', '있습니다.'], ['없다.', '없습니다.'], ['다르다.', '다릅니다.'],
  ['중요하다.', '중요합니다.'], ['필요하다.', '필요합니다.'], ['가능하다.', '가능합니다.'],
  ['안전하다.', '안전합니다.'], ['비슷하다.', '비슷합니다.'], ['가깝다.', '가깝습니다.'],
  ['어렵다.', '어렵습니다.'], ['쉽다.', '쉽습니다.'], ['괜찮다.', '괜찮습니다.'], ['같다.', '같습니다.']
];

const removableHeadings = new Set([
  '### 한 문장 핵심',
  '### 핵심 해설'
]);

function protectInlineText(line) {
  const saved = [];
  const patterns = [
    /`[^`]*`/g,
    /“[^”]*”/g,
    /‘[^’]*’/g,
    /"[^"\n]*"/g
  ];

  let protectedLine = line;
  for (const pattern of patterns) {
    protectedLine = protectedLine.replace(pattern, match => {
      const key = `\u0000${saved.length}\u0000`;
      saved.push(match);
      return key;
    });
  }
  return { protectedLine, saved };
}

function restoreInlineText(line, saved) {
  return line.replace(/\u0000(\d+)\u0000/g, (_, index) => saved[Number(index)]);
}

function makePolite(line) {
  const { protectedLine, saved } = protectInlineText(line);
  let result = protectedLine;
  for (const [from, to] of endingRules) {
    result = result.split(from).join(to);
  }
  return restoreInlineText(result, saved);
}

function naturalizeMarkdown(markdown) {
  const lines = markdown.split('\n');
  let inFence = false;

  return lines.map(line => {
    const trimmed = line.trim();

    if (/^(```|~~~)/.test(trimmed)) {
      inFence = !inFence;
      return line;
    }
    if (inFence || !trimmed) return line;

    if (removableHeadings.has(trimmed)) return '';
    if (trimmed === '### 전체 가르침과의 연결') return '### 다른 가르침과 어떻게 연결되는가';

    // 구조와 원문성이 중요한 부분은 그대로 둡니다.
    if (/^#{1,6}\s/.test(trimmed)) return line;
    if (/^>/.test(trimmed)) return line;
    if (/^\|/.test(trimmed)) return line;
    if (/\[원문\]/.test(trimmed)) return line;

    return makePolite(line);
  }).join('\n').replace(/\n{3,}/g, '\n\n');
}

function enhanceRenderedContent() {
  content.querySelectorAll('a').forEach(a => {
    if (/^https?:\/\//i.test(a.getAttribute('href') || '')) {
      a.target = '_blank';
      a.rel = 'noopener';
    }
  });

  content.querySelectorAll('table').forEach(table => {
    table.setAttribute('role', 'table');
  });
}

async function loadChapter(n) {
  currentChapter = n;
  const chapter = chapters[n - 1];
  setActiveNav(n);
  updatePager(n);
  badge.textContent = `${n}강 / 13강`;
  statusEl.textContent = '불러오는 중…';
  document.title = `${n}강 · ${chapter.title} | 초기불교 완전입문`;
  content.innerHTML = '<div class="loading-card">본문을 불러오고 있습니다.</div>';
  closeMenu();

  try {
    const url = `./content/${encodeURIComponent(chapter.file)}`;
    const response = await fetch(url, { cache: 'no-cache' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const markdown = await response.text();

    if (!window.marked || !window.DOMPurify) {
      throw new Error('Markdown renderer unavailable');
    }

    marked.setOptions({ gfm: true, breaks: false });
    const readingMarkdown = naturalizeMarkdown(markdown);
    const rendered = marked.parse(readingMarkdown);
    content.innerHTML = DOMPurify.sanitize(rendered, { USE_PROFILES: { html: true } });
    enhanceRenderedContent();
    statusEl.textContent = `예상 읽기 ${estimateMinutes(markdown)}분 · 읽기체`;

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

function applyTheme(theme) {
  if (theme === 'dark') document.documentElement.dataset.theme = 'dark';
  else document.documentElement.removeAttribute('data-theme');
  localStorage.setItem('early-buddhism-theme', theme);
  themeButton.textContent = theme === 'dark' ? '☀' : '◐';
}

function initTheme() {
  const saved = localStorage.getItem('early-buddhism-theme');
  if (saved === 'dark' || saved === 'light') {
    applyTheme(saved);
    return;
  }
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  applyTheme(prefersDark ? 'dark' : 'light');
}

function updateProgress() {
  const articleTop = content.offsetTop;
  const articleHeight = content.offsetHeight;
  const viewport = window.innerHeight;
  const distance = Math.max(1, articleHeight - viewport + articleTop);
  const pct = Math.min(100, Math.max(0, ((window.scrollY - articleTop + 24) / distance) * 100));
  progress.style.width = `${pct}%`;
}

navMarkup();
initTheme();

menuButton?.addEventListener('click', openMenu);
closeMenuButton?.addEventListener('click', closeMenu);
scrim.addEventListener('click', closeMenu);
themeButton.addEventListener('click', () => {
  const dark = document.documentElement.dataset.theme === 'dark';
  applyTheme(dark ? 'light' : 'dark');
});

window.addEventListener('hashchange', () => loadChapter(chapterFromHash()));
window.addEventListener('scroll', updateProgress, { passive: true });
window.addEventListener('resize', () => {
  if (window.innerWidth > 900) closeMenu();
  updateProgress();
});

if (!location.hash) location.hash = 'chapter=1';
else loadChapter(chapterFromHash());
