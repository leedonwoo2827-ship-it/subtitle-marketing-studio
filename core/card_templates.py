"""Jinja2 card templates per channel.

Design pattern (per user direction):
- OUTER FRAME = channel identity (KakaoTalk yellow, Instagram gradient,
  Threads navy) — this is the strip readers see at a glance
- INNER CARD  = white background where text and imagery coexist
- All cards keep their channel's native aspect ratio (Threads/Instagram
  1080×1350, KakaoTalk 800×800)

LLM produces structured JSON; Jinja2 fills the template; Playwright
captures each `.studio-card[data-card-index]` as a PNG.
"""
from __future__ import annotations

import html as _html
import json
import re
from typing import Any

import jinja2

_GOOGLE_FONTS_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?'
    'family=Noto+Sans+KR:wght@300;400;500;700;800;900&'
    'family=Black+Han+Sans&'
    'family=Nanum+Myeongjo:wght@400;700;800&'
    'family=Gowun+Batang:wght@400;700&'
    'display=swap" rel="stylesheet">'
)

# Sans default = Noto Sans KR. Serif for storytelling = Nanum Myeongjo / Gowun Batang.
_FONTS_SANS = "'Noto Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif"
# Headline font intentionally NOT Black Han Sans — that face is single-weight
# and reads too chunky in card headlines. Use Noto Sans KR at weight 800.
_FONTS_DISPLAY = "'Noto Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif"
_FONTS_SERIF = "'Nanum Myeongjo', 'Gowun Batang', 'Apple SD Gothic Neo', serif"

