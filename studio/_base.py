"""Base classes for studios. Mirrors tsbookmaker's StudioBase contract."""
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
    channel_guide: str           # full content of knowledge/channel-style-research.md
    llm: Any                     # LLMProvider
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
    """Parse `<<SYSTEM>>` / `<<USER>>` delimited prompt file."""
    m_sys = re.search(r"<<SYSTEM>>\s*(.*?)\s*(?=<<USER>>|$)", prompt, re.DOTALL)
    m_usr = re.search(r"<<USER>>\s*(.*)", prompt, re.DOTALL)
    system = m_sys.group(1).strip() if m_sys else ""
    user = m_usr.group(1).strip() if m_usr else prompt.strip()
    return system, user


def extract_channel_section(guide: str, section_key: str | None) -> str:
    """Pull a single `### <section>` block from channel-style-research.md.

    If section_key is None, return PART 0 + PART 1 only (compact overview).
    If section header not found, fall back to the full guide.
    """
    if not section_key:
        return _slice_until(guide, start_markers=["## PART 0."], stop_markers=["## PART 2."])
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


def _safe_format(template: str, mapping: dict) -> str:
    """Format with `{name}` placeholders; leave unknown placeholders intact."""
    class _D(dict):
        def __missing__(self, key):  # type: ignore[override]
            return "{" + key + "}"
    return template.format_map(_D(mapping))


class StudioBase:
    key: str = ""
    order: int = 0
    title: str = ""
    section: str = ""                # "코어 콘텐츠" / "SEO·유입" / "다이렉트 셀링" / "백오피스"
    channel_section: str | None = None
    output_filename: str = "output.md"
    description: str = ""
    max_tokens: int = 0              # 0 = use ctx default; override per-studio if longer needed
    html_renderer: str = "generic"   # key into core.html_render.RENDERERS

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
