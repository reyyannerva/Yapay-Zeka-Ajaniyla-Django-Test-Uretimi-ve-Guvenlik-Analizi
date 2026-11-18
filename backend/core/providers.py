"""AI model sağlayıcı yapılandırma erişimi — H4-06 / Issue #38.

Sağlayıcı yapılandırması ``settings.LLM_PROVIDERS``'tan okunur. Eksik anahtar veya erişilemeyen
yerel servis backend başlangıcını **engellemez**; sağlayıcı gerçekten kullanılacağı zaman
``require_llm_provider()`` anlaşılır, gizli bilgi sızdırmayan bir hata verir.
"""
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

_ENV_HINT = {"groq": "GROQ_API_KEY", "gemini": "GEMINI_API_KEY", "ollama": "OLLAMA_BASE_URL"}


def llm_provider_config(name: str) -> dict:
    providers = settings.LLM_PROVIDERS
    if name not in providers:
        raise ImproperlyConfigured(
            f"Bilinmeyen LLM sağlayıcısı: {name} (tanımlı: {', '.join(sorted(providers))})"
        )
    return providers[name]


def is_llm_provider_ready(name: str) -> bool:
    """Sağlayıcının zorunlu alanı (api_key ya da base_url) dolu mu? (Başlangıçta güvenli kontrol.)"""
    cfg = llm_provider_config(name)
    return bool(cfg.get(cfg.get("requires")))


def require_llm_provider(name: str) -> dict:
    """Sağlayıcı yapılandırmasını döndürür; zorunlu alan eksikse anlaşılır hata verir (değer sızdırmaz)."""
    cfg = llm_provider_config(name)
    if not cfg.get(cfg.get("requires")):
        hint = _ENV_HINT.get(name, cfg.get("requires"))
        raise ImproperlyConfigured(
            f"'{name}' sağlayıcısı yapılandırılmamış: {hint} tanımlı değil. "
            "Değeri backend/.env dosyasına ekleyin (gizli değer hiçbir çıktıya yazılmaz)."
        )
    return cfg
