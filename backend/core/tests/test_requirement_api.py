"""ReferenceRequirement API testleri — H4-04 / Issue #36."""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import ReferenceRequirement

from .conftest import make_project, make_requirement

pytestmark = pytest.mark.django_db

LIST = reverse("reference-requirement-list")


def detail(pk):
    return reverse("reference-requirement-detail", args=[pk])


def access_rule_payload(project, code="ACC-1", method="DELETE"):
    return {
        "project": project.id,
        "requirement_code": code,
        "category": "ACCESS_RULE",
        "title": "Sipariş silme",
        "expected_result": "anonim 401, staff 204",
        "specification": {
            "schema_version": 1, "endpoint": "/api/orders/<int:pk>/", "method": method,
            "expected_status_by_role": {"anonymous": 401, "staff": 204},
        },
    }


@pytest.fixture
def api(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# --- Oluşturma / doğrulama ---
def test_create_access_rule_201(api, project):
    assert api.post(LIST, access_rule_payload(project), format="json").status_code == 201


def test_all_five_http_methods_accepted(api, project):
    for i, method in enumerate(["GET", "POST", "PUT", "PATCH", "DELETE"]):
        resp = api.post(LIST, access_rule_payload(project, code=f"ACC-{i}", method=method), format="json")
        assert resp.status_code == 201, (method, resp.data)


def test_rejects_unsupported_http_method(api, project):
    resp = api.post(LIST, access_rule_payload(project, method="HEAD"), format="json")
    assert resp.status_code == 400 and "specification" in resp.data


def test_rejects_invalid_specification_type(api, project):
    payload = access_rule_payload(project)
    payload["specification"] = "metin"  # JSON nesnesi değil
    assert api.post(LIST, payload, format="json").status_code == 400


def test_missing_required_field_400(api, project):
    payload = access_rule_payload(project)
    del payload["title"]
    assert api.post(LIST, payload, format="json").status_code == 400


def test_duplicate_code_same_project_rejected(api, project):
    assert api.post(LIST, access_rule_payload(project, code="ACC-DUP"), format="json").status_code == 201
    resp = api.post(LIST, access_rule_payload(project, code="ACC-DUP"), format="json")
    assert resp.status_code == 400  # (project, requirement_code) benzersiz


def test_create_rejects_other_users_project(api, django_user_model):
    others = make_project(django_user_model.objects.create_user(username="r1", password="x"))
    assert api.post(LIST, access_rule_payload(others), format="json").status_code == 400


# --- CRUD / revizyon / sahiplik ---
def test_list_only_own(api, project, django_user_model):
    mine = make_requirement(project, requirement_code="MINE-1")
    others = make_requirement(make_project(django_user_model.objects.create_user(username="r2", password="x")),
                              requirement_code="OTHER-1")
    codes = {r["requirement_code"] for r in api.get(LIST).data}
    assert "MINE-1" in codes and "OTHER-1" not in codes


def test_update_increments_revision(api, project):
    req = make_requirement(project, requirement_code="UPD-1")
    assert req.revision == 1
    payload = access_rule_payload(project, code="UPD-1")
    payload["title"] = "Güncellendi"
    resp = api.put(detail(req.id), payload, format="json")
    assert resp.status_code == 200
    req.refresh_from_db()
    assert req.title == "Güncellendi" and req.revision == 2


def test_patch_updates(api, project):
    req = make_requirement(project, requirement_code="PAT-1")
    resp = api.patch(detail(req.id), {"title": "Yeni başlık"}, format="json")
    assert resp.status_code == 200
    req.refresh_from_db()
    assert req.title == "Yeni başlık"


def test_delete_204(api, project):
    req = make_requirement(project, requirement_code="DEL-1")
    assert api.delete(detail(req.id)).status_code == 204
    assert not ReferenceRequirement.objects.filter(id=req.id).exists()


def test_others_requirement_404(api, django_user_model):
    others = make_requirement(make_project(django_user_model.objects.create_user(username="r3", password="x")),
                              requirement_code="OTH-1")
    assert api.get(detail(others.id)).status_code == 404
    assert api.delete(detail(others.id)).status_code == 404


def test_requires_authentication(project):
    assert APIClient().get(LIST).status_code == 401
