"""Markdown → HTML renderers per studio.

Two strategies:
- `generic`: clean readable rendering of the studio's markdown (default for
  most studios). Markdown → HTML via the `markdown` lib + readable CSS.
- channel-shaped templates (e.g. `instagram_cards`): parse known structure
  from the markdown and inject into a fixed-aspect-ratio card template.
  Designed so a future Playwright screenshot step can capture the cards
  at exact pixel dimensions.
"""
from __future__ import annotations

import html as _html
import re
from typing import Callable

import markdown as _md

_BASE_CSS = """
:root {
  --fg: #1f2937;
  --muted: #6b7280;
  --accent: #2563eb;
  --bg: #ffffff;
  --code-bg: #f3f4f6;
}
* { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Apple SD Gothic Neo",
               "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: var(--fg);
  background: var(--bg);
  max-width: 820px;
  margin: 40px auto;
  padding: 0 24px;
  line-height: 1.65;
  font-size: 16px;
  word-break: keep-all;
}
h1 { font-size: 1.9rem; margin-top: 0; line-height: 1.3; }
h2 { font-size: 1.45rem; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; margin-top: 2em; }
h3 { font-size: 1.15rem; margin-top: 1.8em; color: #111827; }
h4 { font-size: 1rem; color: var(--muted); margin-top: 1.4em; }
p, li { font-size: 1rem; }
ul, ol { padding-left: 1.4em; }
hr { border: none; border-top: 1px dashed #d1d5db; margin: 2em 0; }
blockquote { border-left: 4px solid #e5e7eb; padding-left: 1em; color: var(--muted); }
code { background: var(--code-bg); padding: 2px 5px; border-radius: 4px; font-size: 0.9em; }
pre code { display: block; padding: 12px; overflow-x: auto; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid #e5e7eb; padding: 8px 12px; text-align: left; }
th { background: #f9fafb; }
.meta { color: var(--muted); font-size: 0.85rem; margin-bottom: 2em; }
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


def generic(md_text: str, *, title: str, **_) -> str:
    body = _md.markdown(
        md_text,
        extensions=["extra", "tables", "sane_lists", "nl2br"],
        output_format="html5",
    )
    header = f'<h1>{_html.escape(title)}</h1>\n<p class="meta">Subtitle Marketing Studio</p>\n'
    return _shell(title, header + body)


# ─────────────────── Instagram cards (1080×1350) ───────────────────

_CARD_CSS = """
body { background: #f3f4f6; max-width: none; margin: 0; padding: 32px; font-size: 14px; }
h1 { text-align: center; }
.print-note {
  max-width: 1080px; margin: 0 auto 24px;
  padding: 12px 16px; background: #fff; border-radius: 8px;
  font-size: 13px; color: var(--muted);
}
.cards { display: flex; flex-direction: column; gap: 32px; align-items: center; }
.insta-card {
  width: 1080px; height: 1350px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 50%, #fcd34d 100%);
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 96px 80px;
  font-family: -apple-system, "Pretendard", "Apple SD Gothic Neo", sans-serif;
  word-break: keep-all;
}
.insta-card.cover { background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 50%, #6b21a8 100%); color: #fff; }
.insta-card.cta   { background: linear-gradient(135deg, #064e3b 0%, #047857 50%, #10b981 100%); color: #fff; }
.insta-card .slide-tag {
  font-size: 22px; opacity: 0.55; letter-spacing: 0.05em; font-weight: 600;
}
.insta-card .main {
  font-size: 88px; line-height: 1.25; font-weight: 800; margin-top: auto; margin-bottom: 24px;
}
.insta-card.cover .main { font-size: 96px; }
.insta-card .sub {
  font-size: 36px; line-height: 1.5; opacity: 0.8; font-weight: 500;
}
.insta-card .brand {
  margin-top: auto; padding-top: 32px;
  font-size: 22px; opacity: 0.6; letter-spacing: 0.05em;
}
.caption-block {
  max-width: 1080px; margin: 48px auto 0;
  background: #fff; padding: 32px 40px; border-radius: 16px;
}
.caption-block h2 { margin-top: 0; }
.hashtags { color: #2563eb; word-break: break-all; }
@media print {
  body { background: #fff; padding: 0; }
  .print-note { display: none; }
  .insta-card { page-break-after: always; box-shadow: none; }
}
"""


_RX_SLIDE_HEADER = re.compile(r"^###\s+(\d+장)[^\n]*$", re.MULTILINE)


def _parse_insta_slides(md_text: str) -> list[dict]:
    """Pull each `### N장 — …` block. Returns list of {idx, header, main, sub}."""
    headers = list(_RX_SLIDE_HEADER.finditer(md_text))
    if not headers:
        return []
    out = []
    for i, m in enumerate(headers):
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(md_text)
        # Stop at next ## section (caption/디자인 메모) if encountered first
        next_h2 = md_text.find("\n## ", start)
        if next_h2 != -1 and next_h2 < end:
            end = next_h2
        block = md_text[start:end]
        header_label = m.group(0).lstrip("# ").strip()
        # main: first **bold** line; sub: first *italic* line
        main_m = re.search(r"\*\*([^*\n]+)\*\*", block)
        sub_m = re.search(r"(?:^|[^*])\*([^*\n]+)\*(?!\*)", block)
        out.append({
            "idx": m.group(1),  # "1장"
            "header": header_label,
            "main": (main_m.group(1).strip() if main_m else block.strip().splitlines()[0] if block.strip() else ""),
            "sub": (sub_m.group(1).strip() if sub_m else ""),
        })
    return out


def _extract_section(md_text: str, header: str) -> str:
    """Return body between `## <header>` and next `## ` or EOF."""
    pat = re.compile(rf"^##\s+{re.escape(header)}[^\n]*\n(.*?)(?=\n##\s|\Z)", re.DOTALL | re.MULTILINE)
    m = pat.search(md_text)
    return m.group(1).strip() if m else ""


def instagram_cards(md_text: str, *, title: str, brand: str = "", **_) -> str:
    slides = _parse_insta_slides(md_text)
    if not slides:
        # fall back to generic if parsing fails
        return generic(md_text, title=title)

    cards_html_parts = []
    for i, s in enumerate(slides):
        klass = "cover" if i == 0 else ("cta" if i == len(slides) - 1 else "")
        cards_html_parts.append(
            f'<div class="insta-card {klass}">'
            f'  <div class="slide-tag">{_html.escape(s["idx"])} · 1080 × 1350</div>'
            f'  <div>'
            f'    <div class="main">{_html.escape(s["main"])}</div>'
            f'    <div class="sub">{_html.escape(s["sub"])}</div>'
            f'  </div>'
            f'  <div class="brand">{_html.escape(brand or "Subtitle Marketing Studio")}</div>'
            f'</div>'
        )
    cards_html = "\n".join(cards_html_parts)

    caption_md = _extract_section(md_text, "인스타 캡션")
    design_md = _extract_section(md_text, "디자인 메모")
    caption_html = _md.markdown(caption_md, extensions=["extra", "nl2br"]) if caption_md else ""
    design_html = _md.markdown(design_md, extensions=["extra", "nl2br"]) if design_md else ""

    # Color hashtags blue in caption block
    if caption_html:
        caption_html = re.sub(
            r"(#[\w가-힣]+)",
            r'<span class="hashtags">\1</span>',
            caption_html,
        )

    body = (
        f'<h1>{_html.escape(title)}</h1>\n'
        '<p class="print-note">📐 인스타그램 캐러셀 5장 · 각 1080 × 1350 px [4:5] · '
        '브라우저에서 보거나 인쇄(Ctrl+P)로 PDF/이미지 출력 가능</p>\n'
        f'<div class="cards">{cards_html}</div>\n'
    )
    if caption_html:
        body += (
            '<div class="caption-block">\n'
            '<h2>인스타 캡션</h2>\n'
            f'{caption_html}\n'
            '</div>\n'
        )
    if design_html:
        body += (
            '<div class="caption-block">\n'
            '<h2>디자인 메모</h2>\n'
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
