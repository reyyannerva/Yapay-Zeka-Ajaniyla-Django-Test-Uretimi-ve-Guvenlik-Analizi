"""Ortam değişkeni okuma yardımcıları — H4-01 / Issue #33.

Değerler önce işletim sistemi ortamından, yoksa ``backend/.env`` dosyasından (python-dotenv ile) okunur.
Eksik zorunlu değişkenler ``ImproperlyConfigured`` ile değişkenin **adı** belirtilerek bildirilir; değer
hiçbir hata iletisine yazılmaz.
"""
from __future__ import annotations

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

_TRUE = {"1", "true", "yes", "on", "evet"}
_FALSE = {"0", "false", "no", "off", "hayir", "hayır", ""}
_UNSET = object()


def load_dotenv_file(path: Path) -> None:
    """``.env`` dosyası varsa yükler; mevcut ortam değişkenlerinin üzerine yazmaz."""
    try:
        from dotenv import load_dotenv
    except ImportError:  # python-dotenv kurulu değilse yalnızca ortam kullanılır
        return
    if path.is_file():
        load_dotenv(path, override=False)


def env_str(name: str, default=_UNSET) -> str:
    value = os.environ.get(name)
    if value is None or value == "":
        if default is _UNSET:
            raise ImproperlyConfigured(f"Zorunlu ortam değişkeni tanımlı değil: {name} (bkz. backend/.env.example)")
        return default
    return value


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in _TRUE:
        return True
    if value in _FALSE:
        return False
    raise ImproperlyConfigured(f"{name} mantıksal bir değer olmalı (true/false)")


def env_int(name: str, default: int | None = None, *, minimum: int | None = None, maximum: int | None = None) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        if default is None:
            raise ImproperlyConfigured(f"Zorunlu ortam değişkeni tanımlı değil: {name}")
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ImproperlyConfigured(f"{name} bir tam sayı olmalı") from None
    if (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        raise ImproperlyConfigured(f"{name} {minimum}–{maximum} aralığında olmalı")
    return value


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    raw = os.environ.get(name)
    if raw is None:
        return list(default or [])
    return [item.strip() for item in raw.split(",") if item.strip()]


def database_config() -> dict:
    """PostgreSQL bağlantı ayarları. Tüm bağlantı değerleri ortamdan gelir; varsayılan parola yoktur."""
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env_str("POSTGRES_DB"),
        "USER": env_str("POSTGRES_USER"),
        "PASSWORD": env_str("POSTGRES_PASSWORD"),
        "HOST": env_str("POSTGRES_HOST", "127.0.0.1"),
        "PORT": str(env_int("POSTGRES_PORT", 5432, minimum=1, maximum=65535)),
        "CONN_MAX_AGE": env_int("POSTGRES_CONN_MAX_AGE", 0, minimum=0),
        "OPTIONS": {"connect_timeout": env_int("POSTGRES_CONNECT_TIMEOUT", 5, minimum=1, maximum=120)},
        "TEST": {"NAME": os.environ.get("POSTGRES_TEST_DB") or None},
    }
