#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

TARGET_CHARS = 85_000
HARD_CHARS = 105_000

TRUTH_TITLES = {
    1: "역사적 전망",
    2: "진실의 과학",
    3: "수수께끼로서의 진실: 도전과 투쟁",
    4: "의식의 진화",
    5: "진실의 본질적 구조",
    6: "나타남 대 인과관계: 창조 대 진화",
    7: "진실의 생리학",
    8: "사실 대 허구: 실상과 환상",
    9: "사회구조와 기능적 진실",
    10: "미국",
    11: "사회의 그늘",
    12: "문제 있는 쟁점들",
    13: "진실: 자유에 이르는 길",
    14: "국가와 정치",
    15: "진실과 전쟁",
    16: "종교와 진실",
    17: "영적 진실",
    18: "요약과 결론",
}

MODERN_TITLES = {
    1: "개관",
    2: "인간의 딜레마",
    3: "실재의 패러다임",
    4: "실재는 주관적인가, 객관적인가?",
    5: "과학과 종교: 진실 수준",
    6: "사회적 실재와 진실 수준",
    7: "무엇이 ‘진짜’인가?",
    8: "문화적 전제와 진실",
    9: "믿음",
    10: "경험적 요소 대 개념적 요소",
    11: "신념, 신뢰 그리고 신뢰도",
    12: "가설로서의 신",
    13: "의심, 회의론 그리고 불신",
    14: "영적 경로",
    15: "기도하는 사람 되기: 관상과 명상",
    16: "세상 초월하기",
    17: "도덕, 이성 그리고 믿음",
    18: "나르시시즘: 에고 숭배",
    19: "실습",
}

BOOKS = {
    "truth": {
        "slug": "truth-vs-falsehood-mobile",
        "title": "『진실 대 거짓』 — 제1~18장 전체 해설 웹북",
        "short": "『진실 대 거짓』",
        "titles": TRUTH_TITLES,
    },
    "modern": {
        "slug": "modern-consciousness-map-mobile",
        "title": "『현대인의 의식 지도』 — 제1~19장 전체 해설 웹북",
        "short": "『현대인의 의식 지도』",
        "titles": MODERN_TITLES,
    },
}

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
GPT_RE = re.compile(
    r"(?ms)^## GPT 답변 ·[^\n]*\n\s*(.*?)(?=^## (?:질문|GPT 답변) ·|\Z)"
)

@dataclass
class Conversation:
    cid: str
    date: str
    title: str
    path: Path
    text: str


def meta(text: str, key: str) -> str:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return ""
    fm = m.group(1)
    mm = re.search(rf"(?m)^{re.escape(key)}:\s*[\"']?(.*?)[\"']?\s*$", fm)
    return mm.group(1).strip() if mm else ""


def index_conversations(root: Path) -> dict[str, Conversation]:
    out: dict[str, Conversation] = {}
    for p in root.glob("*.md"):
        text = p.read_text(encoding="utf-8", errors="replace")
        cid = meta(text, "conversation_id")
        if not cid:
            continue
        if cid in out:
            raise RuntimeError(f"duplicate conversation_id: {cid}")
        out[cid] = Conversation(
            cid=cid,
            date=meta(text, "date"),
            title=meta(text, "title"),
            path=p,
            text=text,
        )
    return out


def extract_gpt_blocks(text: str) -> list[str]:
    blocks = [m.group(1).strip() for m in GPT_RE.finditer(text)]
    blocks = [b for b in blocks if b]
    if blocks:
        return blocks
    # Defensive fallback for older archive variants.
    fallback = re.compile(
        r"(?ms)^## (?:Assistant|답변)[^\n]*\n\s*(.*?)(?=^## (?:User|질문|Assistant|답변)[^\n]*|\Z)"
    )
    return [m.group(1).strip() for m in fallback.finditer(text) if m.group(1).strip()]


def date_key(value: str) -> tuple:
    try:
        return (0, datetime.fromisoformat(value))
    except Exception:
        return (1, value)


