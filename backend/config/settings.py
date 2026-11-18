"""Django ayarları — H4-01 / Issue #33.

Gizli değerler ve veritabanı bağlantısı ortam değişkenlerinden okunur (``backend/.env.example``).
Veritabanı yalnızca PostgreSQL'dir; şemadaki kısmi tekil indeks ve JSONB alanları PostgreSQL'e göre
tasarlanmıştır (docs/database/).
"""
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key

from .env import database_config, env_bool, env_int, env_list, env_str, load_dotenv_file

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv_file(BASE_DIR / ".env")

DEBUG = env_bool("DJANGO_DEBUG", False)
SECRET_KEY = env_str("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY tanımlı değil (DEBUG kapalıyken zorunludur)")
    SECRET_KEY = get_random_secret_key()  # yalnızca geliştirme: her süreçte yeni, kalıcı değil
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",  # H4-06 / Issue #38
    "axes",
    "drf_spectacular",  # H4-05 / Issue #37: OpenAPI 3 şeması
    "drf_spectacular_sidecar",  # Swagger UI/ReDoc dosyaları CDN yerine yerelden sunulur
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # CORS middleware olabildiğince üstte, CommonMiddleware'den önce olmalıdır (H4-06 / Issue #38).
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # django-axes en sonda olmalıdır (kilitli istekleri yanıtlar).
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {"default": database_config()}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Kullanıcı modeli: Django'nun yerleşik ``auth.User`` modeli (veri sözlüğü K1). İlişkiler
# ``settings.AUTH_USER_MODEL`` üzerinden kurulur; özel kullanıcı modeli kullanılmaz (docs/database/README.md).
AUTH_USER_MODEL = "auth.User"

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Giriş kilidi kalıcı verisi (İST-10; Issue #33): django-axes tabloları.
# Üç başarısız denemede kullanıcı adı bazında 15 dakika kilit. Deneme sayısı
# ``axes_accessattempt.failures_since_start``, kilit bitiş zamanı ``axes_accessattemptexpiration.expires_at``.
# DRF/SimpleJWT giriş uç noktalarına entegrasyon H4-02 (#34) kapsamındadır.
# Deneme sınırı ve kilit süresi H4-06 (#38) ile ortam değişkenlerinden yapılandırılabilir
# (varsayılanlar H4-02/#33 davranışını korur: 3 deneme / 15 dakika).
AXES_FAILURE_LIMIT = env_int("AXES_FAILURE_LIMIT", 3, minimum=1)
AXES_COOLOFF_TIME = timedelta(minutes=env_int("AXES_COOLOFF_MINUTES", 15, minimum=1))
AXES_LOCKOUT_PARAMETERS = ["username"]
AXES_RESET_ON_SUCCESS = True
AXES_USE_ATTEMPT_EXPIRATION = True
AXES_ENABLE_ACCESS_FAILURE_LOG = True
# axes.W006 (IP parametresi yok) bilinçli olarak susturulur: gereksinim hesap (kullanıcı adı) bazında
# kilittir; IP bazlı istek sınırlaması H4-02 (#34) "temel istek sınırlaması" kapsamındadır.
SILENCED_SYSTEM_CHECKS = ["axes.W006"]

LANGUAGE_CODE = "tr"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "media/"

# --- Proje arşivi yükleme (H4-03 / Issue #35) ---
# Arşivler herkese açık olmayan ayrı bir kökte saklanır (core.storage.ProjectArchiveStorage); URL ile sunulmaz.
PROJECT_ARCHIVE_ROOT = Path(env_str("PROJECT_ARCHIVE_ROOT", str(BASE_DIR / "private_storage")))
# Sınırlar proje kararıdır (isterlerde sayısal değer tanımlı değildir); ortamdan değiştirilebilir.
PROJECT_UPLOAD_LIMITS = {
    "max_upload_bytes": env_int("PROJECT_UPLOAD_MAX_BYTES", 50 * 1024 * 1024, minimum=1),
    "max_total_uncompressed_bytes": env_int("PROJECT_UPLOAD_MAX_UNCOMPRESSED_BYTES", 200 * 1024 * 1024, minimum=1),
    "max_member_bytes": env_int("PROJECT_UPLOAD_MAX_MEMBER_BYTES", 20 * 1024 * 1024, minimum=1),
    "max_entries": env_int("PROJECT_UPLOAD_MAX_ENTRIES", 10_000, minimum=1),
    "max_depth": env_int("PROJECT_UPLOAD_MAX_DEPTH", 32, minimum=1),
    "max_path_length": env_int("PROJECT_UPLOAD_MAX_PATH_LENGTH", 240, minimum=16),
    "max_compression_ratio": env_int("PROJECT_UPLOAD_MAX_COMPRESSION_RATIO", 100, minimum=2),
    # Oran denetimi bu boyutun altındaki küçük girdilere uygulanmaz (yanlış pozitifleri önler).
    "ratio_check_min_bytes": env_int("PROJECT_UPLOAD_RATIO_MIN_BYTES", 1024 * 1024, minimum=0),
}
# Desteklenen arşiv biçimleri (yalnızca ZIP); uzantı tek başına yeterli değildir, içerik de doğrulanır.
PROJECT_UPLOAD_ALLOWED_EXTENSIONS = [".zip"]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",  # H4-05 / Issue #37
}

