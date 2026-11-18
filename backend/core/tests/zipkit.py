"""Testler için bellekte ZIP arşivi üretme yardımcıları — H4-03 / Issue #35.

Saldırı arşivleri (yol geçişi, sembolik bağlantı, özel dosya, ZIP bombası) yalnızca bellekte üretilir;
hiçbiri diske açılmaz. ZipInfo.filename doğrudan atanır, böylece Windows'ta ZipInfo'nun yol
normalleştirmesi saldırı adlarını değiştirmez.
"""
from __future__ import annotations

import io
import stat
import warnings
import zipfile

SETTINGS = '''SECRET_KEY = "test-only"
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "shop",
]
ROOT_URLCONF = "config.urls"
'''

MANAGE = '''#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
'''


def django_files(prefix: str = "", drf: bool = True) -> dict[str, str]:
    settings = SETTINGS if drf else SETTINGS.replace('    "rest_framework",\n', "")
    p = f"{prefix}/" if prefix else ""
    return {
        f"{p}manage.py": MANAGE,
        f"{p}config/__init__.py": "",
        f"{p}config/settings.py": settings,
        f"{p}config/urls.py": "urlpatterns = []\n",
        f"{p}config/wsgi.py": "application = None\n",
        f"{p}shop/__init__.py": "",
        f"{p}shop/apps.py": "from django.apps import AppConfig\n\nclass ShopConfig(AppConfig):\n    name = 'shop'\n",
        f"{p}shop/models.py": "",
        f"{p}requirements.txt": "Django>=5.1\n" + ("djangorestframework>=3.15\n" if drf else ""),
    }


def build_zip(files: dict[str, str | bytes] | None = None, *, raw: list[tuple] | None = None,
              compression: int = zipfile.ZIP_DEFLATED) -> bytes:
    """``files``: yol → içerik. ``raw``: (ad, içerik, unix_mod veya None) — adlar olduğu gibi yazılır."""
    buf = io.BytesIO()
    # Yinelenen girdi içeren saldırı arşivleri bilerek üretilir; zipfile'ın "Duplicate name" uyarısı beklenir.
    with warnings.catch_warnings(), zipfile.ZipFile(buf, "w", compression) as zf:
        warnings.filterwarnings("ignore", message="Duplicate name", category=UserWarning)
        for name, content in (files or {}).items():
            zf.writestr(name, content)
        for name, content, mode in raw or []:
            info = zipfile.ZipInfo("placeholder")
            info.filename = name
            info.compress_type = compression
            if mode is not None:
                info.create_system = 3
                info.external_attr = (mode & 0xFFFF) << 16
            zf.writestr(info, content)
    return buf.getvalue()


def valid_django_zip(prefix: str = "", drf: bool = True, extra: dict | None = None) -> bytes:
    return build_zip({**django_files(prefix, drf), **(extra or {})})


SYMLINK = stat.S_IFLNK | 0o777
FIFO = stat.S_IFIFO | 0o644
CHAR_DEVICE = stat.S_IFCHR | 0o644
REGULAR = stat.S_IFREG | 0o644
