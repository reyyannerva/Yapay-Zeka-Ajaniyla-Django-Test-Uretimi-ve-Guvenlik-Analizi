"""Proje yönetimi ve arşiv yükleme API testleri — H4-03 / Issue #35.

Kimlik doğrulama gerçek SimpleJWT access token'larıyla yapılır (``force_authenticate`` kullanılmaz).
Arşivler her test için ayrı geçici depoya yazılır; gerçek kullanıcı yüklemelerine dokunulmaz.
"""
from __future__ import annotations

import hashlib
import io
import logging
import os
import re
import sys
from datetime import timedelta
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from core.models import AnalysisRun, Project, ReferenceRequirement
from core.projects import services

from .conftest import make_requirement, make_run
from .zipkit import SYMLINK, build_zip, django_files, valid_django_zip

pytestmark = pytest.mark.django_db

User = get_user_model()
LIST = reverse("projects:project-list")
PASSWORD = "Gizli-Parola-123"


def detail(pk) -> str:
    return reverse("projects:project-detail", args=[pk])


@pytest.fixture(autouse=True)
def archive_root(tmp_path, settings):
    """Her test için yalıtılmış, boşluk ve Türkçe karakter içeren geçici arşiv kökü."""
    root = tmp_path / "özel depo kökü"
    settings.PROJECT_ARCHIVE_ROOT = root
    cache.clear()  # yükleme throttle sayaçları testler arasında taşınmasın
    yield root
    cache.clear()


@pytest.fixture
def alice(db):
    return User.objects.create_user(username="alice", password=PASSWORD)


@pytest.fixture
def bob(db):
    return User.objects.create_user(username="bob", password=PASSWORD)


def client_for(user) -> APIClient:
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return c


@pytest.fixture
def api(alice):
    return client_for(alice)


@pytest.fixture
def bob_api(bob):
    return client_for(bob)


def upload(client, data: bytes | None = None, name="proje.zip", **fields):
    payload = {"name": fields.pop("project_name", "Mağaza API"), **fields}
    if data is not None:
        payload["archive"] = SimpleUploadedFile(name, data, content_type="application/zip")
    return client.post(LIST, payload, format="multipart")


def stored_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file()) if root.exists() else []


def archive_code(resp) -> str:
    return resp.json()["archive"][0]["code"]


# ====================================================================== CRUD

def test_create_project_with_valid_archive(api, alice, archive_root):
    data = valid_django_zip()
    resp = upload(api, data, description="Örnek proje")
    assert resp.status_code == 201, resp.json()
    body = resp.json()
    project = Project.objects.get(pk=body["id"])
    assert project.owner == alice and project.source_type == "ARCHIVE" and project.validation_status == "VALID"
    assert project.archive_sha256 == hashlib.sha256(data).hexdigest() == body["archive"]["sha256"]
    assert body["archive"]["original_name"] == "proje.zip" and body["archive"]["size_bytes"] == len(data)
    assert body["validation_report"]["drf_detected"] is True
    assert body["validation_report"]["settings_modules"] == ["config/settings.py"]
    # Depoya sunucu tarafından üretilen adla yazıldı; içerik birebir aynı.
    assert re.fullmatch(r"project_archives/\d{4}/\d{2}/[0-9a-f]{32}\.zip", project.source_archive.name)
    files = stored_files(archive_root)
    assert len(files) == 1 and files[0].read_bytes() == data


def test_response_never_exposes_storage_name_or_absolute_path(api, archive_root):
    resp = upload(api, valid_django_zip())
    text = resp.content.decode()
    project = Project.objects.get()
    assert project.source_archive.name not in text and str(archive_root) not in text
    assert "source_archive" not in resp.json() and "owner" not in resp.json()
    assert "project_archives" not in api.get(detail(project.pk)).content.decode()


