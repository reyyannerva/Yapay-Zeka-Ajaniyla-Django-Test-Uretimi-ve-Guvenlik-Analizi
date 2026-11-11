"""LiteLLM üzerinden Groq istemcisi — H3-05 / Issue #31.

API anahtarı ortam değişkeninden/.env'den okunur; koda/log/repoya ASLA yazılmaz. Hata türleri
(auth/quota/timeout/connection/other) sınıflandırılır; mesajlardan olası anahtar sızıntısı temizlenir.
"""
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

_KEY_PATTERN = re.compile(r"gsk_[A-Za-z0-9]+")


def load_env(env_path: str | Path) -> None:
    """Basit .env yükleyici: dosyadaki değişkenleri (zaten tanımlı değilse) ortama ekler."""
    p = Path(env_path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _sanitize(msg: str) -> str:
    return _KEY_PATTERN.sub("gsk_***", msg or "")


class LLMError(Exception):
    def __init__(self, kind: str, message: str):
        super().__init__(f"[{kind}] {message}")
        self.kind = kind
        self.message = message


@dataclass
class LLMResponse:
    text: str
    prompt_tokens: int | None
    completion_tokens: int | None
    latency_ms: int


class GroqClient:
    """LiteLLM `completion` sarmalayıcısı (model adı config'li)."""

    def __init__(self, model: str, temperature: float = 0.0, max_tokens: int = 1200,
                 timeout: int = 60, api_key_env: str = "GROQ_API_KEY"):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.api_key_env = api_key_env

    def require_key(self) -> None:
        if not os.environ.get(self.api_key_env):
            raise LLMError("auth", f"{self.api_key_env} tanımlı değil (.env veya ortam değişkeni).")

    def complete(self, system: str, user: str) -> LLMResponse:
        self.require_key()
        try:
            import litellm
        except ImportError as exc:  # pragma: no cover
            raise LLMError("other", "litellm kurulu değil (pip install litellm).") from exc

        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        start = time.perf_counter()
        try:
            resp = litellm.completion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
                api_key=os.environ[self.api_key_env],
            )
        except Exception as exc:  # LiteLLM çeşitli istisna türleri atar
            raise self._classify(exc) from None
        latency_ms = int((time.perf_counter() - start) * 1000)

        text = ""
        try:
            text = resp["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            text = getattr(getattr(resp.choices[0], "message", None), "content", "") or ""
        usage = resp.get("usage") if isinstance(resp, dict) else getattr(resp, "usage", None)
        pt = _usage_get(usage, "prompt_tokens")
        ct = _usage_get(usage, "completion_tokens")
        return LLMResponse(text=text, prompt_tokens=pt, completion_tokens=ct, latency_ms=latency_ms)

    @staticmethod
    def _classify(exc: Exception) -> LLMError:
        name = type(exc).__name__.lower()
        msg = _sanitize(str(exc))
        if "authentication" in name or "permission" in name or "401" in msg or "403" in msg:
            return LLMError("auth", msg)
        if "ratelimit" in name or "quota" in name or "429" in msg:
            return LLMError("quota", msg)
        if "timeout" in name:
            return LLMError("timeout", msg)
        if "connection" in name or "apiconnection" in name:
            return LLMError("connection", msg)
        return LLMError("other", f"{type(exc).__name__}: {msg}")


def _usage_get(usage, key):
    if usage is None:
        return None
    if isinstance(usage, dict):
        return usage.get(key)
    return getattr(usage, key, None)
