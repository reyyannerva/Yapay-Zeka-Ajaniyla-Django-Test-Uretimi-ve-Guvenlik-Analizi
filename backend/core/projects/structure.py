"""Arşivdeki Django/DRF proje yapısının statik ön kontrolü — H4-03 / Issue #35.

Kaynak kod **çalıştırılmaz ve içe aktarılmaz**; yalnızca sınırlı boyuttaki metin dosyaları okunur ve
``ast.parse`` ile ayrıştırılır (ayrıştırma kod çalıştırmaz). Bu kontrol yalnızca bir uygunluk ön
kontrolüdür; projenin çalışabilir veya güvenli olduğunu kanıtlamaz.

Kabul kuralı (belgelenmiş, açık):

1. En az bir Django ayar modülü bulunmalı: ``settings.py`` veya ``settings/`` paketindeki bir modül ve
   içinde ``INSTALLED_APPS`` tanımı (Django'ya özgü güçlü işaret).
2. Ayrıca en az bir Django giriş noktası bulunmalı: ``manage.py``, ``wsgi.py``, ``asgi.py`` veya ``urls.py``.

Proje kök dizini ve uygulama adları serbesttir; iç içe dizin yapıları desteklenir. DRF zorunlu değildir;
bulunmazsa uyarı verilir (``rest_framework`` INSTALLED_APPS'te veya bağımlılık dosyasında aranır).
"""
from __future__ import annotations

import ast
import re

from .archive import ArchiveRejected

_SETTINGS_ENV_RX = re.compile(
    r"""DJANGO_SETTINGS_MODULE["']\s*,\s*["']([A-Za-z_][\w.]*)["']""")
_DEPENDENCY_FILES = ("requirements.txt", "requirements-dev.txt", "requirements/base.txt", "pyproject.toml",
                     "Pipfile", "setup.cfg", "setup.py")
_ENTRYPOINTS = ("manage.py", "wsgi.py", "asgi.py", "urls.py")


def _basename(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def _parent(path: str) -> str:
    return path.rsplit("/", 1)[0] if "/" in path else ""


def is_settings_module(path: str) -> bool:
    return _basename(path) == "settings.py" or ("/settings/" in f"/{path}" and path.endswith(".py"))


def wants_text(path: str) -> bool:
    """Yapı taraması için içeriği okunacak dosyalar (yalnızca küçük metin dosyaları)."""
    name = _basename(path)
    return (name == "manage.py" or is_settings_module(path)
            or any(path == d or path.endswith("/" + d) for d in _DEPENDENCY_FILES))


def installed_apps(source: str) -> list[str] | None:
    """``INSTALLED_APPS`` içindeki sabit dizgeleri döndürür; tanım yoksa ``None``. Kod çalıştırılmaz."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return [] if re.search(r"^\s*INSTALLED_APPS\s*[+]?=", source, re.M) else None
    found = None
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            targets, value = [node.target], node.value
        for t in targets:
            if isinstance(t, ast.Name) and t.id == "INSTALLED_APPS":
                found = found or []
                if isinstance(value, (ast.List, ast.Tuple)):
                    found.extend(e.value for e in value.elts
                                 if isinstance(e, ast.Constant) and isinstance(e.value, str))
    return found


def analyze(files: list[str], texts: dict[str, str]) -> dict:
    """Django işaretlerini toplar; geçerli yapı yoksa ``ArchiveRejected`` yükseltir."""
    settings_found: dict[str, list[str]] = {}
    for path in sorted(p for p in files if is_settings_module(p)):
        apps = installed_apps(texts.get(path, ""))
        if apps is not None:
            settings_found[path] = apps
    manage = sorted(p for p in files if _basename(p) == "manage.py")
    entrypoints = sorted(p for p in files if _basename(p) in _ENTRYPOINTS)
    declared_settings = sorted({m.group(1) for p in manage for m in _SETTINGS_ENV_RX.finditer(texts.get(p, ""))})

    if not settings_found:
        raise ArchiveRejected(
            "NO_DJANGO_SETTINGS",
            "Arşivde Django ayar modülü bulunamadı: INSTALLED_APPS içeren bir settings.py veya settings/ "
            "paketi gereklidir.")
    if not entrypoints:
        raise ArchiveRejected(
            "NO_DJANGO_ENTRYPOINT",
            "Arşivde Django giriş noktası bulunamadı: manage.py, wsgi.py, asgi.py veya urls.py gereklidir.")

    all_apps = sorted({a for apps in settings_found.values() for a in apps})
    dependency_text = " ".join(v for p, v in texts.items() if not p.endswith(".py") or _basename(p) == "setup.py")
    drf = "rest_framework" in all_apps or bool(re.search(r"djangorestframework", dependency_text, re.I))
    project_apps = sorted({_parent(p) for p in files if _basename(p) == "apps.py" and _parent(p)})
    warnings = []
    if not manage:
        warnings.append("manage.py bulunamadı")
    if len(manage) > 1:
        warnings.append(f"birden fazla manage.py bulundu ({len(manage)})")
    if not drf:
        warnings.append("Django REST Framework (rest_framework) tespit edilmedi")
    if not any(_basename(p) in ("requirements.txt", "pyproject.toml", "Pipfile") for p in files):
        warnings.append("bağımlılık dosyası (requirements.txt / pyproject.toml / Pipfile) bulunamadı")
    return {
        "manage_py_found": bool(manage),
        "manage_py_paths": manage[:20],
        "settings_modules": sorted(settings_found)[:20],
        "declared_settings_modules": declared_settings[:20],
        "django_apps": project_apps[:100],
        "installed_apps_count": len(all_apps),
        "drf_detected": drf,
        "warnings": warnings,
    }