def split_large_block(block: str, limit: int = TARGET_CHARS) -> list[str]:
    if len(block) <= HARD_CHARS:
        return [block]
    paras = re.split(r"(\n\s*\n)", block)
    chunks: list[str] = []
    cur = ""
    for piece in paras:
        if cur and len(cur) + len(piece) > limit:
            chunks.append(cur.strip())
            cur = piece
        else:
            cur += piece
    if cur.strip():
        chunks.append(cur.strip())
    # Last-resort line split for an abnormally huge single paragraph.
    final: list[str] = []
    for chunk in chunks:
        if len(chunk) <= HARD_CHARS:
            final.append(chunk)
            continue
        lines = chunk.splitlines(keepends=True)
        part = ""
        for line in lines:
            if part and len(part) + len(line) > limit:
                final.append(part.rstrip())
                part = line
            else:
                part += line
        if part.strip():
            final.append(part.rstrip())
    return final


def pack_blocks(blocks: Iterable[str], limit: int = TARGET_CHARS) -> list[str]:
    expanded: list[str] = []
    for b in blocks:
        expanded.extend(split_large_block(b, limit))
    pages: list[str] = []
    cur: list[str] = []
    size = 0
    for b in expanded:
        add = len(b) + (6 if cur else 0)
        if cur and size + add > limit:
            pages.append("\n\n---\n\n".join(cur).strip())
            cur = [b]
            size = len(b)
        else:
            cur.append(b)
            size += add
    if cur:
        pages.append("\n\n---\n\n".join(cur).strip())
    return pages


def yaml_title(title: str) -> str:
    return json.dumps(title, ensure_ascii=False)


def style_block() -> str:
    return """<style>
.hawkins-mobile{max-width:820px;margin:0 auto;font-size:18px;line-height:1.82;word-break:keep-all;overflow-wrap:anywhere}
.hawkins-mobile h1,.hawkins-mobile h2,.hawkins-mobile h3{line-height:1.35;word-break:keep-all}
.hawkins-nav{display:flex;gap:.55rem;flex-wrap:wrap;margin:1rem 0 1.6rem;padding:.8rem 0;border-top:1px solid #ddd;border-bottom:1px solid #ddd}
.hawkins-nav a{display:inline-block;padding:.55rem .8rem;border:1px solid #bbb;border-radius:.6rem;text-decoration:none}
.hawkins-part{font-size:.92rem;opacity:.72;margin:.4rem 0 1.2rem}
.hawkins-toc li{margin:.45rem 0}
@media(max-width:640px){.hawkins-mobile{font-size:17px;line-height:1.76;padding:0 .1rem}.hawkins-nav a{padding:.55rem .7rem}}
</style>"""


def page_frontmatter(title: str) -> str:
    return f"---\nlayout: default\ntitle: {yaml_title(title)}\n---\n\n"


def chapter_nav(book_title: str, chapter: int, title: str, part: int, total: int) -> str:
    links = ["[← 책 목차](../)"]
    if part > 1:
        links.append("[← 이전](" + ("./" if part == 2 else f"part-{part-1:02d}.html") + ")")
    if part < total:
        links.append(f"[다음 →](part-{part+1:02d}.html)")
    nav = " · ".join(links)
    return (
        f"<div class=\"hawkins-mobile\" markdown=\"1\">\n"
        f"{style_block()}\n"
        f"<div class=\"hawkins-nav\">{nav}</div>\n\n"
        f"# {book_title} 제{chapter}장 「{title}」\n\n"
        f"<div class=\"hawkins-part\">모바일 분할 {part}/{total}</div>\n\n"
    )