# --- Kimlik doğrulama / yetkilendirme (H4-02 / Issue #34) ---
# SimpleJWT token süreleri ve blacklist. Süreler ortamdan okunur (H4-06 #38 ile genişletilir).
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env_int("JWT_ACCESS_MINUTES", 15, minimum=1)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env_int("JWT_REFRESH_DAYS", 7, minimum=1)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,  # başarılı girişte last_login + axes sayaç sıfırlama sinyali
}

# E-posta (şifre sıfırlama). Testte ve varsayılan geliştirmede konsol/locmem; üretimde SMTP (#38).
EMAIL_BACKEND = env_str("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env_str("DEFAULT_FROM_EMAIL", "noreply@localhost")
# Şifre sıfırlama bağlantısının yönlendirileceği frontend adresi (uid/token eklenir).
FRONTEND_PASSWORD_RESET_URL = env_str(
    "FRONTEND_PASSWORD_RESET_URL", "http://localhost:5173/reset-password"
)
# Sıfırlama token geçerlilik süresi (saniye); Django PASSWORD_RESET_TIMEOUT.
PASSWORD_RESET_TIMEOUT = env_int("PASSWORD_RESET_TIMEOUT", 3600, minimum=60)

# Giriş denemelerine temel istek sınırlaması (İST-10): anonim login çağrıları için.
REST_FRAMEWORK.setdefault("DEFAULT_THROTTLE_CLASSES", [])
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "login": env_str("LOGIN_THROTTLE_RATE", "10/min"),
    # H4-03: kullanıcı başına arşiv yükleme sınırı (kaynak tüketimine karşı).
    "project_upload": env_str("PROJECT_UPLOAD_THROTTLE_RATE", "30/hour"),
}

# =====================================================================
# Ortam yapılandırması ve backend güvenlik kontrolleri (H4-06 / Issue #38)
# =====================================================================

# --- CORS / CSRF (frontend erişimi) ---
# İzin verilen frontend adresleri ortamdan yapılandırılır (yıldız izin kullanılmaz).
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", ["http://localhost:5173", "http://127.0.0.1:5173"])
CORS_ALLOW_CREDENTIALS = env_bool("CORS_ALLOW_CREDENTIALS", True)
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", CORS_ALLOWED_ORIGINS)

# --- E-posta / SMTP (şifre sıfırlama) ---
# EMAIL_BACKEND SMTP değilse (varsayılan konsol) aşağıdaki değerler kullanılmaz; gizli bilgi .env'dedir.
EMAIL_HOST = env_str("EMAIL_HOST", "localhost")
EMAIL_PORT = env_int("EMAIL_PORT", 587, minimum=1, maximum=65535)
EMAIL_HOST_USER = env_str("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env_str("EMAIL_HOST_PASSWORD", "")  # yalnızca ortamdan; repoya yazılmaz
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 10, minimum=1)

# --- Redis / Celery (ileride asenkron yürütme; şimdilik yalnızca yapılandırma) ---
CELERY_BROKER_URL = env_str("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = env_str("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)