# Shared rules — every template uses these via the wrap shell.
_BASE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 100%; }
body {
  background: #e5e7eb;
  font-family: """ + _FONTS_SANS + """;
  padding: 32px 16px;
  display: flex; flex-direction: column; align-items: center; gap: 40px;
}
.preamble {
  max-width: 1080px; width: 100%;
  padding: 14px 20px; background: #fff; border-radius: 12px;
  font-size: 13px; color: #6b7280; text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.studio-card {
  position: relative; overflow: hidden;
  box-shadow: 0 24px 60px rgba(0,0,0,0.18);
  font-family: """ + _FONTS_SANS + """;
  word-break: keep-all;
  display: flex;
  align-items: stretch; justify-content: stretch;
}
.studio-card .inner {
  width: 100%; height: 100%;
  background: #ffffff;
  color: #1f2937;
  padding: 64px 56px 48px;
  border-radius: 24px;
  display: flex; flex-direction: column;
  position: relative; overflow: hidden;
}
/* meta chrome removed — clean PNG for direct upload */
.studio-card .top-meta {
  display: flex; justify-content: flex-start; align-items: center;
}
.studio-card .badge {
  width: 72px; height: 72px; border-radius: 20px;
  display: flex; align-items: center; justify-content: center;
  font-size: 36px;
}
.studio-card .body {
  flex: 1; display: flex; flex-direction: column; justify-content: center;
  margin: 28px 0;
}
.studio-card .headline {
  font-family: """ + _FONTS_DISPLAY + """;
  font-weight: 800; letter-spacing: -0.02em; line-height: 1.2;
  margin-bottom: 24px;
}
.studio-card .subhead {
  font-weight: 500; line-height: 1.5; color: #4b5563;
}
.studio-card .tags-row {
  display: flex; gap: 10px; flex-wrap: wrap;
  margin-top: 28px;
}
.studio-card .tag {
  padding: 8px 18px; border-radius: 999px;
  font-size: 18px; font-weight: 700;
}
.studio-card .stat-block {
  margin-top: 28px; padding: 24px;
  border-radius: 14px;
}
.studio-card .stat-value { font-size: 52px; font-weight: 900; line-height: 1; }
.studio-card .stat-label { font-size: 20px; margin-top: 8px; color: #4b5563; }

.studio-card .caption-block {
  margin-top: 28px; padding: 24px;
  background: #f9fafb;
  border-radius: 16px;
}
.studio-card .caption-title {
  font-size: 16px; font-weight: 800; letter-spacing: 0.1em;
  text-transform: uppercase; margin-bottom: 12px; color: #6b7280;
}
.studio-card .caption-body { font-size: 22px; line-height: 1.6; color: #1f2937; }
.studio-card .hashtags-row {
  margin-top: 14px; font-size: 20px; font-weight: 700; word-break: break-all;
}
.studio-card .cta-pill {
  display: inline-block; padding: 16px 32px;
  border-radius: 999px; font-size: 24px; font-weight: 900;
  margin-top: 24px; align-self: flex-start;
}
/* Text layout: headline row (reserved space for vertical alignment across cards) +
   blocks-wrap (multi-block body) + tagline pinned to bottom via margin-top: auto. */
.studio-card .headline-row { /* min-height set per-channel */ }
.studio-card .blocks-wrap { padding-top: 4px; }
.studio-card .block { margin-bottom: 26px; }
.studio-card .block:last-of-type { margin-bottom: 0; }
.studio-card .block-subhead {
  font-weight: 800; line-height: 1.35; margin-bottom: 8px;
}
.studio-card .block-body { line-height: 1.7; white-space: pre-line; }
/* Tagline is always pinned to the bottom of the text area */
.studio-card .tagline { margin-top: auto; padding-top: 28px; }

@media print {
  body { background: #fff; padding: 0; gap: 0; }
  .preamble { display: none; }
  .studio-card { page-break-after: always; box-shadow: none; }
}
"""


# ─────────────────── per-channel frames ───────────────────
# Each channel sets:
#  - outer frame size / inner padding (controls how thick the channel-color border looks)
#  - channel-color gradient or solid
#  - channel-strip label/icon
#  - accent color used inside (tags, hashtags, stat numbers, CTA)

_TPL_THREADS_QUICK = """
<style>
  .threads-quick .studio-card {
    width: 1080px; height: 1350px;
    background: linear-gradient(160deg, #0f172a 0%, #1e3a8a 100%);
    padding: 28px;
    border-radius: 32px;
  }
  .threads-quick .inner {
    padding: 0; overflow: hidden;
    display: flex; flex-direction: column;
  }
  .threads-quick .visual-half {
    flex: 0 0 35%;
    background: linear-gradient(180deg, #dbeafe 0%, #bfdbfe 100%);
    display: flex; align-items: center; justify-content: center;
    position: relative; overflow: hidden;
  }
  .threads-quick .visual-half::before,
  .threads-quick .visual-half::after {
    content: ""; position: absolute; border-radius: 50%;
    border: 2px dashed rgba(30,58,138,0.18);
    pointer-events: none;
  }
  .threads-quick .visual-half::before { width: 380px; height: 380px; }
  .threads-quick .visual-half::after  { width: 240px; height: 240px; border-color: rgba(30,58,138,0.32); }
  .threads-quick .big-icon {
    font-size: 180px; line-height: 1;
    filter: drop-shadow(0 10px 20px rgba(30,58,138,0.32));
    position: relative; z-index: 2;
  }
  .threads-quick .text-half {
    flex: 1 1 65%;
    background: #ffffff;
    padding: 84px 60px 52px;
    display: flex; flex-direction: column;
    text-align: left;
  }
  .threads-quick .text-half .headline-row { min-height: 110px; margin-bottom: 28px; }
  .threads-quick .text-half .headline {
    font-family: """ + _FONTS_DISPLAY + """;
    font-size: 56px; font-weight: 800; color: #0f172a;
    line-height: 1.2; letter-spacing: -0.02em; margin: 0;
  }
  .threads-quick .text-half .block-subhead { font-size: 24px; color: #0f172a; }
  .threads-quick .text-half .block-body { font-size: 22px; color: #374151; }
  .threads-quick .text-half .tagline { font-size: 22px; color: #1e3a8a; font-weight: 800; }
</style>
<div class="threads-quick">
  <div class="preamble">📐 Threads 간결형 3장 · 1080 × 1350</div>
  {% for c in cards %}
  <div class="studio-card" data-card-index="{{ loop.index }}">
    <div class="inner">
      <div class="visual-half">
        <div class="big-icon">{{ c.icon | default('💬') }}</div>
      </div>
      <div class="text-half">
        <div class="headline-row">
          {% if loop.first and c.headline %}<div class="headline">{{ c.headline }}</div>{% endif %}
        </div>
        <div class="blocks-wrap">
          {% for b in c.blocks or [] %}
          <div class="block">
            {% if b.subhead %}<div class="block-subhead">{{ b.subhead }}</div>{% endif %}
            {% if b.body %}<div class="block-body">{{ b.body | sentence_break }}</div>{% endif %}
          </div>
          {% endfor %}
        </div>
        {% if c.tagline %}<div class="tagline">{{ c.tagline }}</div>{% endif %}
      </div>
    </div>
  </div>
  {% endfor %}
</div>
"""

_TPL_THREADS_INSIGHT = """
<style>
  .threads-insight .studio-card {
    width: 1080px; height: 1350px;
    background: linear-gradient(160deg, #1e1b4b 0%, #4338ca 100%);
    padding: 28px;
    border-radius: 32px;
  }
  .threads-insight .inner {
    padding: 0;
    overflow: hidden;
    display: flex; flex-direction: column;
  }
  /* TOP HALF — large illustration / emoji centerpiece */
  .threads-insight .visual-half {
    flex: 0 0 35%;
    background: linear-gradient(180deg, #ede9fe 0%, #ddd6fe 100%);
    display: flex; align-items: center; justify-content: center;
    position: relative; overflow: hidden;
  }
  .threads-insight .visual-half::before,
  .threads-insight .visual-half::after {
    content: "";
    position: absolute; border-radius: 50%;
    border: 2px dashed rgba(67,56,202,0.18);
    pointer-events: none;
  }
  .threads-insight .visual-half::before { width: 380px; height: 380px; }
  .threads-insight .visual-half::after  { width: 240px; height: 240px; border-color: rgba(67,56,202,0.30); }
  .threads-insight .big-icon {
    font-size: 180px; line-height: 1;
    filter: drop-shadow(0 10px 20px rgba(67,56,202,0.32));
    position: relative; z-index: 2;
  }
  /* BOTTOM ~65% — left-aligned text, generous body */
  .threads-insight .text-half {
    flex: 1 1 65%;
    background: #ffffff;
    padding: 84px 60px 52px;
    display: flex; flex-direction: column;
    text-align: left;
  }
  .threads-insight .text-half .headline-row { min-height: 100px; margin-bottom: 26px; }
  .threads-insight .text-half .headline {
    font-family: """ + _FONTS_DISPLAY + """;
    font-size: 52px; font-weight: 800; color: #1e1b4b;
    line-height: 1.2; letter-spacing: -0.02em; margin: 0;
  }
  .threads-insight .text-half .block-subhead { font-size: 24px; color: #1e1b4b; }
  .threads-insight .text-half .block-body { font-size: 22px; color: #374151; }
  .threads-insight .text-half .stat-block {
    margin-top: 14px; padding: 14px 20px;
    background: #ede9fe; border-left: 6px solid #4338ca; border-radius: 0 10px 10px 0;
  }
  .threads-insight .text-half .stat-value { font-size: 36px; font-weight: 900; color: #4338ca; }
  .threads-insight .text-half .stat-label { font-size: 18px; color: #4b5563; margin-top: 4px; }
  .threads-insight .text-half .tagline { font-size: 22px; color: #4338ca; font-weight: 800; }
</style>
<div class="threads-insight">
  <div class="preamble">📐 Threads 인사이트 5장 · 1080 × 1350</div>
  {% for c in cards %}
  <div class="studio-card" data-card-index="{{ loop.index }}">
    <div class="inner">
      <div class="visual-half">
        <div class="big-icon">{{ c.icon | default('💡') }}</div>
      </div>
      <div class="text-half">
        <div class="headline-row">
          {% if loop.first and c.headline %}<div class="headline">{{ c.headline }}</div>{% endif %}
        </div>
        <div class="blocks-wrap">
          {% for b in c.blocks or [] %}
          <div class="block">
            {% if b.subhead %}<div class="block-subhead">{{ b.subhead }}</div>{% endif %}
            {% if b.body %}<div class="block-body">{{ b.body | sentence_break }}</div>{% endif %}
          </div>
          {% endfor %}
          {% if c.stat %}
          <div class="stat-block">
            <div class="stat-value">{{ c.stat.value | default('') }}</div>
            <div class="stat-label">{{ c.stat.label | default('') }}</div>
          </div>
          {% endif %}
        </div>
        {% if c.tagline %}<div class="tagline">{{ c.tagline }}</div>{% endif %}
      </div>
    </div>
  </div>
  {% endfor %}
</div>
"""

_TPL_INSTAGRAM_INFO = """
<style>
  .ig-info .studio-card {
    width: 1080px; height: 1350px;
    background: linear-gradient(135deg, #fbbf24 0%, #ec4899 50%, #8b5cf6 100%);
    padding: 28px;
    border-radius: 32px;
  }
  .ig-info .inner { padding: 0; overflow: hidden; display: flex; flex-direction: column; }
  .ig-info .visual-half {
    flex: 0 0 35%;
    background: linear-gradient(180deg, #fef3c7 0%, #fce7f3 100%);
    display: flex; align-items: center; justify-content: center;
    position: relative; overflow: hidden;
  }
  .ig-info .visual-half::before { content: ""; position: absolute; width: 360px; height: 360px;
    border: 2px dashed rgba(157,23,77,0.22); border-radius: 50%; pointer-events: none; }
  .ig-info .big-icon {
    font-size: 180px; line-height: 1; position: relative; z-index: 2;
    filter: drop-shadow(0 8px 18px rgba(157,23,77,0.30));
  }
  .ig-info .text-half {
    flex: 1 1 65%; background: #ffffff;
    padding: 52px 60px;
    display: flex; flex-direction: column; text-align: left;
  }
  .ig-info .text-half .headline-row { min-height: 100px; margin-bottom: 24px; }
  .ig-info .text-half .headline {
    font-family: """ + _FONTS_DISPLAY + """;
    font-size: 52px; font-weight: 800; color: #1f2937;
    line-height: 1.2; letter-spacing: -0.02em; margin: 0;
  }
  .ig-info .text-half .block-subhead { font-size: 24px; color: #9d174d; }
  .ig-info .text-half .block-body { font-size: 22px; color: #374151; }
  .ig-info .text-half .tags-row { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }
  .ig-info .text-half .tag {
    padding: 6px 14px; border-radius: 999px;
    background: #fce7f3; color: #9d174d; border: 2px solid #fbcfe8;
    font-size: 17px; font-weight: 700;
  }
  .ig-info .text-half .tagline { font-size: 20px; color: #be185d; font-weight: 800; }
</style>
<div class="ig-info">
  <div class="preamble">📐 Instagram 정보형 5장 · 1080 × 1350</div>
  {% for c in cards %}
  <div class="studio-card" data-card-index="{{ loop.index }}">
    <div class="inner">
      <div class="visual-half">
        <div class="big-icon">{{ c.icon | default('✨') }}</div>
      </div>
      <div class="text-half">
        <div class="headline-row">
          {% if loop.first and c.headline %}<div class="headline">{{ c.headline }}</div>{% endif %}
        </div>
        <div class="blocks-wrap">
          {% for b in c.blocks or [] %}
          <div class="block">
            {% if b.subhead %}<div class="block-subhead">{{ b.subhead }}</div>{% endif %}
            {% if b.body %}<div class="block-body">{{ b.body | sentence_break }}</div>{% endif %}
          </div>
          {% endfor %}
          {% if c.tags %}
          <div class="tags-row">
            {% for t in c.tags %}<span class="tag">#{{ t }}</span>{% endfor %}
          </div>
          {% endif %}
        </div>
        {% if c.tagline %}<div class="tagline">{{ c.tagline }}</div>{% endif %}
      </div>
    </div>
  </div>
  {% endfor %}
</div>
"""

_TPL_INSTAGRAM_STORY = """
<style>
  .ig-story .studio-card {
    width: 1080px; height: 1350px;
    background: linear-gradient(170deg, #44403c 0%, #78716c 50%, #a8a29e 100%);
    padding: 28px;
    border-radius: 32px;
  }
  .ig-story .inner { padding: 0; overflow: hidden; display: flex; flex-direction: column; background: #fefcf8; }
  .ig-story .visual-half {
    flex: 0 0 35%;
    background: linear-gradient(180deg, #fef2f2 0%, #fed7aa 100%);
    display: flex; align-items: center; justify-content: center;
    position: relative; overflow: hidden;
  }
  .ig-story .visual-half::before {
    content: ""; position: absolute; inset: 0;
    background-image: radial-gradient(circle at 50% 50%, transparent 40%, rgba(68,64,60,0.10) 100%);
    pointer-events: none;
  }
  .ig-story .big-icon {
    font-size: 180px; line-height: 1;
    filter: drop-shadow(0 10px 20px rgba(68,64,60,0.28));
    position: relative; z-index: 2;
  }
  .ig-story .text-half {
    flex: 1 1 65%;
    background: #fefcf8;
    padding: 84px 60px 52px;
    display: flex; flex-direction: column;
    text-align: left;
    color: #292524;
  }
  .ig-story .text-half .headline-row { min-height: 100px; margin-bottom: 24px; }
  .ig-story .text-half .headline {
    font-family: """ + _FONTS_SERIF + """;
    font-weight: 800; font-size: 56px; color: #1c1917;
    line-height: 1.25; letter-spacing: -0.005em; margin: 0;
  }
  .ig-story .text-half .block-subhead {
    font-family: """ + _FONTS_SERIF + """;
    font-size: 24px; color: #292524; font-weight: 700;
  }
  .ig-story .text-half .block-body {
    font-family: """ + _FONTS_SERIF + """;
    font-size: 22px; color: #44403c;
  }
  .ig-story .text-half .tagline {
    font-family: """ + _FONTS_SERIF + """;
    font-size: 22px; color: #78716c; font-style: italic;
  }
</style>
<div class="ig-story">
  <div class="preamble">📐 Instagram 스토리텔링 7장 · 1080 × 1350 · 명조</div>
  {% for c in cards %}
  <div class="studio-card" data-card-index="{{ loop.index }}">
    <div class="inner">
      <div class="visual-half">
        <div class="big-icon">{{ c.icon | default('🌅') }}</div>
      </div>
      <div class="text-half">
        <div class="headline-row">
          {% if loop.first and c.headline %}<div class="headline">{{ c.headline }}</div>{% endif %}
        </div>
        <div class="blocks-wrap">
          {% for b in c.blocks or [] %}
          <div class="block">
            {% if b.subhead %}<div class="block-subhead">{{ b.subhead }}</div>{% endif %}
            {% if b.body %}<div class="block-body">{{ b.body | sentence_break }}</div>{% endif %}
          </div>
          {% endfor %}
        </div>
        {% if c.tagline %}<div class="tagline">{{ c.tagline }}</div>{% endif %}
      </div>
    </div>
  </div>
  {% endfor %}
</div>
"""

_TPL_KAKAO = """
<style>
  .kk .studio-card {
    width: 800px; height: 800px;
    background: linear-gradient(160deg, #fde047 0%, #facc15 50%, #eab308 100%);
    padding: 22px;
    border-radius: 28px;
  }
  .kk .inner { padding: 0; overflow: hidden; display: flex; flex-direction: column; }
  .kk .visual-half {
    flex: 0 0 32%;
    background: linear-gradient(180deg, #fef9c3 0%, #fde68a 100%);
    display: flex; align-items: center; justify-content: center;
    position: relative; overflow: hidden;
  }
  .kk .visual-half::before { content: ""; position: absolute; width: 240px; height: 240px;
    border: 2px dashed rgba(66,32,6,0.24); border-radius: 50%; pointer-events: none; }
  .kk .big-icon {
    font-size: 130px; line-height: 1; position: relative; z-index: 2;
    filter: drop-shadow(0 6px 14px rgba(66,32,6,0.30));
  }
  .kk .text-half {
    flex: 1 1 68%; background: #ffffff;
    padding: 60px 40px 36px;
    display: flex; flex-direction: column; text-align: left;
  }
  .kk .text-half .headline-row { min-height: 70px; margin-bottom: 16px; }
  .kk .text-half .headline {
    font-family: """ + _FONTS_DISPLAY + """;
    font-size: 36px; font-weight: 800; color: #1c1917;
    line-height: 1.25; letter-spacing: -0.02em; margin: 0;
  }
  .kk .text-half .block { margin-bottom: 16px; }
  .kk .text-half .block-subhead { font-size: 18px; color: #422006; }
  .kk .text-half .block-body { font-size: 16px; color: #292524; }
  .kk .text-half .tagline { font-size: 16px; color: #b45309; font-weight: 800; }
</style>
<div class="kk">
  <div class="preamble">📐 KakaoTalk 카드뉴스 · 800 × 800</div>
  {% for c in cards %}
  <div class="studio-card" data-card-index="{{ loop.index }}">
    <div class="inner">
      <div class="visual-half">
        <div class="big-icon">{{ c.icon | default('💬') }}</div>
      </div>
      <div class="text-half">
        <div class="headline-row">
          {% if loop.first and c.headline %}<div class="headline">{{ c.headline }}</div>{% endif %}
        </div>
        <div class="blocks-wrap">
          {% for b in c.blocks or [] %}
          <div class="block">
            {% if b.subhead %}<div class="block-subhead">{{ b.subhead }}</div>{% endif %}
            {% if b.body %}<div class="block-body">{{ b.body | sentence_break }}</div>{% endif %}
          </div>
          {% endfor %}
        </div>
        {% if c.tagline %}<div class="tagline">{{ c.tagline }}</div>{% endif %}
      </div>
    </div>
  </div>
  {% endfor %}
</div>
"""


_TEMPLATES: dict[str, str] = {
    "cards_threads_quick":   _TPL_THREADS_QUICK,
    "cards_threads_insight": _TPL_THREADS_INSIGHT,
    "cards_instagram_info":  _TPL_INSTAGRAM_INFO,
    "cards_instagram_story": _TPL_INSTAGRAM_STORY,
    "cards_kakao":           _TPL_KAKAO,
}


_RX_SENTENCE_END = re.compile(r"([.!?])[ \t]+(?=\S)")


def _sentence_break(text: str | None) -> str:
    """Insert a newline after every sentence-ending period/!/? followed by
    whitespace, so blocks of prose break visually with `white-space: pre-line`."""
    if not text:
        return ""
    return _RX_SENTENCE_END.sub(r"\1\n", str(text))


def _env() -> jinja2.Environment:
    env = jinja2.Environment(autoescape=True, trim_blocks=True, lstrip_blocks=True)
    env.filters["sentence_break"] = _sentence_break
    return env


def render_cards(channel_key: str, data: dict, *, title: str, brand: str = "") -> str:
    tpl_src = _TEMPLATES.get(channel_key)
    if not tpl_src:
        raise ValueError(f"unknown card template: {channel_key}")
    env = _env()
    tpl = env.from_string(tpl_src)
    body = tpl.render(
        cards=data.get("cards", []),
        caption=data.get("caption", ""),
        hashtags=data.get("hashtags", ""),
        cta=data.get("cta", ""),
        button=data.get("button", ""),
        brand=brand or "Subtitle Marketing Studio",
    )
    return _wrap(title, body)


def _wrap(title: str, body_html: str) -> str:
    return (
        '<!doctype html>\n'
        '<html lang="ko"><head>\n'
        '<meta charset="utf-8">\n'
        f'<title>{_html.escape(title)}</title>\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        + _GOOGLE_FONTS_LINK + '\n'
        f'<style>{_BASE_CSS}</style>\n'
        '</head><body>\n'
        f'{body_html}\n'
        '</body></html>\n'
    )


def _fix_llm_json(payload: str) -> str:
    """Repair common LLM-JSON glitches before json.loads.

    The Korean card prompts produce JSON-like text where the model
    sometimes:
      - writes literal newlines/tabs inside string values (illegal JSON)
      - uses smart quotes `“ ” ‘ ’` instead of ASCII `" '`
      - leaves a trailing comma before `}` or `]`
    """
    # 1) Smart quotes → ASCII
    payload = (payload
               .replace("“", '"').replace("”", '"')
               .replace("‘", "'").replace("’", "'"))
    # 2) Escape literal newlines / CR / tabs inside string literals.
    #    Walk the text tracking string state.
    out: list[str] = []
    in_str = False
    escape = False
    for ch in payload:
        if escape:
            out.append(ch)
            escape = False
            continue
        if ch == "\\":
            out.append(ch)
            escape = True
            continue
        if ch == '"':
            in_str = not in_str
            out.append(ch)
            continue
        if in_str:
            if ch == "\n":
                out.append("\\n")
                continue
            if ch == "\r":
                out.append("\\r")
                continue
            if ch == "\t":
                out.append("\\t")
                continue
        out.append(ch)
    fixed = "".join(out)
    # 3) Trailing commas before `}` or `]`
    fixed = re.sub(r",(\s*[}\]])", r"\1", fixed)
    return fixed


def parse_card_json(text: str) -> dict:
    """Pull JSON from LLM output (handles ```json … ``` fences, prose,
    smart quotes, literal newlines in strings, trailing commas)."""
    m = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    payload = m.group(1).strip() if m else text.strip()
    start = payload.find("{")
    end = payload.rfind("}")
    if start >= 0 and end > start:
        payload = payload[start : end + 1]
    # Try strict first; if that fails, apply the LLM-quirk fixer and retry.
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return json.loads(_fix_llm_json(payload))


_CHANNEL_LABEL = {
    "cards_threads_quick":   "Threads",
    "cards_threads_insight": "Threads (인사이트)",
    "cards_instagram_info":  "Instagram",
    "cards_instagram_story": "Instagram (스토리텔링)",
    "cards_kakao":           "KakaoTalk",
}


def format_md_draft(channel_key: str, data: dict, *, title: str) -> str:
    """Build a human-readable Markdown draft from the card JSON.

    First section is the channel-ready SNS body (caption + hashtags) that the
    user copies into the Threads / Instagram / KakaoTalk post text field.
    Second section is the per-card content for reference (also useful when
    only PNG cards are exported).
    """
    cards = data.get("cards") or []
    caption = (data.get("caption") or "").strip()
    hashtags = (data.get("hashtags") or "").strip()
    button = (data.get("button") or "").strip()
    channel_name = _CHANNEL_LABEL.get(channel_key, "SNS")

    out: list[str] = [f"# {title}", ""]

    out.append(f"## 📝 {channel_name} 본문 초안")
    out.append("")
    out.append("> 아래 텍스트를 그대로 채널의 본문 입력란에 붙여넣기.")
    out.append("")

    if caption:
        out.append(caption.strip())
        out.append("")
    else:
        # No explicit caption (e.g., Threads). Synthesise from card 1.
        if cards:
            c0 = cards[0]
            if c0.get("headline"):
                out.append(f"**{c0['headline']}**")
                out.append("")
            for b in c0.get("blocks") or []:
                if b.get("body"):
                    out.append(b["body"].strip())
                    out.append("")
            if c0.get("tagline"):
                out.append(f"_{c0['tagline']}_")
                out.append("")

    if hashtags:
        out.append(hashtags)
        out.append("")

    if button:
        out.append(f"**버튼 라벨**: `{button}`")
        out.append("")

    out.append("---")
    out.append("")
    out.append(f"## 🖼 카드별 내용 ({len(cards)}장)")
    out.append("")

    for i, c in enumerate(cards, start=1):
        icon = (c.get("icon") or "").strip()
        head = (c.get("headline") or "").strip()
        header_text = f"카드 {i}"
        if icon:
            header_text += f" · {icon}"
        if i == 1 and head:
            header_text += f" · {head}"
        out.append(f"### {header_text}")
        out.append("")

        for b in c.get("blocks") or []:
            sub = (b.get("subhead") or "").strip()
            body = (b.get("body") or "").strip()
            if sub:
                out.append(f"**{sub}**")
            if body:
                out.append(body)
            if sub or body:
                out.append("")

        stat = c.get("stat") or {}
        if stat.get("value") or stat.get("label"):
            out.append(f"📊 **{stat.get('value', '').strip()}** — {stat.get('label', '').strip()}")
            out.append("")

        tags = c.get("tags") or []
        if tags:
            out.append(" ".join(f"#{t}" for t in tags))
            out.append("")

        if c.get("tagline"):
            out.append(f"> {c['tagline'].strip()}")
            out.append("")

    return "\n".join(out).rstrip() + "\n"
