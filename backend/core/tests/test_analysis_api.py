"""AnalysisRun API testleri — H4-04 / Issue #36."""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import AnalysisRun

from .conftest import make_execution, make_project, make_requirement, make_run, make_test

pytestmark = pytest.mark.django_db

LIST = reverse("analysis-run-list")


def detail(pk):
    return reverse("analysis-run-detail", args=[pk])


@pytest.fixture
def api(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# --- Oluşturma ---
def test_create_rule_based_queued(api, project):
    resp = api.post(LIST, {"project": project.id, "method": "RULE_BASED"}, format="json")
    assert resp.status_code == 201
    assert resp.data["status"] == "QUEUED"
    assert resp.data["celery_task_id"] is None  # gerçek görev başlatılmaz
    assert AnalysisRun.objects.filter(project=project, status="QUEUED").count() == 1


def test_create_llm_requires_provider_and_model(api, project):
    resp = api.post(LIST, {"project": project.id, "method": "DIRECT_LLM"}, format="json")
    assert resp.status_code == 400


def test_create_llm_with_provider_and_model(api, project):
    resp = api.post(LIST, {"project": project.id, "method": "DIRECT_LLM",
                           "llm_provider": "GROQ", "llm_model": "llama"}, format="json")
    assert resp.status_code == 201 and resp.data["llm_provider"] == "GROQ"


def test_create_rule_based_rejects_llm_fields(api, project):
    resp = api.post(LIST, {"project": project.id, "method": "RULE_BASED", "llm_provider": "GROQ"}, format="json")
    assert resp.status_code == 400


def test_create_rejects_other_users_project(api, django_user_model):
    others = make_project(django_user_model.objects.create_user(username="o1", password="x"))
    resp = api.post(LIST, {"project": others.id, "method": "RULE_BASED"}, format="json")
    assert resp.status_code == 400  # queryset dışı; varlık ifşa edilmez


def test_create_rejects_second_active_run(api, project):
    assert api.post(LIST, {"project": project.id, "method": "RULE_BASED"}, format="json").status_code == 201
    resp = api.post(LIST, {"project": project.id, "method": "RULE_BASED"}, format="json")
    assert resp.status_code == 400  # proje başına tek aktif analiz


def test_create_snapshots_active_requirements(api, project):
    make_requirement(project, requirement_code="ACC-SNAP")
    resp = api.post(LIST, {"project": project.id, "method": "RULE_BASED"}, format="json")
    run = AnalysisRun.objects.get(id=resp.data["id"])
    assert any(r["requirement_code"] == "ACC-SNAP" for r in run.requirements_snapshot)


# --- Listeleme / detay / sahiplik ---
def test_list_only_own_runs(api, user, project, django_user_model):
    mine = make_run(project)
    others = make_run(make_project(django_user_model.objects.create_user(username="o2", password="x")))
    ids = {r["id"] for r in api.get(LIST).data}
    assert mine.id in ids and others.id not in ids


def test_detail_has_progress_without_misleading_zero(api, project):
    run = make_run(project)  # yürütme kaydı yok
    resp = api.get(detail(run.id))
    assert resp.status_code == 200
    assert resp.data["progress"]["total"] == 0
    assert resp.data["progress"]["percent"] is None  # yanıltıcı %0 değil
    assert "requirements_snapshot" in resp.data


def test_detail_progress_counts_executions(api, project):
    run = make_run(project)
    make_execution(make_test(run))  # bir yürütme (PENDING)
    resp = api.get(detail(run.id))
    assert resp.data["progress"]["total"] == 1


def test_retrieve_others_run_404(api, django_user_model):
    others = make_run(make_project(django_user_model.objects.create_user(username="o3", password="x")))
    assert api.get(detail(others.id)).status_code == 404


def test_requires_authentication(project):
    anon = APIClient()
    assert anon.get(LIST).status_code == 401
    assert anon.post(LIST, {"project": project.id, "method": "RULE_BASED"}, format="json").status_code == 401
