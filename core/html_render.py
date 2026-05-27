"""Markdown → HTML renderers per studio.

Two families:
- `generic`: markdown → HTML with emoji-friendly Korean typography (blog,
  press release).
- channel-shaped: parse `### N장` blocks and render fixed-aspect cards.
  Each card has `.studio-card[data-card-index]` so the PNG renderer
  (core/png_render.py, Playwright) can capture them individually at
  exact pixel dimensions.
"""
from __future__ import annotations

import html as _html
import json
import re
from typing import Callable

import markdown as _md

from core import card_templates

# ─────────────────── shared HTML shell ───────────────────

_BASE_CSS = """
:root {
  --fg: #111827;
  --muted: #6b7280;
  --accent: #2563eb;
  --accent-soft: #dbeafe;
  --bg: #ffffff;
  --bg-soft: #f9fafb;
  --code-bg: #f3f4f6;
  --border: #e5e7eb;
}
* { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Apple SD Gothic Neo",
               "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: var(--fg); background: var(--bg);
  max-width: 860px; margin: 0 auto; padding: 56px 28px 80px;
  line-height: 1.75; font-size: 17px; word-break: keep-all;
}
.title-block { margin-bottom: 48px; }
.title-block h1 { font-size: 2.2rem; margin: 0 0 8px; letter-spacing: -0.02em; line-height: 1.25; }
.title-block .meta { color: var(--muted); font-size: 0.9rem; margin: 0; }
.title-block .stripe {
  display: inline-block; width: 64px; height: 6px; border-radius: 3px;
  background: linear-gradient(90deg, #2563eb, #7c3aed); margin-bottom: 16px;
}
h1 { font-size: 1.9rem; line-height: 1.3; }
h2 {
  font-size: 1.5rem; margin-top: 2.4em; margin-bottom: 0.6em; line-height: 1.35;
  padding-left: 14px; border-left: 5px solid var(--accent); letter-spacing: -0.01em;
}
h3 { font-size: 1.18rem; margin-top: 2em; margin-bottom: 0.4em; color: #1f2937; font-weight: 700; }
h4 { font-size: 1rem; color: var(--muted); margin-top: 1.6em; }
p, li { font-size: 1.02rem; }
p { margin: 0.6em 0 1.1em; }
ul, ol { padding-left: 1.4em; margin: 0.6em 0 1.2em; }
li { margin-bottom: 0.35em; }
hr { border: none; border-top: 1px dashed var(--border); margin: 2.6em 0; }
strong { color: #0f172a; }
blockquote {
  border-left: 4px solid var(--accent-soft); background: var(--bg-soft);
  padding: 14px 20px; border-radius: 0 8px 8px 0; color: #1f2937; margin: 1.2em 0;
}
code { background: var(--code-bg); padding: 2px 6px; border-radius: 4px; font-size: 0.92em; color: #be185d; }
pre code { display: block; padding: 14px; overflow-x: auto; color: var(--fg); }
table {
  border-collapse: collapse; width: 100%; margin: 1.4em 0;
  font-size: 0.96rem; border-radius: 8px; overflow: hidden;
}
th, td { border: 1px solid var(--border); padding: 10px 14px; text-align: left; }
th { background: var(--bg-soft); font-weight: 700; }
tr:nth-child(even) td { background: #fafafa; }
.hashtag-line { color: var(--accent); font-weight: 600; word-break: break-all; margin: 1.4em 0; }
@media print { body { padding: 24px; max-width: none; } }
"""


def _shell(title: str, body_html: str, extra_css: str = "") -> str:
    return (
        '<!doctype html>\n'
        '<html lang="ko"><head>\n'
        '<meta charset="utf-8">\n'
        f'<title>{_html.escape(title)}</title>\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<style>{_BASE_CSS}\n{extra_css}</style>\n'
        '</head><body>\n'
        f'{body_html}\n'
        '</body></html>\n'
    )


# ─────────────────── hashtag pre-processor ───────────────────

_RX_LEADING_HASH_LINE = re.compile(r"(?m)^(#[^\n]*)$")


