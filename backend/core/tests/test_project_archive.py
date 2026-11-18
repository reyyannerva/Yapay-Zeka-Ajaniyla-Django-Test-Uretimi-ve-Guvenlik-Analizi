"""Arşiv güvenliği ve Django yapı ön kontrolü birim testleri — H4-03 / Issue #35.

Testler veritabanı gerektirmez; arşivler bellekte üretilir ve hiçbir dosya diske açılmaz.
"""
from __future__ import annotations

import io
import os
import zipfile

import pytest

from core.projects import structure
from core.projects.archive import ArchiveLimits, ArchiveRejected, inspect_zip, normalize_member_path

from .zipkit import CHAR_DEVICE, FIFO, REGULAR, SYMLINK, build_zip, django_files, valid_django_zip

LIMITS = ArchiveLimits()


def inspect(data: bytes, name: str = "proje.zip", limits: ArchiveLimits = LIMITS):
    return inspect_zip(io.BytesIO(data), name, limits, text_wanted=structure.wants_text)


def rejected(data: bytes, name: str = "proje.zip", limits: ArchiveLimits = LIMITS) -> ArchiveRejected:
    with pytest.raises(ArchiveRejected) as exc:
        inspect(data, name, limits)
    return exc.value


def analyze(data: bytes) -> dict:
    ins = inspect(data)
    return structure.analyze(ins.files, ins.texts)


# ------------------------------------------------------------------ biçim

def test_valid_django_zip_is_accepted_with_report_fields():
    ins = inspect(valid_django_zip())
    assert ins.file_count == len(django_files()) and len(ins.sha256) == 64 and ins.size_bytes > 0
    assert "config/settings.py" in ins.texts and "shop/models.py" not in ins.texts


@pytest.mark.parametrize("name", ["proje.tar.gz", "proje.rar", "proje", "proje.zip.exe"])
def test_unsupported_extension(name):
    assert rejected(valid_django_zip(), name).code == "UNSUPPORTED_TYPE"


def test_uppercase_extension_is_allowed():
    assert inspect(valid_django_zip(), "PROJE.ZIP").file_count > 0


def test_empty_file():
    assert rejected(b"").code == "EMPTY_FILE"


def test_fake_zip_by_extension_only():
    assert rejected(b"print('merhaba')\n" * 10).code == "NOT_A_ZIP"


def test_corrupt_zip_with_valid_signature():
    assert rejected(b"PK\x03\x04" + os.urandom(200)).code == "CORRUPT_ARCHIVE"


