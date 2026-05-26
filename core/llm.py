"""LLM provider — Ubion LiteLLM proxy via OpenAI SDK (deepseek-v4-flash fixed)."""
from __future__ import annotations

from dataclasses import dataclass

from core.user_settings import FIXED_MODEL, Settings


@dataclass
class UbionLiteLLMProvider:
    base_url: str
    api_key: str
    model: str = FIXED_MODEL

    @property
    def is_local(self) -> bool:
        return False

    def _client(self):
        from openai import OpenAI  # lazy import
        url = (self.base_url or "").rstrip("/")
        return OpenAI(api_key=self.api_key, base_url=f"{url}/v1")

    def generate(self, system: str, user: str, *, max_tokens: int = 4096, temperature: float = 0.7) -> str:
        resp = self._client().chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""

    def ping(self) -> tuple[bool, str]:
        try:
            text = self.generate(
                "You are a connection tester.", "Respond with exactly: OK",
                max_tokens=8, temperature=0,
            )
            return True, f"OK ({self.model}) → {text.strip()[:40]}"
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"


def build_provider(settings: Settings) -> UbionLiteLLMProvider:
    return UbionLiteLLMProvider(
        base_url=settings.base_url,
        api_key=settings.api_key,
        model=FIXED_MODEL,
    )