# --- AI model sağlayıcıları (İST-05, İST-11) ---
# Anahtarlar/servis adresleri ortamdan okunur. Eksik anahtar veya erişilemeyen yerel servis
# backend başlangıcını ENGELLEMEZ; sağlayıcı gerçekten kullanıldığında anlaşılır hata döndürülür
# (bkz. core.providers.require_llm_provider). Gizli anahtarlar hiçbir çıktıya yazılmaz.
LLM_DEFAULT_PROVIDER = env_str("LLM_DEFAULT_PROVIDER", "groq")
LLM_REQUEST_TIMEOUT = env_int("LLM_REQUEST_TIMEOUT", 60, minimum=1)
LLM_PROVIDERS = {
    "groq": {
        "requires": "api_key",
        "api_key": env_str("GROQ_API_KEY", ""),
        "model": env_str("GROQ_MODEL", "llama-3.3-70b-versatile"),
    },
    "gemini": {
        "requires": "api_key",
        "api_key": env_str("GEMINI_API_KEY", ""),
        "model": env_str("GEMINI_MODEL", "gemini-1.5-flash"),
    },
    "ollama": {
        # Yerel servis; API anahtarı gerektirmez.
        "requires": "base_url",
        "base_url": env_str("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        "model": env_str("OLLAMA_MODEL", "llama3"),
    },
}
# LiteLLM sağlayıcı soyutlaması (opsiyonel ayarlar).
LITELLM_SETTINGS = {
    "default_provider": LLM_DEFAULT_PROVIDER,
    "request_timeout": LLM_REQUEST_TIMEOUT,
}

# --- Üretim güvenlik sertleştirmesi (DEBUG kapalıyken; check --deploy uyarıları) ---
SECURE_CONTENT_TYPE_NOSNIFF = True
if not DEBUG:
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", True)
    CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", True)
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 31_536_000, minimum=0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", True)
    # Ters vekil sunucu arkasında HTTPS'i doğru algılamak için (yalnızca güvenilen proxy ile).
    if env_bool("SECURE_PROXY_SSL_HEADER", True):
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- API dokümantasyonu (H4-05 / Issue #37) ---
# Şema ve Swagger UI erişimi: API_DOCS_PUBLIC=true iken herkese açık (geliştirme varsayılanı = DEBUG);
# false iken yalnızca personel (is_staff) kullanıcılar (yönetici oturumu veya JWT) erişebilir.
API_DOCS_PUBLIC = env_bool("API_DOCS_PUBLIC", DEBUG)
SPECTACULAR_SETTINGS = {
    "TITLE": "Yapay Zekâ Ajanıyla Django Test Üretimi ve Güvenlik Analizi API",
    "DESCRIPTION": (
        "Hafta 4 backend API'si: SimpleJWT kimlik doğrulama, hesap kilidi ve şifre sıfırlama (H4-02), "
        "proje yönetimi ve güvenli ZIP yükleme (H4-03), analiz çalıştırmaları ve referans gereksinimler "
        "(H4-04). Korumalı uç noktalar `Authorization: Bearer <access token>` ister. Ayrıntılı kılavuz: "
        "docs/api/README.md."
    ),
    "VERSION": "0.4.0",
    "OAS_VERSION": "3.0.3",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PERMISSIONS": ["core.api.docs.ApiDocsPermission"],
    "SERVE_AUTHENTICATION": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    # İstek ve yanıt bileşenleri ayrılır: salt okunur alanlar istek şemasında, write_only alanlar yanıtta görünmez;
    # dosya alanları istek şemasında ikili (binary) olarak gösterilir.
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/",
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "SWAGGER_UI_SETTINGS": {"persistAuthorization": False, "displayOperationId": False, "filter": True},
    "TAGS": [
        {"name": "Kimlik Doğrulama", "description": "SimpleJWT giriş, token yenileme, çıkış ve oturum bilgisi."},
        {"name": "Parola İşlemleri", "description": "E-posta ile şifre sıfırlama talebi ve yeni parola belirleme."},
        {"name": "Proje Yükleme", "description": "multipart/form-data ile ZIP arşivi yükleyerek proje oluşturma."},
        {"name": "Proje Yönetimi", "description": "Kullanıcının projelerini listeleme, görüntüleme, güncelleme, silme."},
        {"name": "Analiz İşlemleri", "description": "Analiz çalıştırması oluşturma (QUEUED), listeleme ve detay."},
        {"name": "Referans Gereksinimler", "description": "Bağımsız referans gereksinim JSON'u (ROLE, ACCESS_RULE, "
                                                         "DEPLOY_EXPECTATION) CRUD."},
    ],
    "ENUM_NAME_OVERRIDES": {
        "AnalysisRunStatusEnum": "core.models.analysis.AnalysisRunStatus",
        "AnalysisMethodEnum": "core.models.analysis.AnalysisMethod",
        "LlmProviderEnum": "core.models.analysis.LlmProvider",
        "ProjectSourceTypeEnum": "core.models.project.ProjectSourceType",
        "ProjectValidationStatusEnum": "core.models.project.ProjectValidationStatus",
        "RequirementCategoryEnum": "core.models.requirement.RequirementCategory",
        "RequirementSourceEnum": "core.models.requirement.RequirementSource",
        "HttpMethodEnum": "core.choices.HttpMethod",
        "ArchiveErrorCodeEnum": "core.api.schema.ARCHIVE_ERROR_CODES",
        "ArchiveEntryReasonEnum": "core.api.schema.ARCHIVE_ENTRY_REASONS",
    },
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
    ],
}
