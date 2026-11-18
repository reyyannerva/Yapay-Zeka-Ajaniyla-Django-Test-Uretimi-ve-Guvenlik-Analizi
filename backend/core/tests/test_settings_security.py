"""Ortam yapılandırması ve backend güvenlik ayarları testleri — H4-06 / Issue #38.

Kapsam: CORS/CSRF ayarları, SMTP değişkenlerinin ortamdan okunması, giriş kilidi parametrelerinin
yapılandırılabilirliği, AI sağlayıcı anahtarının opsiyonelliği (eksik anahtar başlangıcı bozmaz ama
kullanımda anlaşılır hata verir) ve gizli değerin hata mesajına sızmaması.
"""
import importlib

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from core import providers


# --- CORS / CSRF ---
def test_corsheaders_installed_and_middleware_ordered():
    assert "corsheaders" in settings.INSTALLED_APPS
    mw = settings.MIDDLEWARE
    cors = mw.index("corsheaders.middleware.CorsMiddleware")
    security = mw.index("django.middleware.security.SecurityMiddleware")
    common = mw.index("django.middleware.common.CommonMiddleware")
    # CORS middleware SecurityMiddleware'den sonra, CommonMiddleware'den önce olmalı.
    assert security < cors < common


def test_cors_origins_configured_without_wildcard():
    assert isinstance(settings.CORS_ALLOWED_ORIGINS, list)
    assert settings.CORS_ALLOWED_ORIGINS  # boş değil
    assert "*" not in settings.CORS_ALLOWED_ORIGINS
    # CSRF güvenilen origin'ler de tanımlı.
    assert settings.CSRF_TRUSTED_ORIGINS


# --- SMTP / e-posta ---
def test_smtp_settings_present():
    for name in ("EMAIL_HOST", "EMAIL_PORT", "EMAIL_HOST_USER", "EMAIL_HOST_PASSWORD",
                 "EMAIL_USE_TLS", "EMAIL_TIMEOUT"):
        assert hasattr(settings, name)
    assert isinstance(settings.EMAIL_PORT, int)


# --- Giriş kilidi parametreleri (yapılandırılabilir) ---
def test_lockout_parameters_are_typed():
    assert isinstance(settings.AXES_FAILURE_LIMIT, int) and settings.AXES_FAILURE_LIMIT >= 1
    # AXES_COOLOFF_TIME bir timedelta'dır (dakikadan türetilir).
    assert settings.AXES_COOLOFF_TIME.total_seconds() >= 60


def test_lockout_env_configurable(monkeypatch):
    """AXES_FAILURE_LIMIT/COOLOFF ortam değişkeninden okunur (settings yeniden içe aktarılarak doğrulanır)."""
    monkeypatch.setenv("AXES_FAILURE_LIMIT", "5")
    monkeypatch.setenv("AXES_COOLOFF_MINUTES", "30")
    import config.settings as s
    reloaded = importlib.reload(s)
    try:
        assert reloaded.AXES_FAILURE_LIMIT == 5
        assert reloaded.AXES_COOLOFF_TIME.total_seconds() == 30 * 60
    finally:
        importlib.reload(s)  # genel ayarları geri yükle


# --- AI sağlayıcıları: opsiyonel anahtar, kullanımda anlaşılır hata ---
def test_llm_providers_structure():
    for name in ("groq", "gemini", "ollama"):
        cfg = settings.LLM_PROVIDERS[name]
        assert "requires" in cfg and cfg["requires"] in cfg


_SECRET = "sk-super-gizli-anahtar-12345"


@override_settings(LLM_PROVIDERS={"groq": {"requires": "api_key", "api_key": "", "model": "m"}})
def test_require_provider_raises_when_key_missing():
    with pytest.raises(ImproperlyConfigured) as exc:
        providers.require_llm_provider("groq")
    assert "GROQ_API_KEY" in str(exc.value)  # eksik değişkenin adını söyler
    assert not providers.is_llm_provider_ready("groq")


@override_settings(LLM_PROVIDERS={"groq": {"requires": "api_key", "api_key": _SECRET, "model": "m"}})
def test_require_provider_returns_config_when_set():
    cfg = providers.require_llm_provider("groq")
    assert cfg["api_key"] == _SECRET
    assert providers.is_llm_provider_ready("groq")


@override_settings(LLM_PROVIDERS={"groq": {"requires": "api_key", "api_key": "", "model": "m"}})
def test_error_message_does_not_leak_secret_value():
    """Hata mesajı yalnızca değişken adını içerir; sağlayıcı anahtarının değerini sızdırmaz."""
    other = {"requires": "api_key", "api_key": _SECRET, "model": "m"}
    with override_settings(LLM_PROVIDERS={"groq": {"requires": "api_key", "api_key": "", "model": "m"},
                                          "gemini": other}):
        with pytest.raises(ImproperlyConfigured) as exc:
            providers.require_llm_provider("groq")
        assert _SECRET not in str(exc.value)


def test_unknown_provider_raises():
    with pytest.raises(ImproperlyConfigured, match="Bilinmeyen"):
        providers.require_llm_provider("yok-boyle-saglayici")


# --- Üretim güvenlik sertleştirmesi ---
def test_content_type_nosniff_always_on():
    assert settings.SECURE_CONTENT_TYPE_NOSNIFF is True