def test_truncated_zip():
    data = valid_django_zip()
    assert rejected(data[: len(data) // 2]).code == "CORRUPT_ARCHIVE"


def test_crc_mismatch_is_detected_by_actually_reading_content():
    data = bytearray(build_zip({"a.txt": "A" * 5000}, compression=zipfile.ZIP_STORED))
    idx = data.find(b"AAAA")
    data[idx] = ord("B")  # bildirilen CRC artık içerikle uyuşmuyor
    err = rejected(bytes(data))
    assert err.code == "CORRUPT_ARCHIVE" and err.entries[0]["path"] == "a.txt"


def test_empty_archive():
    assert rejected(build_zip({})).code == "EMPTY_ARCHIVE"


def test_encrypted_entry_rejected():
    data = bytearray(build_zip({"a.txt": "x"}))
    # Genel amaçlı bayrak bit 0 (şifreli): yerel başlık ve merkez dizin girdisinde.
    for sig, offset in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
        i = data.find(sig)
        data[i + offset] |= 0x01
    assert rejected(bytes(data)).code == "ENCRYPTED"


# ------------------------------------------------------------------ yol güvenliği (Zip Slip)

@pytest.mark.parametrize("name,reasons", [
    ("../evil.py", {"PATH_TRAVERSAL"}),
    ("app/../../evil.py", {"PATH_TRAVERSAL"}),
    ("..\\evil.py", {"BACKSLASH_PATH", "PATH_TRAVERSAL"}),           # Windows'ta zipfile \ → / çevirir
    ("app\\..\\..\\evil.py", {"BACKSLASH_PATH", "PATH_TRAVERSAL"}),
    ("/etc/passwd", {"ABSOLUTE_PATH"}),
    ("C:/Windows/evil.py", {"DRIVE_PATH"}),
    ("C:\\Windows\\evil.py", {"BACKSLASH_PATH", "DRIVE_PATH"}),
    ("//server/share/evil.py", {"UNC_PATH"}),
    ("\\\\server\\share\\evil.py", {"BACKSLASH_PATH", "UNC_PATH"}),
    ("app/CON.py", {"RESERVED_NAME"}),
    ("app/nul", {"RESERVED_NAME"}),
    ("app/a<b>.py", {"INVALID_NAME"}),
    ("app/trailing. ", {"INVALID_NAME"}),
    ("app/ctrl\x07.py", {"INVALID_NAME"}),
])
def test_dangerous_paths_are_rejected(name, reasons):
    err = rejected(valid_django_zip_with_raw([(name, "x", None)]))
    assert err.entries and err.entries[0]["reason"] in reasons, err.entries


def valid_django_zip_with_raw(raw):
    return build_zip(django_files(), raw=raw)


@pytest.mark.parametrize("raw,expected", [
    ("a/b.py", "a/b.py"), ("./a/./b.py", "a/b.py"), ("a//b.py", "a/b.py"), ("dir/", "dir"),
])
def test_normalize_member_path_safe_variants(raw, expected):
    assert normalize_member_path(raw) == (expected, None)


def test_traversal_hidden_after_normalization_is_rejected():
    assert normalize_member_path("a/./../../b")[1] == "PATH_TRAVERSAL"


# ------------------------------------------------------------------ sembolik bağlantı ve özel dosyalar

@pytest.mark.parametrize("mode,reason", [(SYMLINK, "SYMLINK"), (FIFO, "SPECIAL_FILE"), (CHAR_DEVICE, "SPECIAL_FILE")])
def test_symlinks_and_special_files_rejected(mode, reason):
    err = rejected(valid_django_zip_with_raw([("app/link", "/etc/passwd", mode)]))
    assert err.code == reason and err.entries[0] == {"path": "app/link", "reason": reason}


def test_regular_unix_file_mode_is_allowed():
    assert inspect(valid_django_zip_with_raw([("app/x.py", "x = 1\n", REGULAR)])).file_count > 0


# ------------------------------------------------------------------ yinelenen ve çakışan yollar

def test_duplicate_paths_rejected():
    err = rejected(valid_django_zip_with_raw([("app/x.py", "1", None), ("app/x.py", "2", None)]))
    assert err.code == "DUPLICATE_PATH"


def test_normalized_duplicate_rejected():
    err = rejected(valid_django_zip_with_raw([("app/x.py", "1", None), ("app/./x.py", "2", None)]))
    assert err.code == "DUPLICATE_PATH"


def test_case_insensitive_collision_rejected():
    err = rejected(valid_django_zip_with_raw([("app/Views.py", "1", None), ("app/views.py", "2", None)]))
    assert err.code == "CASE_COLLISION"


def test_file_directory_conflict_rejected():
    err = rejected(valid_django_zip_with_raw([("app/x", "1", None), ("app/x/y.py", "2", None)]))
    assert err.code == "PATH_CONFLICT"


def test_repeated_directory_entries_are_harmless():
    assert inspect(valid_django_zip_with_raw([("pkg/", "", None), ("pkg/", "", None)])).file_count > 0


# ------------------------------------------------------------------ kaynak sınırları ve ZIP bombası

def test_compression_ratio_bomb_rejected():
    limits = ArchiveLimits(max_compression_ratio=50, ratio_check_min_bytes=64 * 1024)
    data = build_zip({**django_files(), "bomb.txt": b"\0" * (4 * 1024 * 1024)})
    err = rejected(data, limits=limits)
    assert err.code == "COMPRESSION_RATIO" and err.entries[0]["path"] == "bomb.txt"


def test_total_uncompressed_size_limit():
    limits = ArchiveLimits(max_total_uncompressed_bytes=10_000, max_compression_ratio=10_000)
    data = build_zip({**django_files(), "big.txt": os.urandom(20_000)})
    assert rejected(data, limits=limits).code == "UNCOMPRESSED_TOO_LARGE"


def test_member_size_limit():
    limits = ArchiveLimits(max_member_bytes=1000, max_compression_ratio=10_000)
    data = build_zip({**django_files(), "big.txt": os.urandom(5000)})
    assert rejected(data, limits=limits).code == "MEMBER_TOO_LARGE"


def test_entry_count_limit():
    limits = ArchiveLimits(max_entries=len(django_files()) + 2)
    data = build_zip({**django_files(), **{f"x/{i}.txt": "x" for i in range(5)}})
    assert rejected(data, limits=limits).code == "TOO_MANY_ENTRIES"


def test_depth_limit():
    deep = "/".join(f"d{i}" for i in range(40)) + "/x.py"
    assert rejected(valid_django_zip_with_raw([(deep, "x", None)])).code == "TOO_DEEP"


def test_path_length_limit():
    long_name = "a/" + "b" * 300 + ".py"
    assert rejected(valid_django_zip_with_raw([(long_name, "x", None)])).code == "PATH_TOO_LONG"


def test_compressed_upload_size_limit():
    limits = ArchiveLimits(max_upload_bytes=100)
    assert rejected(valid_django_zip(), limits=limits).code == "FILE_TOO_LARGE"


def test_declared_size_is_not_trusted(monkeypatch):
    """Merkez dizindeki boyut küçük gösterilse bile gerçek okuma sınırı uygular."""
    limits = ArchiveLimits(max_member_bytes=1000, max_compression_ratio=10_000)
    data = build_zip({**django_files(), "big.txt": os.urandom(5000)})
    real_infolist = zipfile.ZipFile.infolist

    def lying_infolist(self):
        infos = real_infolist(self)
        for info in infos:
            if info.filename == "big.txt":
                info.file_size = 10  # bildirilen boyut sınırın altında
        return infos

    monkeypatch.setattr(zipfile.ZipFile, "infolist", lying_infolist)
    with pytest.raises(ArchiveRejected) as exc:
        inspect(data, limits=limits)
    assert exc.value.code in {"MEMBER_TOO_LARGE", "CORRUPT_ARCHIVE"}


# ------------------------------------------------------------------ gizli dosyalar

def test_secret_files_are_reported_not_rejected():
    ins = inspect(valid_django_zip(extra={".env": "SECRET=1", "keys/server.pem": "x", "shop/.env.local": "x"}))
    assert {e["path"] for e in ins.excluded} == {".env", "keys/server.pem", "shop/.env.local"}
    assert all(e["reason"] == "SECRET_FILE_EXCLUDED" for e in ins.excluded)


# ------------------------------------------------------------------ Django yapı ön kontrolü

def test_structure_flat_project():
    rep = analyze(valid_django_zip())
    assert rep["manage_py_found"] and rep["settings_modules"] == ["config/settings.py"]
    assert rep["declared_settings_modules"] == ["config.settings"] and rep["drf_detected"]
    assert rep["django_apps"] == ["shop"] and rep["warnings"] == []


def test_structure_nested_project():
    rep = analyze(valid_django_zip(prefix="backend/src"))
    assert rep["manage_py_paths"] == ["backend/src/manage.py"]
    assert rep["settings_modules"] == ["backend/src/config/settings.py"]


def test_structure_settings_package_layout():
    files = {k: v for k, v in django_files().items() if k != "config/settings.py"}
    files["config/settings/__init__.py"] = ""
    files["config/settings/base.py"] = "INSTALLED_APPS = ['django.contrib.auth', 'rest_framework']\n"
    files["config/settings/dev.py"] = "from .base import *\nDEBUG = True\n"
    rep = analyze(build_zip(files))
    assert rep["settings_modules"] == ["config/settings/base.py"]


def test_structure_django_without_drf_is_accepted_with_warning():
    rep = analyze(valid_django_zip(drf=False))
    assert rep["drf_detected"] is False
    assert any("rest_framework" in w for w in rep["warnings"])


def test_structure_drf_detected_from_requirements_only():
    files = django_files(drf=False)
    files["requirements.txt"] = "Django\ndjangorestframework==3.15\n"
    assert analyze(build_zip(files))["drf_detected"] is True


def test_structure_installed_apps_augmented_assignment():
    files = django_files()
    files["config/settings.py"] = "INSTALLED_APPS = []\nINSTALLED_APPS += ['rest_framework']\n"
    assert analyze(build_zip(files))["drf_detected"] is True


def test_structure_without_manage_py_but_wsgi_is_accepted_with_warning():
    files = {k: v for k, v in django_files().items() if not k.endswith("manage.py")}
    rep = analyze(build_zip(files))
    assert rep["manage_py_found"] is False and "manage.py bulunamadı" in rep["warnings"]


def test_structure_non_django_archive_rejected():
    ins = inspect(build_zip({"README.md": "# proje", "main.py": "print(1)\n"}))
    with pytest.raises(ArchiveRejected) as exc:
        structure.analyze(ins.files, ins.texts)
    assert exc.value.code == "NO_DJANGO_SETTINGS"


def test_structure_settings_without_installed_apps_rejected():
    ins = inspect(build_zip({"manage.py": "x", "config/settings.py": "DEBUG = True\n"}))
    with pytest.raises(ArchiveRejected) as exc:
        structure.analyze(ins.files, ins.texts)
    assert exc.value.code == "NO_DJANGO_SETTINGS"


def test_structure_settings_without_entrypoint_rejected():
    ins = inspect(build_zip({"lib/settings.py": "INSTALLED_APPS = []\n"}))
    with pytest.raises(ArchiveRejected) as exc:
        structure.analyze(ins.files, ins.texts)
    assert exc.value.code == "NO_DJANGO_ENTRYPOINT"


def test_structure_syntax_error_in_settings_falls_back_to_text():
    files = django_files()
    files["config/settings.py"] = "INSTALLED_APPS = [\n  'rest_framework',\n  oops((\n"
    rep = analyze(build_zip(files))
    assert rep["settings_modules"] == ["config/settings.py"]
