"""Django ayarları — H4-01 / Issue #33.

Gizli değerler ve veritabanı bağlantısı ortam değişkenlerinden okunur (``backend/.env.example``).
Veritabanı yalnızca PostgreSQL'dir; şemadaki kısmi tekil indeks ve JSONB alanları PostgreSQL'e göre
tasarlanmıştır (docs/database/).
"""
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key

from .env import database_config, env_bool, env_list, env_str, load_dotenv_file

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
    "axes",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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
AXES_FAILURE_LIMIT = 3
AXES_COOLOFF_TIME = timedelta(minutes=15)
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

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}