def write_chapter(book_dir: Path, book_short: str, chapter: int, title: str, blocks: list[str]) -> dict:
    parts = pack_blocks(blocks)
    if not parts:
        raise RuntimeError(f"chapter {chapter} has no GPT answer content")
    chapter_dir = book_dir / f"chapter-{chapter:02d}"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    total = len(parts)
    max_chars = 0
    for idx, body in enumerate(parts, 1):
        max_chars = max(max_chars, len(body))
        page_title = f"{book_short} 제{chapter}장 「{title}」 {idx}/{total}" if total > 1 else f"{book_short} 제{chapter}장 「{title}」"
        name = "index.md" if idx == 1 else f"part-{idx:02d}.md"
        nav_top = chapter_nav(book_short, chapter, title, idx, total)
        nav_bottom_links = ["[← 책 목차](../)"]
        if idx > 1:
            nav_bottom_links.append("[← 이전](" + ("./" if idx == 2 else f"part-{idx-1:02d}.html") + ")")
        if idx < total:
            nav_bottom_links.append(f"[다음 →](part-{idx+1:02d}.html)")
        nav_bottom = " · ".join(nav_bottom_links)
        content = (
            page_frontmatter(page_title)
            + nav_top
            + body.strip()
            + f"\n\n<div class=\"hawkins-nav\">{nav_bottom}</div>\n</div>\n"
        )
        (chapter_dir / name).write_text(content, encoding="utf-8")
    return {"parts": total, "max_chars": max_chars, "chars": sum(len(p) for p in parts)}


def write_book_index(book_dir: Path, info: dict, stats: dict[int, dict]) -> None:
    lines = [
        page_frontmatter(info["title"]),
        '<div class="hawkins-mobile" markdown="1">',
        style_block(),
        f'# {info["title"]}',
        '',
        'Google Docs·워드를 거치지 않는 외부 모바일 읽기용 웹북입니다. 긴 장은 가벼운 여러 페이지로 자동 분할했습니다.',
        '',
        '## 목차',
        '',
        '<ol class="hawkins-toc">',
    ]
    for ch, title in info["titles"].items():
        parts = stats[ch]["parts"]
        suffix = f" · {parts}개 페이지" if parts > 1 else ""
        lines.append(f'<li><a href="chapter-{ch:02d}/">제{ch}장 「{title}」</a>{suffix}</li>')
    lines += ['</ol>', '', '</div>', '']
    (book_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")


def build_book(
    key: str,
    manifest: dict,
    convs: dict[str, Conversation],
    recon_dir: Path,
    output_root: Path,
) -> dict:
    info = BOOKS[key]
    book_dir = output_root / info["slug"]
    if book_dir.exists():
        shutil.rmtree(book_dir)
    book_dir.mkdir(parents=True)
    stats: dict[int, dict] = {}

    for ch, title in info["titles"].items():
        blocks: list[str] = []
        if key == "truth" and (ch in (2, 3) or ch >= 16):
            source = recon_dir / f"chapter-{ch}.md"
            if not source.exists():
                raise RuntimeError(f"missing reconstructed chapter: {source}")
            blocks = [source.read_text(encoding="utf-8").strip()]
        else:
            ids = list(manifest[key].get(str(ch), []))
            if key == "truth" and ch == 3:
                # Repair an early manifest typo in a deterministic way.
                ids = ["6a702be1-1ca8-83ee-b0cd-cdc8580d98f9"]
            if not ids:
                raise RuntimeError(f"manifest has no ids: {key} chapter {ch}")
            missing = [cid for cid in ids if cid not in convs]
            if missing:
                raise RuntimeError(f"missing archive conversations for {key} chapter {ch}: {missing}")
            selected = [convs[cid] for cid in ids]
            selected.sort(key=lambda c: date_key(c.date))
            for conv in selected:
                ans = extract_gpt_blocks(conv.text)
                if not ans:
                    raise RuntimeError(f"no GPT answer blocks in {conv.cid} ({conv.title})")
                blocks.extend(ans)
        stats[ch] = write_chapter(book_dir, info["short"], ch, title, blocks)

    write_book_index(book_dir, info, stats)
    return {
        "book": key,
        "slug": info["slug"],
        "chapters": len(stats),
        "pages": sum(v["parts"] for v in stats.values()),
        "max_part_chars": max(v["max_chars"] for v in stats.values()),
        "chapter_stats": stats,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conversations", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--reconstructed", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    convs = index_conversations(args.conversations)
    args.output.mkdir(parents=True, exist_ok=True)

    results = []
    for key in ("truth", "modern"):
        results.append(build_book(key, manifest, convs, args.reconstructed, args.output))

    report = {
        "conversation_archive_count": len(convs),
        "target_chars": TARGET_CHARS,
        "hard_chars": HARD_CHARS,
        "results": results,
    }
    (args.output / "build-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
