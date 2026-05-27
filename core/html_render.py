"""Markdown → HTML renderers per studio.

Two strategies:
- `generic`: visually-rich rendering of any studio's markdown — Pretendard,
  emoji-aware H2 accents, callout boxes, color stripes. Default.
- channel-shaped templates (e.g. `instagram_cards`): parse known structure
  from the markdown and inject into a fixed-aspect-ratio card template.
  Designed so a future Playwright screenshot step can capture cards at
  exact pixel dimensions.
"""
from __future__ import annotations

import html as _html
import re
from typing import Callable

import markdown as _md

# ─────────────────── shared CSS ───────────────────

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
  color: var(--fg);
  background: var(--bg);
  max-width: 860px;
  margin: 0 auto;
  padding: 56px 28px 80px;
  line-height: 1.75;
  font-size: 17px;
  word-break: keep-all;
}
.title-block { margin-bottom: 48px; }
.title-block h1 {
  font-size: 2.2rem; margin: 0 0 8px;
  letter-spacing: -0.02em; line-height: 1.25;
}
.title-block .meta { color: var(--muted); font-size: 0.9rem; margin: 0; }
.title-block .stripe {
  display: inline-block; width: 64px; height: 6px; border-radius: 3px;
  background: linear-gradient(90deg, #2563eb, #7c3aed); margin-bottom: 16px;
}
h1 { font-size: 1.9rem; line-height: 1.3; }
h2 {
  font-size: 1.5rem; margin-top: 2.4em; margin-bottom: 0.6em; line-height: 1.35;
  padding-left: 14px; border-left: 5px solid var(--accent);
  letter-spacing: -0.01em;
}
h3 {
  font-size: 1.18rem; margin-top: 2em; margin-bottom: 0.4em;
  color: #1f2937; font-weight: 700;
}
h4 { font-size: 1rem; color: var(--muted); margin-top: 1.6em; }
p, li { font-size: 1.02rem; }
p { margin: 0.6em 0 1.1em; }
ul, ol { padding-left: 1.4em; margin: 0.6em 0 1.2em; }
li { margin-bottom: 0.35em; }
hr { border: none; border-top: 1px dashed var(--border); margin: 2.6em 0; }
strong { color: #0f172a; }
blockquote {
  border-left: 4px solid var(--accent-soft);
  background: var(--bg-soft);
  padding: 14px 20px; border-radius: 0 8px 8px 0;
  color: #1f2937;
  margin: 1.2em 0;
}
code {
  background: var(--code-bg); padding: 2px 6px; border-radius: 4px;
  font-size: 0.92em; color: #be185d;
}
pre code { display: block; padding: 14px; overflow-x: auto; color: var(--fg); }
table {
  border-collapse: collapse; width: 100%; margin: 1.4em 0;
  font-size: 0.96rem; border-radius: 8px; overflow: hidden;
}
th, td { border: 1px solid var(--border); padding: 10px 14px; text-align: left; }
th { background: var(--bg-soft); font-weight: 700; }
tr:nth-child(even) td { background: #fafafa; }
a { color: var(--accent); text-decoration: none; border-bottom: 1px solid var(--accent-soft); }
a:hover { border-bottom-color: var(--accent); }
img { max-width: 100%; height: auto; border-radius: 8px; }
.callout {
  background: linear-gradient(135deg, #eff6ff, #f5f3ff);
  border: 1px solid #ddd6fe;
  border-radius: 12px;
  padding: 18px 22px; margin: 1.4em 0;
}
@media print {
  body { padding: 24px; max-width: none; }
}
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


# ─────────────────── generic markdown → HTML ───────────────────

def generic(md_text: str, *, title: str, **_) -> str:
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


# ─────────────────── Instagram cards (1080×1350) ───────────────────

_CARD_CSS = """
body {
  background: #e5e7eb; max-width: none; margin: 0; padding: 40px 24px; font-size: 14px;
  font-family: -apple-system, "Pretendard", "Apple SD Gothic Neo", "Segoe UI", sans-serif;
  line-height: 1.4;
}
h1 { text-align: center; font-size: 28px; color: #111827; margin: 0 0 8px; }
.print-note {
  max-width: 1080px; margin: 8px auto 32px;
  padding: 14px 20px; background: #fff; border-radius: 12px;
  font-size: 13px; color: #6b7280; text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.cards { display: flex; flex-direction: column; gap: 48px; align-items: center; }

.insta-card {
  width: 1080px; height: 1350px;
  position: relative; overflow: hidden;
  border-radius: 24px;
  box-shadow: 0 24px 60px rgba(0,0,0,0.18);
  display: flex; flex-direction: column;
  padding: 110px 96px 96px;
  word-break: keep-all;
  color: #111827;
  background: linear-gradient(155deg, #fef3c7 0%, #fde68a 50%, #fbbf24 100%);
}
/* Per-slide gradient themes */
.insta-card.c1 { background: linear-gradient(155deg, #1e1b4b 0%, #312e81 45%, #6d28d9 100%); color: #fff; }
.insta-card.c2 { background: linear-gradient(155deg, #fef3c7 0%, #fde68a 55%, #fbbf24 100%); }
.insta-card.c3 { background: linear-gradient(155deg, #fce7f3 0%, #fbcfe8 50%, #f472b6 100%); }
.insta-card.c4 { background: linear-gradient(155deg, #d1fae5 0%, #a7f3d0 50%, #34d399 100%); }
.insta-card.c5 { background: linear-gradient(155deg, #0f172a 0%, #134e4a 50%, #059669 100%); color: #fff; }

.insta-card::before {
  content: ""; position: absolute; inset: 0;
  background-image:
    radial-gradient(circle at 88% 12%, rgba(255,255,255,0.28) 0%, transparent 38%),
    radial-gradient(circle at 12% 88%, rgba(0,0,0,0.10) 0%, transparent 42%);
  pointer-events: none;
}
.insta-card::after {
  content: ""; position: absolute;
  right: -120px; bottom: -120px;
  width: 380px; height: 380px; border-radius: 50%;
  background: rgba(255,255,255,0.12);
  pointer-events: none;
}

.insta-card .top {
  display: flex; justify-content: space-between; align-items: center;
  position: relative; z-index: 2;
}
.insta-card .badge {
  width: 104px; height: 104px; border-radius: 50%;
  background: rgba(255,255,255,0.22); backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center;
  font-size: 44px; font-weight: 900; letter-spacing: -0.04em;
  border: 2px solid rgba(255,255,255,0.4);
}
.insta-card.c2 .badge, .insta-card.c3 .badge, .insta-card.c4 .badge {
  background: rgba(17,24,39,0.10); border-color: rgba(17,24,39,0.22); color: #111827;
}
.insta-card .slide-meta {
  font-size: 22px; opacity: 0.65; letter-spacing: 0.18em; font-weight: 800;
  text-transform: uppercase;
}
.insta-card .accent-line {
  width: 140px; height: 10px; background: currentColor; opacity: 0.85; border-radius: 5px;
  margin-top: 56px; position: relative; z-index: 2;
}
.insta-card .body {
  flex: 1; display: flex; flex-direction: column; justify-content: center;
  position: relative; z-index: 2; padding: 16px 0;
}
.insta-card .main {
  font-size: 96px; line-height: 1.16; font-weight: 900; letter-spacing: -0.02em;
  margin: 0 0 36px;
}
.insta-card.c1 .main { font-size: 108px; }
.insta-card.c5 .main { font-size: 88px; }
.insta-card .sub {
  font-size: 40px; line-height: 1.55; font-weight: 500; opacity: 0.85;
}
.insta-card .footer {
  display: flex; justify-content: space-between; align-items: flex-end;
  position: relative; z-index: 2;
  margin-top: auto; padding-top: 36px;
  border-top: 2px solid currentColor;
}
.insta-card .footer-left { font-size: 26px; font-weight: 800; letter-spacing: 0.05em; }
.insta-card .footer-right { font-size: 22px; opacity: 0.7; letter-spacing: 0.08em; }
.insta-card .cta-pill {
  display: inline-block; padding: 18px 36px; background: #fff; color: #111827;
  border-radius: 999px; font-size: 30px; font-weight: 900;
  margin-top: 24px;
}

.caption-block {
  max-width: 1080px; margin: 56px auto 0;
  background: #fff; padding: 40px 48px; border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.06);
}
.caption-block h2 { margin: 0 0 16px; font-size: 1.5rem; padding-left: 12px; border-left: 4px solid #2563eb; }
.hashtags { color: #2563eb; word-break: break-all; font-weight: 600; }

@media print {
  @page { size: 1080px 1350px; margin: 0; }
  body { background: #fff; padding: 0; }
  .print-note, h1 { display: none; }
  .insta-card { page-break-after: always; box-shadow: none; border-radius: 0; }
  .caption-block { page-break-before: always; box-shadow: none; }
}
"""

_RX_SLIDE_HEADER = re.compile(r"^###\s+(\d+장)[^\n]*$", re.MULTILINE)

_SLIDE_EMOJIS = ["✨", "📮", "📻", "📺", "🚀"]
_DEFAULT_EMOJI = "🎯"


def _parse_insta_slides(md_text: str) -> list[dict]:
    """Pull each `### N장 — …` block. Returns list of {idx, header, main, sub}."""
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
        header_label = m.group(0).lstrip("# ").strip()
        main_m = re.search(r"\*\*([^*\n]+)\*\*", block)
        sub_m = re.search(r"(?:^|[^*])\*([^*\n]+)\*(?!\*)", block)
        main_text = main_m.group(1).strip() if main_m else (block.strip().splitlines()[0] if block.strip() else "")
        sub_text = sub_m.group(1).strip() if sub_m else ""
        out.append({
            "idx": m.group(1),  # "1장"
            "header": header_label,
            "main": main_text,
            "sub": sub_text,
        })
    return out


def _extract_section(md_text: str, header: str) -> str:
    pat = re.compile(rf"^##\s+{re.escape(header)}[^\n]*\n(.*?)(?=\n##\s|\Z)", re.DOTALL | re.MULTILINE)
    m = pat.search(md_text)
    return m.group(1).strip() if m else ""


def instagram_cards(md_text: str, *, title: str, brand: str = "", **_) -> str:
    slides = _parse_insta_slides(md_text)
    if not slides:
        return generic(md_text, title=title)

    n = len(slides)
    cards_html_parts = []
    for i, s in enumerate(slides):
        slide_class = f"c{min(i + 1, 5)}"
        emoji = _SLIDE_EMOJIS[i] if i < len(_SLIDE_EMOJIS) else _DEFAULT_EMOJI
        role = "표지" if i == 0 else ("CTA" if i == n - 1 else f"본문 {i}")
        is_cta = (i == n - 1)
        cta_html = '<div class="cta-pill">저장하기 ↗</div>' if is_cta else ""
        cards_html_parts.append(
            f'<div class="insta-card {slide_class}">'
            f'  <div class="top">'
            f'    <div class="badge">{emoji}</div>'
            f'    <div class="slide-meta">{_html.escape(s["idx"])} · {role}</div>'
            f'  </div>'
            f'  <div class="accent-line"></div>'
            f'  <div class="body">'
            f'    <div class="main">{_html.escape(s["main"])}</div>'
            f'    <div class="sub">{_html.escape(s["sub"])}</div>'
            f'    {cta_html}'
            f'  </div>'
            f'  <div class="footer">'
            f'    <div class="footer-left">{_html.escape(brand or "Subtitle Marketing Studio")}</div>'
            f'    <div class="footer-right">1080 × 1350 · 4:5</div>'
            f'  </div>'
            f'</div>'
        )
    cards_html = "\n".join(cards_html_parts)

    caption_md = _extract_section(md_text, "인스타 캡션")
    design_md = _extract_section(md_text, "디자인 메모")
    caption_html = _md.markdown(caption_md, extensions=["extra", "nl2br"]) if caption_md else ""
    design_html = _md.markdown(design_md, extensions=["extra", "nl2br"]) if design_md else ""

    if caption_html:
        caption_html = re.sub(
            r"(#[\w가-힣]+)",
            r'<span class="hashtags">\1</span>',
            caption_html,
        )

    body = (
        f'<h1>{_html.escape(title)}</h1>\n'
        '<p class="print-note">📐 인스타그램 캐러셀 5장 · 각 1080 × 1350 px [4:5] · '
        '브라우저에서 Ctrl+P → "대상: PDF로 저장" → 한 장당 한 페이지로 추출 가능</p>\n'
        f'<div class="cards">{cards_html}</div>\n'
    )
    if caption_html:
        body += (
            '<div class="caption-block">\n'
            '<h2>💬 인스타 캡션</h2>\n'
            f'{caption_html}\n'
            '</div>\n'
        )
    if design_html:
        body += (
            '<div class="caption-block">\n'
            '<h2>🎨 디자인 메모</h2>\n'
            f'{design_html}\n'
            '</div>\n'
        )
    return _shell(title, body, extra_css=_CARD_CSS)


# ─────────────────── dispatch ───────────────────

RENDERERS: dict[str, Callable[..., str]] = {
    "generic": generic,
    "instagram_cards": instagram_cards,
}


def render(renderer_key: str, md_text: str, *, title: str, brand: str = "") -> str:
    fn = RENDERERS.get(renderer_key, generic)
    try:
        return fn(md_text, title=title, brand=brand)
    except Exception:
        return generic(md_text, title=title)