def test_list_detail_update_delete_cycle(api, archive_root, django_capture_on_commit_callbacks):
    pk = upload(api, valid_django_zip()).json()["id"]
    listing = api.get(LIST)
    assert listing.status_code == 200 and listing.json()["count"] == 1
    assert listing.json()["results"][0]["id"] == pk
    got = api.get(detail(pk))
    assert got.status_code == 200 and got.json()["name"] == "Mağaza API"
    patched = api.patch(detail(pk), {"description": "güncel açıklama"}, format="json")
    assert patched.status_code == 200 and patched.json()["description"] == "güncel açıklama"
    put = api.put(detail(pk), {"name": "Yeni ad", "description": ""}, format="json")
    assert put.status_code == 200 and put.json()["name"] == "Yeni ad"
    with django_capture_on_commit_callbacks(execute=True):
        assert api.delete(detail(pk)).status_code == 204
    assert not Project.objects.exists() and stored_files(archive_root) == []
    assert api.get(detail(pk)).status_code == 404


def test_update_metadata_keeps_archive_unchanged(api):
    pk = upload(api, valid_django_zip()).json()["id"]
    before = Project.objects.values("source_archive", "archive_sha256", "validation_report").get(pk=pk)
    api.patch(detail(pk), {"name": "Başka ad"}, format="json")
    after = Project.objects.values("source_archive", "archive_sha256", "validation_report").get(pk=pk)
    assert before == after


def test_list_is_paginated_and_ordered_newest_first(api):
    for i in range(3):
        upload(api, valid_django_zip(), project_name=f"p{i}")
    body = api.get(LIST, {"page_size": 2}).json()
    assert body["count"] == 3 and len(body["results"]) == 2 and body["results"][0]["name"] == "p2"


def test_missing_required_fields(api):
    resp = api.post(LIST, {"description": "x"}, format="multipart")
    assert resp.status_code == 400 and {"name", "archive"} <= set(resp.json())


@pytest.mark.parametrize("name", ["", "   ", "a" * 151, "kötü\x00ad"])
def test_invalid_project_name(api, name):
    assert upload(api, valid_django_zip(), project_name=name).status_code == 400


def test_duplicate_name_for_same_owner_rejected_but_allowed_for_other_user(api, bob_api):
    assert upload(api, valid_django_zip()).status_code == 201
    dup = upload(api, valid_django_zip())
    assert dup.status_code == 400 and "name" in dup.json()
    assert upload(bob_api, valid_django_zip()).status_code == 201


def test_update_to_existing_name_rejected(api):
    upload(api, valid_django_zip(), project_name="a")
    pk = upload(api, valid_django_zip(), project_name="b").json()["id"]
    assert api.patch(detail(pk), {"name": "a"}, format="json").status_code == 400


@pytest.mark.parametrize("method", ["put", "patch", "delete"])
def test_collection_level_write_methods_not_allowed(api, method):
    assert getattr(api, method)(LIST, {}, format="json").status_code == 405


def test_post_on_detail_not_allowed(api):
    pk = upload(api, valid_django_zip()).json()["id"]
    assert api.post(detail(pk), {}, format="json").status_code == 405


def test_create_requires_multipart(api):
    resp = api.post(LIST, {"name": "x"}, format="json")
    assert resp.status_code == 415


# ====================================================================== toplu atama (mass assignment)

@pytest.mark.parametrize("field,value", [
    ("owner", "2"), ("validation_status", "VALID"), ("source_type", "ALLOWED_DIRECTORY"),
    ("source_archive", "project_archives/x.zip"), ("archive_sha256", "0" * 64), ("id", "999"),
    ("created_at", "2020-01-01T00:00:00Z"), ("validation_report", "{}"),
])
def test_protected_fields_rejected_on_create(api, bob, field, value):
    resp = upload(api, valid_django_zip(), **{field: value})
    assert resp.status_code == 400 and field in resp.json()
    assert not Project.objects.exists()


