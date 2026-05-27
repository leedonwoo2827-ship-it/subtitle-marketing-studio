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
_FONTS_DISPLAY = "'Black Han Sans', 'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif"
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
.studio-card .channel-strip {
  position: absolute; top: 0; left: 0; right: 0;
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 28px;
  font-size: 18px; font-weight: 800; letter-spacing: 0.06em;
  color: #fff; z-index: 3;
}
.studio-card .channel-strip .ch-dot {
  display: inline-flex; gap: 6px;
}
.studio-card .channel-strip .ch-dot span {
  width: 12px; height: 12px; border-radius: 50%;
  background: rgba(255,255,255,0.45);
}
.studio-card .channel-strip .ch-dot span:first-child { background: #fff; }

.studio-card .top-meta {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 36px;
}
.studio-card .badge {
  width: 80px; height: 80px; border-radius: 22px;
  display: flex; align-items: center; justify-content: center;
  font-size: 40px;
}
.studio-card .role-tag {
  padding: 8px 18px; border-radius: 999px;
  font-size: 16px; font-weight: 800; letter-spacing: 0.06em;
  text-transform: uppercase;
}
.studio-card .body {
  flex: 1; display: flex; flex-direction: column; justify-content: center;
  margin: 28px 0;
}
.studio-card .headline {
  font-family: """ + _FONTS_DISPLAY + """;
  font-weight: 900; letter-spacing: -0.02em; line-height: 1.2;
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
.studio-card .footer {
  margin-top: auto; padding-top: 24px;
  display: flex; justify-content: space-between; align-items: flex-end;
  font-size: 18px; color: #6b7280;
  border-top: 1px solid #e5e7eb;
}

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
  .threads-quick .channel-strip { background: transparent; }
  .threads-quick .channel-strip .ch-name { color: #fbbf24; }
  .threads-quick .badge { background: #fef3c7; color: #78350f; }
  .threads-quick .role-tag { background: #1e3a8a; color: #fbbf24; }
  .threads-quick .headline { font-size: 76px; color: #0f172a; }
  .threads-quick .tag { background: #1e3a8a; color: #fef3c7; }
  .threads-quick .cta-pill { background: #1e3a8a; color: #fef3c7; }
  .threads-quick .hashtags-row { color: #1e3a8a; }
</style>
<div class="threads-quick">
  <div class="preamble">📐 Threads 카드뉴스 3장 · 1080 × 1350 · 외곽 네이비 + 내부 화이트</div>
  {% for c in cards %}
  <div class="studio-card" data-card-index="{{ loop.index }}">
    <div class="channel-strip">
      <span class="ch-name">@ Threads · {{ loop.index }}/{{ cards|length }}</span>
      <span class="ch-dot"><span></span><span></span><span></span></span>
    </div>
    <div class="inner">
      <div class="top-meta">
        <div class="badge">{{ c.icon | default('💬') }}</div>
        <div class="role-tag">{{ c.role | default('') }}</div>
      </div>
      <div class="body">
        <div class="headline">{{ c.headline | default('') }}</div>
        <div class="subhead">{{ c.subhead | default('') }}</div>
        {% if loop.last and c.cta %}<div class="cta-pill">{{ c.cta }}</div>{% endif %}
        {% if loop.last and hashtags %}<div class="hashtags-row">{{ hashtags }}</div>{% endif %}
      </div>
      <div class="footer">
        <div>{{ brand }}</div>
        <div>1080 × 1350</div>
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
  .threads-insight .channel-strip .ch-name { color: #c7d2fe; }
  .threads-insight .badge { background: #ede9fe; color: #4338ca; }
  .threads-insight .role-tag { background: #4338ca; color: #ede9fe; }
  .threads-insight .headline { font-size: 64px; color: #1e1b4b; }
  .threads-insight .tag { background: #ede9fe; color: #4338ca; }
  .threads-insight .stat-block { background: #ede9fe; border-left: 6px solid #4338ca; }
  .threads-insight .stat-value { color: #4338ca; }
  .threads-insight .hashtags-row { color: #4338ca; }
</style>
<div class="threads-insight">
  <div class="preamble">📐 Threads 인사이트 5장 · 1080 × 1350</div>
  {% for c in cards %}
  <div class="studio-card" data-card-index="{{ loop.index }}">
    <div class="channel-strip">
      <span class="ch-name">@ Threads · Insight · {{ loop.index }}/{{ cards|length }}</span>
      <span class="ch-dot"><span></span><span></span><span></span></span>
    </div>
    <div class="inner">
      <div class="top-meta">
        <div class="badge">{{ c.icon | default('📊') }}</div>
        <div class="role-tag">{{ '%02d'|format(loop.index) }} · {{ c.role | default('') }}</div>
      </div>
      <div class="body">
        <div class="headline">{{ c.headline | default('') }}</div>
        <div class="subhead">{{ c.subhead | default('') }}</div>
        {% if c.stat %}
        <div class="stat-block">
          <div class="stat-value">{{ c.stat.value | default('') }}</div>
          <div class="stat-label">{{ c.stat.label | default('') }}</div>
        </div>
        {% endif %}
        {% if loop.last and hashtags %}<div class="hashtags-row">{{ hashtags }}</div>{% endif %}
      </div>
      <div class="footer">
        <div>{{ brand }}</div>
        <div>1080 × 1350</div>
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
  .ig-info .channel-strip .ch-name { color: #fff; }
  .ig-info .badge { background: linear-gradient(135deg, #fef3c7, #fce7f3); color: #9d174d; }
  .ig-info .role-tag { background: #db2777; color: #fff; }
  .ig-info .headline { font-size: 72px; color: #1f2937; }
  .ig-info .tag { background: #fce7f3; color: #9d174d; border: 2px solid #fbcfe8; }
  .ig-info .cta-pill { background: #1f2937; color: #fff; }
  .ig-info .caption-block { background: linear-gradient(135deg, #fef3c7 0%, #fce7f3 100%); }
  .ig-info .caption-title { color: #9d174d; }
  .ig-info .hashtags-row { color: #be185d; }
</style>
<div class="ig-info">
  <div class="preamble">📐 Instagram 정보형 5장 · 1080 × 1350 · 5장에 캡션·해시태그 내장</div>
  {% for c in cards %}
  <div class="studio-card" data-card-index="{{ loop.index }}">
    <div class="channel-strip">
      <span class="ch-name">⊙ Instagram · {{ loop.index }}/{{ cards|length }}</span>
      <span class="ch-dot"><span></span><span></span><span></span></span>
    </div>
    <div class="inner">
      <div class="top-meta">
        <div class="badge">{{ c.icon | default('✨') }}</div>
        <div class="role-tag">{{ '%02d'|format(loop.index) }} · {{ c.role | default('') }}</div>
      </div>
      <div class="body">
        <div class="headline">{{ c.headline | default('') }}</div>
        <div class="subhead">{{ c.subhead | default('') }}</div>
        {% if c.tags %}
        <div class="tags-row">
          {% for t in c.tags %}<span class="tag">#{{ t }}</span>{% endfor %}
        </div>
        {% endif %}
        {% if loop.last and caption %}
        <div class="caption-block">
          <div class="caption-title">💬 Caption</div>
          <div class="caption-body">{{ caption }}</div>
          {% if hashtags %}<div class="hashtags-row">{{ hashtags }}</div>{% endif %}
        </div>
        {% endif %}
        {% if loop.last and cta %}<div class="cta-pill">{{ cta }}</div>{% endif %}
      </div>
      <div class="footer">
        <div>{{ brand }}</div>
        <div>1080 × 1350</div>
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
  .ig-story .inner {
    background: #fefcf8;
    color: #292524;
  }
  .ig-story .channel-strip .ch-name { color: #fafaf9; font-style: italic; font-family: """ + _FONTS_SERIF + """; }
  .ig-story .badge { background: #292524; color: #fefcf8; border-radius: 50%; }
  .ig-story .role-tag { background: transparent; color: #78716c; font-family: """ + _FONTS_SERIF + """; font-style: italic; }
  .ig-story .headline {
    font-family: """ + _FONTS_SERIF + """;
    font-weight: 800; font-size: 68px; color: #1c1917; letter-spacing: -0.005em;
  }
  .ig-story .subhead { color: #57534e; font-size: 28px; }
  .ig-story .caption-block { background: #f5f5f4; }
  .ig-story .caption-body { font-family: """ + _FONTS_SERIF + """; }
  .ig-story .hashtags-row { color: #78716c; }
</style>
<div class="ig-story">
  <div class="preamble">📐 Instagram 스토리텔링 7장 · 1080 × 1350 · 7장에 캡션 내장</div>
  {% for c in cards %}
  <div class="studio-card" data-card-index="{{ loop.index }}">
    <div class="channel-strip">
      <span class="ch-name">— Instagram · chapter {{ loop.index }}/{{ cards|length }} —</span>
      <span class="ch-dot"><span></span><span></span><span></span></span>
    </div>
    <div class="inner">
      <div class="top-meta">
        <div class="badge">{{ c.icon | default('🌅') }}</div>
        <div class="role-tag">— {{ c.role | default('') }} —</div>
      </div>
      <div class="body">
        <div class="headline">{{ c.headline | default('') }}</div>
        <div class="subhead">{{ c.subhead | default('') }}</div>
        {% if loop.last and caption %}
        <div class="caption-block">
          <div class="caption-body">{{ caption }}</div>
          {% if hashtags %}<div class="hashtags-row">{{ hashtags }}</div>{% endif %}
        </div>
        {% endif %}
      </div>
      <div class="footer">
        <div>— {{ brand }} —</div>
        <div>1080 × 1350</div>
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
    padding: 26px;
    border-radius: 28px;
  }
  .kk .inner { padding: 48px 44px 36px; }
  .kk .channel-strip .ch-name { color: #422006; }
  .kk .channel-strip .ch-dot span { background: rgba(66,32,6,0.35); }
  .kk .channel-strip .ch-dot span:first-child { background: #422006; }
  .kk .badge { background: #fef3c7; color: #78350f; width: 64px; height: 64px; font-size: 32px; border-radius: 18px; }
  .kk .role-tag { background: #422006; color: #fde047; font-size: 14px; padding: 6px 14px; }
  .kk .top-meta { margin-top: 28px; }
  .kk .headline { font-size: 48px; color: #1c1917; margin-bottom: 16px; }
  .kk .subhead { font-size: 22px; }
  .kk .cta-pill {
    background: #422006; color: #fde047;
    border-radius: 12px;
    font-size: 20px; padding: 12px 24px;
    margin-top: 24px;
  }
  .kk .footer { font-size: 14px; }
</style>
<div class="kk">
  <div class="preamble">📐 KakaoTalk 카드뉴스 · 800 × 800 · 외곽 노랑 + 내부 화이트</div>
  {% for c in cards %}
  <div class="studio-card" data-card-index="{{ loop.index }}">
    <div class="channel-strip">
      <span class="ch-name">💬 KakaoTalk · {{ loop.index }}/{{ cards|length }}</span>
      <span class="ch-dot"><span></span><span></span><span></span></span>
    </div>
    <div class="inner">
      <div class="top-meta">
        <div class="badge">{{ c.icon | default('💬') }}</div>
        <div class="role-tag">{{ '%02d'|format(loop.index) }} · {{ c.role | default('') }}</div>
      </div>
      <div class="body">
        <div class="headline">{{ c.headline | default('') }}</div>
        <div class="subhead">{{ c.subhead | default('') }}</div>
        {% if c.button %}<div class="cta-pill">{{ c.button }}</div>{% endif %}
      </div>
      <div class="footer">
        <div>{{ brand }}</div>
        <div>800 × 800</div>
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


def _env() -> jinja2.Environment:
    return jinja2.Environment(autoescape=True, trim_blocks=True, lstrip_blocks=True)


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


def parse_card_json(text: str) -> dict:
    """Pull JSON from LLM output (handles ```json … ``` fences and prose)."""
    m = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    payload = m.group(1).strip() if m else text.strip()
    start = payload.find("{")
    end = payload.rfind("}")
    if start >= 0 and end > start:
        payload = payload[start : end + 1]
    return json.loads(payload)
