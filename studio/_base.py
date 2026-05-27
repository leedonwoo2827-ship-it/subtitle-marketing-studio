"""Base classes for studios."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


@dataclass
class StudioContext:
    project_dir: Path
    subtitle_text: str
    channel_guide: str
    llm: Any
    extra: dict = field(default_factory=dict)
    parallelism: int = 4
    max_tokens: int = 8192
    temperature: float = 0.7


def load_prompt(key: str) -> str:
    path = PROMPTS_DIR / f"{key}_ko.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def split_system_user(prompt: str) -> tuple[str, str]:
    m_sys = re.search(r"<<SYSTEM>>\s*(.*?)\s*(?=<<USER>>|$)", prompt, re.DOTALL)
    m_usr = re.search(r"<<USER>>\s*(.*)", prompt, re.DOTALL)
    system = m_sys.group(1).strip() if m_sys else ""
    user = m_usr.group(1).strip() if m_usr else prompt.strip()
    return system, user


def extract_channel_section(guide: str, section_key: str | None) -> str:
    """Pull a `### <section>` block from channel-style-research.md.

    None or missing → returns PART 0 + PART 1 (overview).
    """
    if not section_key:
        return _slice_until(guide, ["## PART 0."], ["## PART 2."])
    pattern = re.compile(
        rf"###\s+{re.escape(section_key)}[^\n]*\n(.*?)(?=\n###\s|\n##\s|\Z)",
        re.DOTALL,
    )
    m = pattern.search(guide)
    if not m:
        return guide
    return f"### {section_key}\n{m.group(1).strip()}"


def _slice_until(text: str, start_markers: list[str], stop_markers: list[str]) -> str:
    start = 0
    for sm in start_markers:
        i = text.find(sm)
        if i >= 0:
            start = i
            break
    end = len(text)
    for sm in stop_markers:
        j = text.find(sm, start + 1)
        if j > 0:
            end = j
            break
    return text[start:end].strip()


_RX_PLACEHOLDER = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def _safe_format(template: str, mapping: dict) -> str:
    """Substitute only `{identifier}` placeholders present in `mapping`.

    Leaves anything else inside braces (e.g. JSON examples in the prompt
    like `{ "role": "후킹" }`) completely untouched. This is safer than
    `str.format_map` which tries to parse anything between `{...}` as a
    format spec and chokes on JSON.
    """
    def _repl(m):
        key = m.group(1)
        return str(mapping[key]) if key in mapping else m.group(0)
    return _RX_PLACEHOLDER.sub(_repl, template)


class StudioBase:
    key: str = ""
    order: int = 0
    title: str = ""
    section: str = ""                    # "카드뉴스·기타" / "블로그"
    channel_section: str | None = None
    description: str = ""
    max_tokens: int = 0                  # 0 = use ctx default; override per-studio
    html_renderer: str = "generic"       # core.html_render.RENDERERS key
    png_renderer: str = ""               # core.png_render: Playwright fallback (HTML→PNG); "" disables
    image_renderer: str = ""             # core.image_render: Nano Banana image gen; "" disables
    docx_renderer: str = ""              # core.docx_render.RENDERERS key; "" = no DOCX
    output_filename: str = "output.md"

    def render(self, ctx: StudioContext) -> str:
        prompt = load_prompt(self.key)
        system, user = split_system_user(prompt)
        guide_excerpt = extract_channel_section(ctx.channel_guide, self.channel_section)
        bindings = {
            "subtitle": ctx.subtitle_text,
            "channel_guide": guide_excerpt,
            "target_keyword": ctx.extra.get("target_keyword", ""),
            "brand_name": ctx.extra.get("brand_name", ""),
            **ctx.extra,
        }
        system_filled = _safe_format(system, bindings)
        user_filled = _safe_format(user, bindings)
        budget = self.max_tokens or getattr(ctx, "max_tokens", 8192)
        return ctx.llm.generate(
            system_filled,
            user_filled,
            max_tokens=budget,
            temperature=getattr(ctx, "temperature", 0.7),
        )