@pytest.mark.parametrize("field,value", [
    ("owner", 2), ("validation_status", "INVALID"), ("archive_sha256", "0" * 64), ("source_archive", "x.zip"),
    ("id", 5), ("validation_report", {}), ("created_at", "2020-01-01T00:00:00Z"),
])
def test_protected_fields_rejected_on_update(api, bob, field, value):
    pk = upload(api, valid_django_zip()).json()["id"]
    before = Project.objects.values().get(pk=pk)
    resp = api.patch(detail(pk), {field: value}, format="json")
    assert resp.status_code == 400 and field in resp.json()
    assert Project.objects.values().get(pk=pk) == before


def test_owner_is_always_server_side(api, alice, bob):
    resp = upload(api, valid_django_zip(), owner=str(bob.pk))
    assert resp.status_code == 400
    assert not Project.objects.filter(owner=bob).exists()


def test_archive_cannot_be_replaced_through_update(api):
    pk = upload(api, valid_django_zip()).json()["id"]
    resp = api.patch(detail(pk), {"archive": SimpleUploadedFile("y.zip", valid_django_zip())}, format="multipart")
    assert resp.status_code == 400 and "archive" in resp.json()


# ====================================================================== kimlik doğrulama (SimpleJWT)

def test_anonymous_requests_rejected(alice):
    anon = APIClient()
    project = Project.objects.create(owner=alice, name="x", source_type="ALLOWED_DIRECTORY", source_directory="d")
    for resp in (anon.get(LIST), anon.get(detail(project.pk)), anon.patch(detail(project.pk), {}),
                 anon.delete(detail(project.pk)), anon.post(LIST, {}, format="multipart")):
        assert resp.status_code == 401
    assert Project.objects.filter(pk=project.pk).exists()


@pytest.mark.parametrize("header", ["Bearer bozuk.token.degeri", "Bearer ", "Token abc", "Bearer a.b"])
def test_invalid_tokens_rejected(header):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=header)
    assert c.get(LIST).status_code == 401


def test_expired_token_rejected(alice):
    token = AccessToken.for_user(alice)
    token.set_exp(from_time=timezone.now() - timedelta(hours=2), lifetime=timedelta(minutes=1))
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    resp = c.get(LIST)
    assert resp.status_code == 401


def test_token_from_real_login_endpoint_works(alice):
    c = APIClient()
    login = c.post(reverse("auth:login"), {"username": "alice", "password": PASSWORD}, format="json")
    assert login.status_code == 200
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")
    assert upload(c, valid_django_zip()).status_code == 201 and c.get(LIST).json()["count"] == 1


def test_token_of_deactivated_user_rejected(alice):
    c = client_for(alice)
    alice.is_active = False
    alice.save()
    assert c.get(LIST).status_code == 401


# ====================================================================== sahiplik izolasyonu

@pytest.fixture
def bobs_project(bob_api):
    resp = upload(bob_api, valid_django_zip(), project_name="Bob'un gizli projesi", name="gizli-bob.zip")
    assert resp.status_code == 201
    return Project.objects.get(pk=resp.json()["id"])


def test_list_does_not_leak_foreign_projects(api, bobs_project):
    upload(api, valid_django_zip(), project_name="Alice projesi")
    body = api.get(LIST).json()
    assert [p["name"] for p in body["results"]] == ["Alice projesi"]
    assert "gizli" not in str(body) and "Bob" not in str(body)


def test_foreign_project_detail_is_hidden_as_404(api, bobs_project):
    resp = api.get(detail(bobs_project.pk))
    assert resp.status_code == 404 and "gizli" not in resp.content.decode()


def test_foreign_project_cannot_be_updated(api, bobs_project):
    for resp in (api.patch(detail(bobs_project.pk), {"name": "ele geçirildi"}, format="json"),
                 api.put(detail(bobs_project.pk), {"name": "ele geçirildi"}, format="json")):
        assert resp.status_code == 404
    assert Project.objects.get(pk=bobs_project.pk).name == "Bob'un gizli projesi"