def _protect_hashtag_lines(md_text: str) -> str:
    """Convert hashtag-only lines into a styled paragraph so markdown.markdown
    doesn't interpret them as an H1/H2/H3 heading.

    A line is considered a hashtag line (vs. a real heading) if:
    - It contains 2+ `#` tokens, OR
    - It starts with `#` followed immediately by a word char (no space), OR
    - It starts with `#` followed by a unicode variation selector (e.g. `#️⃣`)
      and contains another `#` later.
    """
    def _sub(m):
        line = m.group(1).strip()
        # Real heading: `# Title` or `## Title` — single `#` group followed by space then content
        real_heading = re.match(r"^#{1,6}\s+\S", line) and line.count("#") <= 6 and " #" not in line
        if real_heading:
            return m.group(0)
        # Hashtag line indicators
        if line.count("#") >= 2:
            esc = _html.escape(line)
            return f'<p class="hashtag-line">{esc}</p>'
        if re.match(r"^#[\w가-힣]+\s*$", line):  # single bare hashtag on its own line
            esc = _html.escape(line)
            return f'<p class="hashtag-line">{esc}</p>'
        return m.group(0)
    return _RX_LEADING_HASH_LINE.sub(_sub, md_text)


# ─────────────────── generic blog/press renderer ───────────────────

def generic(md_text: str, *, title: str, **_) -> str:
    md_text = _protect_hashtag_lines(md_text)
    body = _md.markdown(
        md_text,
        extensions=["extra", "tables", "sane_lists", "nl2br"],
        output_format="html5",
    )
    header = (
        '<div class="title-block">\n'
        '  <div class="stripe"></div>\n'
        f'  <h1>{_html.escape(title)}</h1>\n'
        '  <p class="meta">Subtitle Marketing Studio</p>\n'
        '</div>\n'
    )
    return _shell(title, header + body)


# ─────────────────── card parsing ───────────────────

_RX_SLIDE_HEADER = re.compile(r"^###\s+(\d+장)([^\n]*)$", re.MULTILINE)
_RX_BOLD = re.compile(r"\*\*([^*\n]+)\*\*")
_RX_ITALIC = re.compile(r"(?:^|[^*])\*([^*\n]+)\*(?!\*)")


def _parse_cards(md_text: str) -> list[dict]:
    """Pull each `### N장 …` block. Returns list of {idx, role, main, sub, body, hashtags, cta}."""
    headers = list(_RX_SLIDE_HEADER.finditer(md_text))
    if not headers:
        return []
    out = []
    for i, m in enumerate(headers):
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(md_text)
        next_h2 = md_text.find("\n## ", start)
        if next_h2 != -1 and next_h2 < end:
            end = next_h2
        block = md_text[start:end]
        bolds = _RX_BOLD.findall(block)
        italic_m = _RX_ITALIC.search(block)
        idx_label = m.group(1)
        role = m.group(2).strip().lstrip("—–-").strip()
        main = bolds[0].strip() if bolds else (block.strip().splitlines()[0] if block.strip() else "")
        sub = italic_m.group(1).strip() if italic_m else ""

        # Find labeled bold sections inside the card (caption, hashtags, CTA)
        body = _grab_labeled(block, ["캡션 본문", "본문"])
        hashtags = _grab_labeled(block, ["해시태그"])
        cta = _grab_labeled(block, ["CTA"])
        out.append({
            "idx": idx_label, "role": role,
            "main": main, "sub": sub,
            "body": body, "hashtags": hashtags, "cta": cta,
        })
    return out


def _grab_labeled(block: str, labels: list[str]) -> str:
    """Extract the value after `**<label>**` (any of) until newline or next bold."""
    for lbl in labels:
        m = re.search(rf"\*\*{re.escape(lbl)}\*\*\s*[:：]?\s*(.+?)(?:\n\s*\*\*|\n\n|\Z)", block, re.DOTALL)
        if m:
            return m.group(1).strip()
    return ""


def _extract_section(md_text: str, header: str) -> str:
    pat = re.compile(rf"^##\s+{re.escape(header)}[^\n]*\n(.*?)(?=\n##\s|\Z)", re.DOTALL | re.MULTILINE)
    m = pat.search(md_text)
    return m.group(1).strip() if m else ""


# ─────────────────── card CSS (shared base + variants) ───────────────────

