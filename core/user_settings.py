"""GUI-managed settings persisted to data/user_settings.json.

Single provider: Ubion LiteLLM proxy with deepseek-v4-flash fixed.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

SETTINGS_PATH = Path(__file__).resolve().parent.parent / "data" / "user_settings.json"

DEFAULT_BASE_URL = "http://192.168.50.119:4000"
FIXED_MODEL = "deepseek-v4-flash"

# Image generation (Gemini Nano Banana via Ubion LiteLLM proxy)
IMAGE_MODEL = "gemini-3.1-flash-image-preview"
IMAGE_COST_USD = 0.04   # approximate per-image cost
USD_KRW = 1504.71       # 2026-05-27 exchange rate; update as needed


def krw(usd: float) -> int:
    """Convert USD → KRW (integer)."""
    return int(round(usd * USD_KRW))


@dataclass
class Settings:
    base_url: str = DEFAULT_BASE_URL
    api_key: str = ""
    model: str = FIXED_MODEL  # locked — no UI to change

    # Generation — 8192 to comfortably fit long-form Korean output
    max_tokens: int = 8192
    temperature: float = 0.7
    parallelism: int = 4

    # Shared variables across studios
    target_keyword: str = ""
    brand_name: str = ""

    extra: dict = field(default_factory=dict)


def _env_defaults() -> Settings:
    s = Settings()
    s.base_url = os.environ.get("UBION_LITELLM_URL", s.base_url)
    s.api_key = os.environ.get("UBION_LITELLM_KEY", s.api_key)
    return s


def load() -> Settings:
    base = _env_defaults()
    if not SETTINGS_PATH.exists():
        return base
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return base
    merged = asdict(base)
    merged.update({k: v for k, v in data.items() if k in merged})
    merged["model"] = FIXED_MODEL  # always force
    return Settings(**merged)


def save(settings: Settings) -> None:
    settings.model = FIXED_MODEL
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(asdict(settings), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