def test_foreign_project_cannot_be_deleted_and_file_remains(api, bobs_project, archive_root,
                                                            django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        assert api.delete(detail(bobs_project.pk)).status_code == 404
    assert Project.objects.filter(pk=bobs_project.pk).exists() and len(stored_files(archive_root)) == 1


def test_users_with_same_archive_filename_do_not_overwrite_each_other(api, bob_api, archive_root):
    a, b = valid_django_zip(), valid_django_zip(extra={"bob.txt": "bob"})
    upload(api, a, name="ayni.zip")
    upload(bob_api, b, name="ayni.zip")
    names = list(Project.objects.values_list("source_archive", flat=True))
    assert len(set(names)) == 2
    assert {f.read_bytes() for f in stored_files(archive_root)} == {a, b}


def test_foreign_analysis_runs_are_not_counted_or_exposed(api, bobs_project):
    make_run(bobs_project)
    pk = upload(api, valid_django_zip()).json()["id"]
    assert api.get(detail(pk)).json()["analysis_run_count"] == 0


# ====================================================================== yükleme doğrulaması (API)

@pytest.mark.parametrize("data,name,code", [
    (b"", "proje.zip", "EMPTY_FILE"),
    (b"bu bir zip degil" * 20, "proje.zip", "NOT_A_ZIP"),
    (b"PK\x03\x04" + b"\x00" * 100, "proje.zip", "CORRUPT_ARCHIVE"),
    ("VALID", "proje.tar.gz", "UNSUPPORTED_TYPE"),
    ("VALID", "proje.exe", "UNSUPPORTED_TYPE"),
])
def test_invalid_uploads_rejected_without_storing(api, archive_root, data, name, code):
    resp = upload(api, valid_django_zip() if data == "VALID" else data, name=name)
    assert resp.status_code == 400 and archive_code(resp) == code, resp.json()
    assert not Project.objects.exists() and stored_files(archive_root) == []


def test_missing_file_rejected(api):
    resp = upload(api, None)
    assert resp.status_code == 400 and "archive" in resp.json()


def test_non_django_archive_rejected_with_actionable_message(api, archive_root):
    resp = upload(api, build_zip({"README.md": "x", "app.py": "print(1)"}))
    assert resp.status_code == 400 and archive_code(resp) == "NO_DJANGO_SETTINGS"
    assert "INSTALLED_APPS" in resp.json()["archive"][0]["detail"]
    assert stored_files(archive_root) == []


@pytest.mark.parametrize("prefix", ["", "kaynak/backend", "a/b/c"])
def test_valid_nested_django_layouts_accepted(api, prefix):
    resp = upload(api, valid_django_zip(prefix=prefix), project_name=f"p-{prefix or 'kok'}")
    assert resp.status_code == 201


def test_django_without_drf_accepted_with_warning(api):
    resp = upload(api, valid_django_zip(drf=False))
    assert resp.status_code == 201
    report = resp.json()["validation_report"]
    assert report["drf_detected"] is False and report["warnings"]


@pytest.mark.parametrize("raw_name,reason", [
    ("../../evil.py", "PATH_TRAVERSAL"), ("/etc/cron.d/x", "ABSOLUTE_PATH"), ("C:/x.py", "DRIVE_PATH"),
    ("//srv/share/x.py", "UNC_PATH"),
])
def test_zip_slip_rejected_via_api(api, archive_root, raw_name, reason):
    resp = upload(api, build_zip(django_files(), raw=[(raw_name, "x", None)]))
    assert resp.status_code == 400
    err = resp.json()["archive"][0]
    assert err["entries"][0]["reason"] == reason
    assert stored_files(archive_root) == []


def test_symlink_rejected_via_api(api, archive_root):
    resp = upload(api, build_zip(django_files(), raw=[("config/secret", "/etc/shadow", SYMLINK)]))
    assert resp.status_code == 400 and archive_code(resp) == "SYMLINK" and stored_files(archive_root) == []


def test_zip_bomb_rejected_via_api(api, settings, archive_root):
    settings.PROJECT_UPLOAD_LIMITS = {**settings.PROJECT_UPLOAD_LIMITS, "max_compression_ratio": 20,
                                      "ratio_check_min_bytes": 64 * 1024}
    resp = upload(api, build_zip({**django_files(), "bomb.bin": b"\0" * (8 * 1024 * 1024)}))
    assert resp.status_code == 400 and archive_code(resp) == "COMPRESSION_RATIO"
    assert stored_files(archive_root) == []


def test_excessive_uncompressed_size_via_api(api, settings):
    settings.PROJECT_UPLOAD_LIMITS = {**settings.PROJECT_UPLOAD_LIMITS, "max_total_uncompressed_bytes": 50_000,
                                      "max_compression_ratio": 10_000}
    resp = upload(api, build_zip({**django_files(), "big.bin": os.urandom(80_000)}))
    assert resp.status_code == 400 and archive_code(resp) == "UNCOMPRESSED_TOO_LARGE"


def test_excessive_member_count_via_api(api, settings):
    settings.PROJECT_UPLOAD_LIMITS = {**settings.PROJECT_UPLOAD_LIMITS, "max_entries": 12}
    resp = upload(api, build_zip({**django_files(), **{f"x/{i}.txt": "x" for i in range(10)}}))
    assert resp.status_code == 400 and archive_code(resp) == "TOO_MANY_ENTRIES"


def test_oversized_upload_returns_413_and_stores_nothing(api, settings, archive_root):
    settings.PROJECT_UPLOAD_LIMITS = {**settings.PROJECT_UPLOAD_LIMITS, "max_upload_bytes": 20_000}
    resp = upload(api, build_zip({**django_files(), "big.bin": os.urandom(100_000)}, compression=0))
    assert resp.status_code == 413
    assert not Project.objects.exists() and stored_files(archive_root) == []


def test_oversized_file_is_stopped_while_streaming(api, settings, archive_root, monkeypatch):
    """Content-Length ön kontrolünü geçen (çok parçalı paya sığan) ama sınırı aşan dosya, gövde okunurken
    MaxSizeUploadHandler tarafından durdurulur: 413, kayıt ve dosya yok."""
    from core.projects import upload as upload_mod

    settings.PROJECT_UPLOAD_LIMITS = {**settings.PROJECT_UPLOAD_LIMITS, "max_upload_bytes": 20_000}
    data = build_zip({**django_files(), "big.bin": os.urandom(40_000)}, compression=0)
    assert 20_000 < len(data) < 20_000 + 64 * 1024  # başlık ön kontrolüne takılmaz
    stopped = []
    real = upload_mod.MaxSizeUploadHandler.receive_data_chunk

    def spy(self, raw, start):
        try:
            return real(self, raw, start)
        except upload_mod.StopUpload:
            stopped.append(self.received)
            raise

    monkeypatch.setattr(upload_mod.MaxSizeUploadHandler, "receive_data_chunk", spy)
    resp = upload(api, data)
    assert resp.status_code == 413 and stopped and stopped[0] > 20_000
    assert not Project.objects.exists() and stored_files(archive_root) == []


def test_multiple_archives_rejected(api, archive_root):
    resp = api.post(LIST, {"name": "x", "archive": [SimpleUploadedFile("a.zip", valid_django_zip()),
                                                    SimpleUploadedFile("b.zip", valid_django_zip())]},
                    format="multipart")
    assert resp.status_code == 400 and stored_files(archive_root) == []


def test_secret_files_listed_in_report(api):
    resp = upload(api, valid_django_zip(extra={".env": "SECRET_KEY=gercek-gizli"}))
    assert resp.status_code == 201
    assert resp.json()["validation_report"]["rejected_entries"] == [{"path": ".env", "reason": "SECRET_FILE_EXCLUDED"}]
    assert "gercek-gizli" not in resp.content.decode()


def test_error_responses_do_not_leak_internal_paths(api, archive_root):
    resp = upload(api, b"PK\x03\x04garbage")
    text = resp.content.decode()
    assert str(archive_root) not in text and "Traceback" not in text and "site-packages" not in text


# ====================================================================== yüklenen kod çalıştırılmaz

def test_uploaded_code_is_never_imported_or_executed(api, tmp_path, monkeypatch):
    marker = tmp_path / "ÇALIŞTIRILDI.txt"
    payload = f"import pathlib\npathlib.Path({str(marker)!r}).write_text('x')\n"
    files = django_files()
    files["manage.py"] = files["manage.py"].replace("import os", payload + "import os")
    files["config/settings.py"] = payload + files["config/settings.py"]
    files["shop/apps.py"] = payload + files["shop/apps.py"]
    files["h403_payload_pkg/__init__.py"] = payload
    files["setup.py"] = payload
    files["conftest.py"] = payload

    import subprocess

    def forbidden(*a, **k):
        raise AssertionError("yükleme sırasında alt süreç başlatıldı")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(os, "system", forbidden)
    before = set(sys.modules)
    resp = upload(api, build_zip(files))
    assert resp.status_code == 201, resp.json()
    assert not marker.exists()
    new_modules = set(sys.modules) - before
    assert not [m for m in new_modules if m.startswith(("h403_payload_pkg", "shop", "config.settings"))]


# ====================================================================== depo ve veritabanı tutarlılığı

def _uploaded(data=None, name="p.zip"):
    return SimpleUploadedFile(name, data or valid_django_zip())


def test_database_failure_leaves_no_orphan_file(alice, archive_root, monkeypatch):
    def boom(self, *a, **k):
        raise RuntimeError("veritabanı yazılamadı")

    monkeypatch.setattr(Project, "save", boom)
    with pytest.raises(RuntimeError):
        services.create_project(alice, "x", "", _uploaded())
    assert stored_files(archive_root) == []


def test_concurrent_duplicate_name_integrity_error_cleans_up_file(alice, archive_root, monkeypatch):
    services.create_project(alice, "ayni", "", _uploaded())
    monkeypatch.setattr(services, "name_taken", lambda owner, name: False)  # yarış: ön kontrol geçti
    with pytest.raises(services.DuplicateProjectName):
        services.create_project(alice, "ayni", "", _uploaded())
    assert len(stored_files(archive_root)) == 1 and Project.objects.count() == 1


def test_storage_write_failure_creates_no_record(alice, monkeypatch):
    storage = Project._meta.get_field("source_archive").storage

    def fail_save(*a, **k):
        raise OSError("disk dolu")

    monkeypatch.setattr(storage, "save", fail_save)
    with pytest.raises(OSError):
        services.create_project(alice, "x", "", _uploaded())
    assert not Project.objects.exists()


def test_delete_cascades_finished_analysis_records(api, django_capture_on_commit_callbacks, archive_root):
    pk = upload(api, valid_django_zip()).json()["id"]
    project = Project.objects.get(pk=pk)
    make_run(project, status="COMPLETED", started_at=timezone.now(), finished_at=timezone.now())
    make_requirement(project)
    with django_capture_on_commit_callbacks(execute=True):
        assert api.delete(detail(pk)).status_code == 204
    assert not AnalysisRun.objects.exists() and not ReferenceRequirement.objects.exists()
    assert stored_files(archive_root) == []


def test_delete_blocked_while_analysis_is_active(api, archive_root, django_capture_on_commit_callbacks):
    pk = upload(api, valid_django_zip()).json()["id"]
    make_run(Project.objects.get(pk=pk))  # QUEUED = aktif
    with django_capture_on_commit_callbacks(execute=True):
        resp = api.delete(detail(pk))
    assert resp.status_code == 409
    assert Project.objects.filter(pk=pk).exists() and len(stored_files(archive_root)) == 1


def test_file_is_not_deleted_when_transaction_rolls_back(alice, archive_root):
    project = services.create_project(alice, "x", "", _uploaded())
    pk = project.pk
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            services.delete_project(project)
            raise RuntimeError("sonradan hata")
    assert Project.objects.filter(pk=pk).exists() and len(stored_files(archive_root)) == 1


def test_storage_cleanup_failure_is_logged_and_recoverable(api, archive_root, monkeypatch, caplog,
                                                           django_capture_on_commit_callbacks):
    pk = upload(api, valid_django_zip()).json()["id"]
    storage = Project._meta.get_field("source_archive").storage
    real_delete = storage.delete
    monkeypatch.setattr(storage, "delete", lambda name: (_ for _ in ()).throw(PermissionError("kilitli")))
    with caplog.at_level(logging.WARNING, logger="core.projects"), \
            django_capture_on_commit_callbacks(execute=True):
        assert api.delete(detail(pk)).status_code == 204
    assert not Project.objects.exists() and len(stored_files(archive_root)) == 1
    assert any("cleanup_project_archives" in r.getMessage() for r in caplog.records)
    # Öksüz dosya tespit edilebilir ve komutla temizlenebilir.
    monkeypatch.setattr(storage, "delete", real_delete)
    out = io.StringIO()
    call_command("cleanup_project_archives", stdout=out)
    assert "1 öksüz arşiv bulundu" in out.getvalue() and len(stored_files(archive_root)) == 1
    call_command("cleanup_project_archives", "--delete", stdout=io.StringIO())
    assert stored_files(archive_root) == []


def test_cleanup_command_keeps_referenced_archives(api, archive_root):
    upload(api, valid_django_zip())
    out = io.StringIO()
    call_command("cleanup_project_archives", "--delete", stdout=out)
    assert "0 öksüz arşiv" in out.getvalue() and len(stored_files(archive_root)) == 1


def test_postgresql_record_persists_expected_values(api, alice):
    from django.db import connection

    assert connection.vendor == "postgresql"
    pk = upload(api, valid_django_zip(), description="açıklama").json()["id"]
    with connection.cursor() as cur:
        cur.execute("SELECT owner_id, name, source_type, validation_status, archive_sha256, "
                    "validation_report->'archive'->>'original_name' FROM projects WHERE id = %s", [pk])
        owner_id, name, source_type, status, sha, original = cur.fetchone()
    assert (owner_id, name, source_type, status, original) == (alice.pk, "Mağaza API", "ARCHIVE", "VALID", "proje.zip")
    assert re.fullmatch(r"[0-9a-f]{64}", sha)


def test_storage_does_not_offer_public_url(api):
    upload(api, valid_django_zip())
    with pytest.raises(NotImplementedError):
        Project.objects.get().source_archive.url


@pytest.mark.skipif(os.name != "posix", reason="POSIX dosya izinleri")
def test_stored_archive_is_private_and_not_executable(api, archive_root):
    upload(api, valid_django_zip())
    (path,) = stored_files(archive_root)
    assert oct(path.stat().st_mode & 0o777) == "0o600"


def test_upload_throttle_limits_requests(api, settings):
    from rest_framework.settings import api_settings
    settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK,
                               "DEFAULT_THROTTLE_RATES": {**settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],
                                                          "project_upload": "2/hour"}}
    api_settings.reload()
    from rest_framework.throttling import ScopedRateThrottle
    ScopedRateThrottle.THROTTLE_RATES = api_settings.DEFAULT_THROTTLE_RATES
    try:
        codes = [upload(api, valid_django_zip(), project_name=f"t{i}").status_code for i in range(3)]
        assert codes == [201, 201, 429]
    finally:
        api_settings.reload()
        ScopedRateThrottle.THROTTLE_RATES = api_settings.DEFAULT_THROTTLE_RATES


def test_integrity_error_names_are_not_silently_swallowed(alice, monkeypatch):
    def other_integrity(self, *a, **k):
        raise IntegrityError("başka bir kısıt")

    monkeypatch.setattr(Project, "save", other_integrity)
    with pytest.raises(IntegrityError):
        services.create_project(alice, "x", "", _uploaded())
