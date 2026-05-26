"""LLM providers: LiteLLM proxy (remote, OpenAI-compatible) and Ollama (local)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from core.user_settings import Settings


class LLMProvider(Protocol):
    def generate(self, system: str, user: str, *, max_tokens: int = 4096, temperature: float = 0.7) -> str: ...
    def ping(self) -> tuple[bool, str]: ...
    @property
    def is_local(self) -> bool: ...


@dataclass
class LiteLLMProvider:
    base_url: str
    api_key: str
    model: str

    @property
    def is_local(self) -> bool:
        return False

    def generate(self, system: str, user: str, *, max_tokens: int = 4096, temperature: float = 0.7) -> str:
        import litellm  # lazy import — heavy module

        resp = litellm.completion(
            model=self.model,
            api_base=self.base_url or None,
            api_key=self.api_key or None,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp["choices"][0]["message"]["content"] or ""

    def ping(self) -> tuple[bool, str]:
        try:
            out = self.generate("You are a connection tester.", "Respond with only: OK", max_tokens=8, temperature=0)
            return True, out.strip()[:80]
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"


@dataclass
class OllamaProvider:
    host: str
    model: str

    @property
    def is_local(self) -> bool:
        return True

    def _client(self):
        import ollama
        return ollama.Client(host=self.host or "http://localhost:11434")

    def generate(self, system: str, user: str, *, max_tokens: int = 4096, temperature: float = 0.7) -> str:
        client = self._client()
        resp = client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            options={"temperature": temperature, "num_predict": max_tokens},
        )
        return resp["message"]["content"] or ""

    def ping(self) -> tuple[bool, str]:
        try:
            client = self._client()
            models = client.list()
            names = [m.get("name") or m.get("model") for m in models.get("models", [])]
            if self.model not in names:
                return False, f"model '{self.model}' not pulled. Available: {names[:5]}"
            return True, f"OK ({len(names)} models)"
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"


def build_provider(settings: Settings) -> LLMProvider:
    if settings.provider == "ollama":
        return OllamaProvider(host=settings.ollama_host, model=settings.ollama_model)
    return LiteLLMProvider(
        base_url=settings.litellm_base_url,
        api_key=settings.litellm_api_key,
        model=settings.litellm_model,
    )