_CARD_BASE_CSS = """
body {
  background: #e5e7eb; max-width: none; margin: 0; padding: 32px 16px;
  font-family: -apple-system, "Pretendard", "Apple SD Gothic Neo", "Segoe UI", sans-serif;
  line-height: 1.4;
}
.studio-title { text-align: center; font-size: 24px; color: #111827; margin: 0 0 8px; }
.print-note {
  max-width: 1080px; margin: 8px auto 32px;
  padding: 12px 18px; background: #fff; border-radius: 12px;
  font-size: 13px; color: #6b7280; text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.cards { display: flex; flex-direction: column; gap: 40px; align-items: center; }
.studio-card {
  position: relative; overflow: hidden;
  display: flex; flex-direction: column;
  word-break: keep-all; color: #111827;
  box-shadow: 0 24px 60px rgba(0,0,0,0.18);
  border-radius: 24px;
}
.studio-card::before {
  content: ""; position: absolute; inset: 0;
  background-image:
    radial-gradient(circle at 88% 12%, rgba(255,255,255,0.26) 0%, transparent 38%),
    radial-gradient(circle at 12% 88%, rgba(0,0,0,0.08) 0%, transparent 42%);
  pointer-events: none;
}
.studio-card .top {
  display: flex; justify-content: space-between; align-items: center;
  position: relative; z-index: 2;
}
.studio-card .badge {
  width: 96px; height: 96px; border-radius: 50%;
  background: rgba(255,255,255,0.22); backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center;
  font-size: 40px; font-weight: 900; letter-spacing: -0.04em;
  border: 2px solid rgba(255,255,255,0.4);
}
.studio-card .slide-meta {
  font-size: 18px; opacity: 0.6; letter-spacing: 0.14em; font-weight: 800; text-transform: uppercase;
}
.studio-card .body { flex: 1; display: flex; flex-direction: column; justify-content: center; position: relative; z-index: 2; }
.studio-card .main { font-weight: 900; letter-spacing: -0.02em; line-height: 1.18; margin: 0 0 28px; }
.studio-card .sub  { font-weight: 500; line-height: 1.5; opacity: 0.85; }
.studio-card .footer {
  display: flex; justify-content: space-between; align-items: flex-end;
  position: relative; z-index: 2;
  margin-top: auto; padding-top: 28px;
  border-top: 2px solid currentColor;
}
.studio-card .brand     { font-weight: 800; letter-spacing: 0.04em; }
.studio-card .size-tag  { opacity: 0.7; letter-spacing: 0.06em; }
.cta-pill {
  display: inline-block; padding: 14px 28px; background: #fff; color: #111827;
  border-radius: 999px; font-weight: 900; margin-top: 20px;
}
.caption-inside { background: rgba(255,255,255,0.12); border-radius: 14px; padding: 16px 18px; margin-top: 16px; }
.hashtags-inside { color: #93c5fd; font-weight: 700; margin-top: 12px; word-break: break-all; }
.dark-on-light .hashtags-inside { color: #1d4ed8; }

/* Size variants */
.studio-card.size-1080-1350 { width: 1080px; height: 1350px; padding: 96px 88px 80px; }
.studio-card.size-1080-1350 .main { font-size: 84px; }
.studio-card.size-1080-1350 .sub  { font-size: 34px; }
.studio-card.size-1080-1350 .brand { font-size: 24px; }
.studio-card.size-1080-1350 .size-tag { font-size: 20px; }

.studio-card.size-800-800 { width: 800px; height: 800px; padding: 70px 64px 56px; }
.studio-card.size-800-800 .main { font-size: 56px; }
.studio-card.size-800-800 .sub  { font-size: 26px; }
.studio-card.size-800-800 .brand { font-size: 20px; }
.studio-card.size-800-800 .size-tag { font-size: 16px; }
.studio-card.size-800-800 .badge { width: 72px; height: 72px; font-size: 30px; }

/* Channel themes */
.theme-threads .studio-card { background: linear-gradient(155deg, #0f172a 0%, #1e293b 50%, #475569 100%); color: #fff; }
.theme-threads .studio-card.cta-card { background: linear-gradient(155deg, #064e3b 0%, #047857 50%, #10b981 100%); }
.theme-threads-insight .studio-card { background: linear-gradient(155deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%); color: #fff; }
.theme-threads-insight .studio-card.cover-card { background: linear-gradient(155deg, #0f172a 0%, #1e1b4b 50%, #4c1d95 100%); }
.theme-threads-insight .studio-card.cta-card { background: linear-gradient(155deg, #064e3b 0%, #047857 50%, #10b981 100%); }

.theme-instagram-info .studio-card { background: linear-gradient(155deg, #fef3c7 0%, #fde68a 50%, #fbbf24 100%); }
.theme-instagram-info .studio-card.cover-card { background: linear-gradient(155deg, #1e1b4b 0%, #312e81 50%, #6d28d9 100%); color: #fff; }
.theme-instagram-info .studio-card.cta-card { background: linear-gradient(155deg, #064e3b 0%, #047857 50%, #10b981 100%); color: #fff; }

.theme-instagram-story .studio-card { background: linear-gradient(155deg, #fef2f2 0%, #fed7aa 40%, #fdba74 100%); }
.theme-instagram-story .studio-card.cover-card { background: linear-gradient(155deg, #292524 0%, #44403c 50%, #78716c 100%); color: #fff; }
.theme-instagram-story .studio-card.cta-card { background: linear-gradient(155deg, #1c1917 0%, #44403c 50%, #a8a29e 100%); color: #fff; }
.theme-instagram-story .studio-card.c2 { background: linear-gradient(155deg, #fef3c7 0%, #fde68a 100%); }
.theme-instagram-story .studio-card.c3 { background: linear-gradient(155deg, #ddd6fe 0%, #c4b5fd 100%); }
.theme-instagram-story .studio-card.c4 { background: linear-gradient(155deg, #fce7f3 0%, #fbcfe8 100%); }
.theme-instagram-story .studio-card.c5 { background: linear-gradient(155deg, #d1fae5 0%, #a7f3d0 100%); }

.theme-kakao .studio-card { background: linear-gradient(155deg, #fef9c3 0%, #fde047 50%, #facc15 100%); }
.theme-kakao .studio-card.cover-card { background: linear-gradient(155deg, #422006 0%, #78350f 50%, #ca8a04 100%); color: #fff; }
.theme-kakao .studio-card.cta-card { background: linear-gradient(155deg, #fef9c3 0%, #fde047 50%, #f59e0b 100%); }

.caption-block {
  max-width: 1080px; margin: 48px auto 0;
  background: #fff; padding: 36px 40px; border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.06);
}
.caption-block h2 { margin: 0 0 14px; font-size: 1.4rem; padding-left: 12px; border-left: 4px solid #2563eb; }
.caption-block .hashtag-line { color: #2563eb; font-weight: 600; word-break: break-all; }

@media print {
  @page { size: 1080px 1350px; margin: 0; }
  body { background: #fff; padding: 0; }
  .print-note, .studio-title { display: none; }
  .studio-card { page-break-after: always; box-shadow: none; border-radius: 0; }
  .caption-block { page-break-before: always; box-shadow: none; }
}
"""


