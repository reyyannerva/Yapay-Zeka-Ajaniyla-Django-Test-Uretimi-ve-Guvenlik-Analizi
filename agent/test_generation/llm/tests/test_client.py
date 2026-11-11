import os

import pytest

from agent.test_generation.llm.client import GroqClient, LLMError, _sanitize, load_env


def test_load_env(tmp_path, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    env = tmp_path / ".env"
    env.write_text('GROQ_API_KEY="gsk_test123"\n# yorum\nLLM_MODEL=groq/x\n', encoding="utf-8")
    load_env(env)
    assert os.environ["GROQ_API_KEY"] == "gsk_test123"
    assert os.environ["LLM_MODEL"] == "groq/x"


def test_load_env_does_not_override(monkeypatch, tmp_path):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_existing")
    env = tmp_path / ".env"
    env.write_text("GROQ_API_KEY=gsk_other\n", encoding="utf-8")
    load_env(env)
    assert os.environ["GROQ_API_KEY"] == "gsk_existing"


def test_require_key_raises(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(LLMError) as ei:
        GroqClient(model="groq/x").require_key()
    assert ei.value.kind == "auth"


def test_sanitize_strips_key():
    assert "gsk_" in _sanitize("hata: gsk_abc123 geçersiz") and "abc123" not in _sanitize("gsk_abc123")


def test_classify_quota():
    err = GroqClient._classify(type("RateLimitError", (Exception,), {})("429 too many"))
    assert err.kind == "quota"


def test_classify_timeout():
    err = GroqClient._classify(type("Timeout", (Exception,), {})("timed out"))
    assert err.kind == "timeout"
