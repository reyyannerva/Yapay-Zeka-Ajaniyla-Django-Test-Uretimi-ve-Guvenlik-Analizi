"""Katman B kontrollü hedef uygulaması ayarları — H5-05 / Issue #43.

Bu uygulama, H5-05 kontrollü ek geliştirme deneyinin HEDEF uygulamasıdır (H3-01 sample_app ile aynı
yaklaşım): projenin ürün backend'i değildir, SQLite kullanır ve yalnızca Django test istemcisiyle,
geçici test veritabanında çalıştırılır. Bilerek güvensiz uçlar ``tasks/legacy.py`` içinde ayrı ve
işaretli tutulur. Mühürlü H3-03 test kümesindeki senaryo/kaynaklardan (``catalog.Article``) türetilmemiştir.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-h5-05-controlled-target")
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "rest_framework",
    "tasks",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = []
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
REST_FRAMEWORK = {
    # Anonim isteklerin korunan uçlarda 403 yerine net 401 alması için WWW-Authenticate döndüren Basic.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "UNAUTHENTICATED_USER": "django.contrib.auth.models.AnonymousUser",
}