# ─────────────────── card renderer ───────────────────

_EMOJIS_BY_CHANNEL = {
    "threads_quick": ["💬", "🎯", "🔁"],
    "threads_insight": ["📊", "🔍", "💡", "📈", "✨"],
    "instagram_info": ["✨", "📌", "📊", "📍", "🎯"],
    "instagram_story": ["🌅", "📮", "🎞", "📷", "💌", "🌙", "✨"],
    "kakao_cards": ["💬", "📨", "🔔"],
}


def _card_html(
    card: dict, i: int, n: int, *,
    size_class: str, emoji: str, brand: str, size_tag: str,
) -> str:
    """Render one card. First card is .cover-card, last is .cta-card."""
    if i == 0:
        klass = "cover-card"
    elif i == n - 1:
        klass = "cta-card"
    else:
        klass = f"c{i + 1}"

    body_html = ""
    if card.get("body"):
        body_html += f'<div class="caption-inside">{_html.escape(card["body"])}</div>'
    if card.get("hashtags"):
        body_html += f'<div class="hashtags-inside">{_html.escape(card["hashtags"])}</div>'
    if card.get("cta") and i == n - 1:
        body_html += f'<div class="cta-pill">{_html.escape(card["cta"])}</div>'
    elif i == n - 1 and not card.get("cta"):
        body_html += '<div class="cta-pill">저장하기 ↗</div>'

    role = card.get("role") or ""
    return (
        f'<div class="studio-card {size_class} {klass}" data-card-index="{i + 1}">'
        f'  <div class="top">'
        f'    <div class="badge">{emoji}</div>'
        f'    <div class="slide-meta">{_html.escape(card["idx"])} · {_html.escape(role)[:18]}</div>'
        f'  </div>'
        f'  <div class="body">'
        f'    <div class="main">{_html.escape(card["main"])}</div>'
        f'    {f"<div class=\"sub\">{_html.escape(card['sub'])}</div>" if card['sub'] else ""}'
        f'    {body_html}'
        f'  </div>'
        f'  <div class="footer">'
        f'    <div class="brand">{_html.escape(brand or "Subtitle Marketing Studio")}</div>'
        f'    <div class="size-tag">{size_tag}</div>'
        f'  </div>'
        f'</div>'
    )


