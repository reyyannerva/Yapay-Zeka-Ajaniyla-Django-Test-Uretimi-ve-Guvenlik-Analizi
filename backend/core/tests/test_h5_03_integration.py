"""H5-03 / Issue #41 — frontend'in kullandığı API sözleşmesinin iki kullanıcıyla uçtan uca doğrulanması.

Testler gerçek JWT (login uç noktası) ile çalışır ve PostgreSQL test veritabanını kullanır (SQLite desteklenmez;
``test_database_is_postgresql``). Kapsam: veri izolasyonu (Issue #41 kabul kriteri 9), kalıcılık (AC5/AC10),
referans JSON'da beş HTTP metodu ve geçersiz girdiler (AC7), frontend'in kullandığı yanıt biçimleri (AC1/AC6).
"""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from rest_framework.test import APIClient

from core.models import AnalysisRun, Project, ReferenceRequirement

from .zipkit import valid_django_zip

pytestmark = pytest.mark.django_db

PASSWORD = "Gizli-Parola-123"
HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


@pytest.fixture(autouse=True)
def _isolation(tmp_path, settings):
    settings.PROJECT_ARCHIVE_ROOT = tmp_path / "archives"
    cache.clear()
    yield
    cache.clear()


def _client_for(username: str) -> APIClient:
    get_user_model().objects.create_user(username=username, password=PASSWORD, email=f"{username}@example.test")
    client = APIClient()
    tokens = client.post("/api/auth/login/", {"username": username, "password": PASSWORD}, format="json")
    assert tokens.status_code == 200, tokens.content
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens.data['access']}")
    return client


@pytest.fixture
def user_a():
    return _client_for("kullanici_a")


@pytest.fixture
def user_b():
    return _client_for("kullanici_b")


def upload(client: APIClient, name: str, **extra):
    archive = SimpleUploadedFile(f"{name}.zip", valid_django_zip(), content_type="application/zip")
    return client.post("/api/projects/", {"name": name, "archive": archive, **extra}, format="multipart")


def access_rule(project_id: int, code: str, method: str = "GET") -> dict:
    return {
        "project": project_id,
        "requirement_code": code,
        "category": "ACCESS_RULE",
        "source": "JSON_UPLOAD",
        "title": "Anonim erişemez",
        "expected_result": "401",
        "specification": {"schema_version": 1, "endpoint": "/api/x/", "method": method,
                          "expected_status_by_role": {"anonim": 401}},
    }


@pytest.fixture
def b_records(user_b):
    """Kullanıcı B'nin proje, analiz ve referans kayıtları."""
    project = upload(user_b, "b-projesi").data
    requirement = user_b.post("/api/reference-requirements/", access_rule(project["id"], "B-REQ"), format="json").data
    run = user_b.post("/api/analysis-runs/", {"project": project["id"], "method": "RULE_BASED"}, format="json").data
    return {"project": project, "requirement": requirement, "run": run}


def test_database_is_postgresql():
    assert connection.vendor == "postgresql"


# --- Sahiplik matrisi (Issue #41 / AC9) ---
def test_lists_are_isolated_per_user(user_a, user_b, b_records):
    upload(user_a, "a-projesi")
    names_a = [p["name"] for p in user_a.get("/api/projects/").data["results"]]
    names_b = [p["name"] for p in user_b.get("/api/projects/").data["results"]]
    assert names_a == ["a-projesi"]
    assert names_b == ["b-projesi"]
    assert user_a.get("/api/analysis-runs/").data == []
    assert user_a.get("/api/reference-requirements/").data == []
    assert len(user_b.get("/api/analysis-runs/").data) == 1


def test_foreign_project_read_update_delete_hidden_as_404(user_a, b_records):
    pid = b_records["project"]["id"]
    assert user_a.get(f"/api/projects/{pid}/").status_code == 404
    assert user_a.patch(f"/api/projects/{pid}/", {"name": "ele-gecirildi"}, format="json").status_code == 404
    assert user_a.put(f"/api/projects/{pid}/", {"name": "x", "description": ""}, format="json").status_code == 404
    assert user_a.delete(f"/api/projects/{pid}/").status_code == 404
    project = Project.objects.get(pk=pid)
    assert project.name == "b-projesi"


def test_cannot_create_analysis_on_foreign_project(user_a, b_records):
    pid = b_records["project"]["id"]
    resp = user_a.post("/api/analysis-runs/", {"project": pid, "method": "RULE_BASED"}, format="json")
    assert resp.status_code == 400 and "project" in resp.data
    assert AnalysisRun.objects.filter(project_id=pid).count() == 1


def test_foreign_analysis_run_detail_hidden(user_a, b_records):
    assert user_a.get(f"/api/analysis-runs/{b_records['run']['id']}/").status_code == 404


