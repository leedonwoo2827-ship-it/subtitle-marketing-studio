"""GUI-managed settings persisted to data/user_settings.json."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

SETTINGS_PATH = Path(__file__).resolve().parent.parent / "data" / "user_settings.json"


@dataclass
class Settings:
    provider: str = "litellm"  # "litellm" | "ollama"

    # LiteLLM proxy
    litellm_base_url: str = ""
    litellm_api_key: str = ""
    litellm_model: str = "deepseek/deepseek-chat"

    # Ollama local
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Generation
    max_tokens: int = 4096
    temperature: float = 0.7
    parallelism: int = 4  # remote default; local forced to 1 in runner

    # Extras shared across studios
    target_keyword: str = ""
    brand_name: str = ""

    extra: dict = field(default_factory=dict)


def _env_defaults() -> Settings:
    s = Settings()
    s.litellm_base_url = os.environ.get("LITELLM_BASE_URL", s.litellm_base_url)
    s.litellm_api_key = os.environ.get("LITELLM_API_KEY", s.litellm_api_key)
    s.litellm_model = os.environ.get("LITELLM_MODEL", s.litellm_model)
    s.ollama_host = os.environ.get("OLLAMA_HOST", s.ollama_host)
    s.ollama_model = os.environ.get("OLLAMA_MODEL", s.ollama_model)
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
    return Settings(**merged)


def save(settings: Settings) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(asdict(settings), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