def _render_cards(
    md_text: str, *, title: str, brand: str,
    channel_key: str, size_class: str, theme_class: str, size_tag: str,
    extra_sections: list[tuple[str, str]] | None = None,
) -> str:
    """Common card renderer. extra_sections = [(md_header, display_title)]."""
    cards = _parse_cards(md_text)
    if not cards:
        return generic(md_text, title=title)
    emojis = _EMOJIS_BY_CHANNEL.get(channel_key, ["✨"] * len(cards))
    n = len(cards)
    cards_html = "\n".join(
        _card_html(c, i, n, size_class=size_class,
                   emoji=emojis[i] if i < len(emojis) else emojis[-1],
                   brand=brand, size_tag=size_tag)
        for i, c in enumerate(cards)
    )

    body = (
        f'<div class="{theme_class}">'
        f'<div class="studio-title">{_html.escape(title)}</div>'
        f'<div class="print-note">📐 {size_tag} · 카드 {n}장 · 브라우저에서 보거나 PNG로 추출(상단 🖼 버튼)</div>'
        f'<div class="cards">{cards_html}</div>'
        f'</div>'
    )

    for md_header, disp in (extra_sections or []):
        section_md = _extract_section(md_text, md_header)
        if section_md:
            section_md = _protect_hashtag_lines(section_md)
            section_html = _md.markdown(section_md, extensions=["extra", "nl2br"])
            body += f'<div class="caption-block"><h2>{_html.escape(disp)}</h2>{section_html}</div>'

    return _shell(title, body, extra_css=_CARD_BASE_CSS)


def _render_json_cards(channel_key: str, md_text: str, *, title: str, brand: str) -> str:
    """LLM returns JSON for card studios. Parse and render via Jinja2 template."""
    try:
        data = card_templates.parse_card_json(md_text)
    except (json.JSONDecodeError, ValueError) as e:
        # If the LLM ignored the JSON contract, fall back to generic rendering
        return generic(
            f"### ⚠️ JSON 파싱 실패\n\n`{type(e).__name__}: {e}`\n\n원본 출력 아래 (재실행 권장):\n\n---\n\n{md_text}",
            title=title,
        )
    return card_templates.render_cards(channel_key, data, title=title, brand=brand)


def cards_threads_quick(md_text: str, *, title: str, brand: str = "", **_) -> str:
    return _render_json_cards("cards_threads_quick", md_text, title=title, brand=brand)


def cards_threads_insight(md_text: str, *, title: str, brand: str = "", **_) -> str:
    return _render_json_cards("cards_threads_insight", md_text, title=title, brand=brand)


def cards_instagram_info(md_text: str, *, title: str, brand: str = "", **_) -> str:
    return _render_json_cards("cards_instagram_info", md_text, title=title, brand=brand)


def cards_instagram_story(md_text: str, *, title: str, brand: str = "", **_) -> str:
    return _render_json_cards("cards_instagram_story", md_text, title=title, brand=brand)


def cards_kakao(md_text: str, *, title: str, brand: str = "", **_) -> str:
    return _render_json_cards("cards_kakao", md_text, title=title, brand=brand)


# ─────────────────── dispatch ───────────────────

RENDERERS: dict[str, Callable[..., str]] = {
    "generic": generic,
    "cards_threads_quick": cards_threads_quick,
    "cards_threads_insight": cards_threads_insight,
    "cards_instagram_info": cards_instagram_info,
    "cards_instagram_story": cards_instagram_story,
    "cards_kakao": cards_kakao,
}


def render(renderer_key: str, md_text: str, *, title: str, brand: str = "") -> str:
    fn = RENDERERS.get(renderer_key, generic)
    try:
        return fn(md_text, title=title, brand=brand)
    except Exception:
        return generic(md_text, title=title)