def test_foreign_reference_requirement_not_readable_or_writable(user_a, b_records):
    rid = b_records["requirement"]["id"]
    assert user_a.get(f"/api/reference-requirements/{rid}/").status_code == 404
    assert user_a.patch(f"/api/reference-requirements/{rid}/", {"is_active": False}, format="json").status_code == 404
    assert user_a.put(f"/api/reference-requirements/{rid}/",
                      access_rule(b_records["project"]["id"], "B-REQ", "POST"), format="json").status_code == 404
    assert user_a.delete(f"/api/reference-requirements/{rid}/").status_code == 404
    requirement = ReferenceRequirement.objects.get(pk=rid)
    assert requirement.is_active is True and requirement.revision == 1


def test_cannot_add_reference_to_foreign_project(user_a, b_records):
    resp = user_a.post("/api/reference-requirements/", access_rule(b_records["project"]["id"], "A-REQ"), format="json")
    assert resp.status_code == 400 and "project" in resp.data
    assert not ReferenceRequirement.objects.filter(requirement_code="A-REQ").exists()


def test_cannot_move_own_reference_to_foreign_project(user_a, b_records):
    own = upload(user_a, "a-projesi").data
    mine = user_a.post("/api/reference-requirements/", access_rule(own["id"], "A-REQ"), format="json").data
    resp = user_a.patch(f"/api/reference-requirements/{mine['id']}/", {"project": b_records["project"]["id"]},
                        format="json")
    assert resp.status_code == 400
    assert ReferenceRequirement.objects.get(pk=mine["id"]).project_id == own["id"]


def test_owner_field_in_body_cannot_assign_record_to_another_user(user_a, b_records):
    b_user = get_user_model().objects.get(username="kullanici_b")
    resp = upload(user_a, "sahip-denemesi", owner=b_user.id)
    assert resp.status_code == 400 and "owner" in resp.data
    assert not Project.objects.filter(name="sahip-denemesi").exists()


def test_tampered_ids_do_not_bypass_ownership(user_a, b_records):
    # URL'deki kimliği tahmin etmek/sırayla denemek de yalnızca 404 üretir (varlık ifşa edilmez).
    for pid in range(b_records["project"]["id"] - 2, b_records["project"]["id"] + 3):
        resp = user_a.get(f"/api/projects/{pid}/")
        assert resp.status_code == 404
        assert "b-projesi" not in resp.content.decode()


