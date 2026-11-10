"""
Kontrollü DRF hedef uygulaması ayarları — H3-01 / Issue #27.

Bu uygulama, AI test ajanının üzerinde test üreteceği KONTROLLÜ bir HEDEF uygulamadır;
projenin kendi ürün backend'i (Hafta 4) değildir. SQLite kullanır ki tek komutla
çalıştırılabilsin. Bilerek eklenen güvenlik hataları `catalog/insecure.py` içinde ayrı
ve işaretli tutulur.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Dev amaçlı anahtar; gerçek bir sır değildir ve ortam değişkeninden override edilebilir.
# Bu uygulama yalnızca yerel/izole test hedefidir.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-h3-01-controlled-target")

# Kontrollü hedef uygulama; yerel çalıştırma için True. (Üründe False olmalıdır.)
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "rest_framework",
    "catalog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    # Anonim isteklerin korunan uçlarda net 401 alması için header döndüren
    # Basic + Session kimlik doğrulama kullanılır.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    # İzinler view bazında açıkça tanımlanır (varsayılan: açık uç).
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}
