"""LLM provider abstraction.

The whole app treats the LLM as optional. Every caller has a deterministic
fallback, so the product runs end-to-end with no API key (demo mode).
Swap providers by implementing LLMProvider and changing get_provider().
"""
import json
import re
from abc import ABC, abstractmethod

import httpx

from .config import GROQ_API_KEY, GROQ_MODEL


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    def complete(self, system: str, user: str) -> str | None:
        """Return model text, or None if unavailable/failed."""

    def complete_json(self, system: str, user: str) -> dict | None:
        raw = self.complete(system + "\nRespond with a single JSON object only.", user)
        if not raw:
            return None
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


class GroqProvider(LLMProvider):
    """Groq's OpenAI-compatible chat completions API via plain HTTP."""

    name = "groq"

    def complete(self, system: str, user: str) -> str | None:
        try:
            resp = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1024,
                },
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception:
            return None  # callers fall back to deterministic logic


class MockProvider(LLMProvider):
    """No-key demo mode: always defers to the deterministic fallback."""

    name = "mock"

    def complete(self, system: str, user: str) -> str | None:
        return None


_provider: LLMProvider | None = None


def get_provider() -> LLMProvider:
    global _provider
    if _provider is None:
        _provider = GroqProvider() if GROQ_API_KEY else MockProvider()
    return _provider