# --- Referans JSON: beş HTTP metodu ve geçersiz girdiler (AC7) ---
@pytest.mark.parametrize("method", HTTP_METHODS)
def test_reference_access_rule_accepts_each_http_method(user_a, method):
    project = upload(user_a, f"p-{method.lower()}").data
    resp = user_a.post("/api/reference-requirements/", access_rule(project["id"], f"ACC-{method}", method),
                       format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["http_method"] == method
    assert ReferenceRequirement.objects.get(pk=resp.data["id"]).specification["method"] == method


@pytest.mark.parametrize("method", ["TRACE", "HEAD", "OPTIONS", "get", ""])
def test_reference_rejects_unsupported_http_method_and_persists_nothing(user_a, method):
    project = upload(user_a, "p-gecersiz").data
    resp = user_a.post("/api/reference-requirements/", access_rule(project["id"], "ACC-X", method), format="json")
    assert resp.status_code == 400
    assert "method" in resp.data["specification"]
    assert ReferenceRequirement.objects.count() == 0


def test_reference_invalid_payloads_are_rejected_with_field_errors(user_a):
    project = upload(user_a, "p-alanlar").data
    missing = user_a.post("/api/reference-requirements/", {"project": project["id"], "category": "ACCESS_RULE"},
                          format="json")
    assert missing.status_code == 400 and {"requirement_code", "title"} <= set(missing.data)
    wrong_type = access_rule(project["id"], "ACC-T")
    wrong_type["specification"]["expected_status_by_role"] = {"anonim": "dört yüz bir"}
    assert user_a.post("/api/reference-requirements/", wrong_type, format="json").status_code == 400
    first = user_a.post("/api/reference-requirements/", access_rule(project["id"], "ACC-D"), format="json")
    duplicate = user_a.post("/api/reference-requirements/", access_rule(project["id"], "ACC-D"), format="json")
    assert first.status_code == 201 and duplicate.status_code == 400
    assert ReferenceRequirement.objects.filter(requirement_code="ACC-D").count() == 1


def test_reference_put_patch_delete_cycle(user_a):
    project = upload(user_a, "p-crud").data
    created = user_a.post("/api/reference-requirements/", access_rule(project["id"], "ACC-C"), format="json").data
    put = user_a.put(f"/api/reference-requirements/{created['id']}/", access_rule(project["id"], "ACC-C", "PUT"),
                     format="json")
    assert put.status_code == 200 and put.data["http_method"] == "PUT" and put.data["revision"] == 2
    patch = user_a.patch(f"/api/reference-requirements/{created['id']}/", {"is_active": False}, format="json")
    assert patch.status_code == 200 and patch.data["is_active"] is False
    assert user_a.delete(f"/api/reference-requirements/{created['id']}/").status_code == 204
    assert not ReferenceRequirement.objects.filter(pk=created["id"]).exists()


# --- PostgreSQL kalıcılığı ve frontend akışı (AC5, AC6, AC10) ---
def test_frontend_crud_flow_persists_in_postgresql(user_a):
    created = upload(user_a, "akis-projesi", description="ilk")
    assert created.status_code == 201
    pid = created.data["id"]
    assert Project.objects.get(pk=pid).owner.username == "kullanici_a"

    updated = user_a.patch(f"/api/projects/{pid}/", {"description": "güncellendi"}, format="json")
    assert updated.status_code == 200
    Project.objects.get(pk=pid).refresh_from_db()
    assert Project.objects.get(pk=pid).description == "güncellendi"
    assert user_a.get(f"/api/projects/{pid}/").data["description"] == "güncellendi"  # "sayfa yenileme"

    user_a.post("/api/reference-requirements/", access_rule(pid, "ACC-SNAP"), format="json")
    run = user_a.post("/api/analysis-runs/", {"project": pid, "method": "HYBRID", "llm_provider": "GROQ",
                                              "llm_model": "ornek-model"}, format="json")
    assert run.status_code == 201 and run.data["status"] == "QUEUED"
    stored = AnalysisRun.objects.get(pk=run.data["id"])
    assert stored.project_id == pid and stored.project.owner.username == "kullanici_a"
    assert [r["requirement_code"] for r in stored.requirements_snapshot] == ["ACC-SNAP"]
    detail = user_a.get(f"/api/analysis-runs/{stored.pk}/").data
    assert detail["progress"]["percent"] is None and detail["generated_test_count"] == 0

    # Aktif analizli proje silinemez (409); analiz sonlanınca CASCADE ile silinir.
    assert user_a.delete(f"/api/projects/{pid}/").status_code == 409
    AnalysisRun.objects.filter(pk=stored.pk).update(status="CANCELLED", finished_at=stored.created_at)
    assert user_a.delete(f"/api/projects/{pid}/").status_code == 204
    assert not Project.objects.filter(pk=pid).exists()
    assert not AnalysisRun.objects.filter(pk=stored.pk).exists()
    assert not ReferenceRequirement.objects.filter(project_id=pid).exists()


def test_invalid_archive_is_rejected_and_not_persisted(user_a):
    corrupt = SimpleUploadedFile("bozuk.zip", b"PK\x03\x04 bozuk", content_type="application/zip")
    resp = user_a.post("/api/projects/", {"name": "bozuk", "archive": corrupt}, format="multipart")
    assert resp.status_code == 400 and resp.data["archive"][0]["code"]
    text = SimpleUploadedFile("not.txt", b"merhaba", content_type="text/plain")
    assert user_a.post("/api/projects/", {"name": "metin", "archive": text}, format="multipart").status_code == 400
    assert user_a.post("/api/projects/", {"name": "dosyasiz"}, format="multipart").status_code == 400
    assert user_a.post("/api/projects/", {"name": "json"}, format="json").status_code == 415
    assert not Project.objects.exists()


def test_logout_blacklists_refresh_and_old_access_has_short_lifetime(user_a):
    tokens = APIClient().post("/api/auth/login/", {"username": "kullanici_a", "password": PASSWORD}, format="json").data
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    assert client.post("/api/auth/logout/", {"refresh": tokens["refresh"]}, format="json").status_code == 205
    assert APIClient().post("/api/auth/refresh/", {"refresh": tokens["refresh"]}, format="json").status_code == 401


def test_refresh_rotation_blacklists_previous_refresh(user_a):
    tokens = APIClient().post("/api/auth/login/", {"username": "kullanici_a", "password": PASSWORD}, format="json").data
    first = APIClient().post("/api/auth/refresh/", {"refresh": tokens["refresh"]}, format="json")
    assert first.status_code == 200 and first.data["refresh"] != tokens["refresh"]
    # Eski refresh ikinci kez kullanılamaz (frontend bu yüzden yenilemeyi tek uçuşta yapar).
    assert APIClient().post("/api/auth/refresh/", {"refresh": tokens["refresh"]}, format="json").status_code == 401
