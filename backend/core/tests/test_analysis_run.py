from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from core.models import AnalysisRun

from .conftest import assert_integrity, at, make_project, make_run

pytestmark = pytest.mark.django_db

ISSUE_33_STATUSES = ["QUEUED", "ANALYZING", "GENERATING", "EXECUTING", "COMPLETED", "FAILED"]


def times_for(status):
    """Durum için kısıtları sağlayan asgari zaman ve hata alanları."""
    kw = {}
    if status not in ("QUEUED", "FAILED", "CANCELLED"):
        kw["started_at"] = at(0)
    if status in AnalysisRun.TERMINAL_STATUSES:
        kw["finished_at"] = at(60)
    if status == "FAILED":
        kw["error_code"] = "SANDBOX_TIMEOUT"
    return kw


def test_defaults(project):
    r = make_run(project)
    r.refresh_from_db()
    assert r.status == "QUEUED" and r.celery_task_id is None
    assert (r.started_at, r.finished_at) == (None, None)
    assert (r.requirements_snapshot, r.ast_results, r.processing_metadata) == ([], {}, {})
    assert r.fallback_enabled is True and r.created_at and r.updated_at


def test_issue_33_statuses_are_present_exactly():
    assert set(ISSUE_33_STATUSES) <= set(AnalysisRun.Status.values)
    assert [s for s in AnalysisRun.Status.values if s not in ISSUE_33_STATUSES] == ["VALIDATING", "SCANNING",
                                                                                     "CANCELLED"]


@pytest.mark.parametrize("status", AnalysisRun.Status.values)
def test_every_status_can_be_stored(user, status):
    r = make_run(make_project(user), status=status, **times_for(status))
    assert AnalysisRun.objects.get(pk=r.pk).status == status


@pytest.mark.parametrize("status", ["DONE", "queued", "RUNNING", ""])
def test_invalid_status_rejected_by_db_and_model(project, status):
    assert_integrity(lambda: make_run(project, status=status), "ck_analysis_runs_status_valid")
    with pytest.raises(ValidationError):
        AnalysisRun(project=project, method="RULE_BASED", status=status).full_clean()


def test_celery_task_id_stored_and_unique_when_present(user):
    p1, p2 = make_project(user), make_project(user)
    make_run(p1, celery_task_id="6f1c2b8e-0d4a-4c1e-9a55-1b2f7a9e0c11")
    assert AnalysisRun.objects.get(celery_task_id="6f1c2b8e-0d4a-4c1e-9a55-1b2f7a9e0c11").project == p1
    assert_integrity(lambda: make_run(p2, celery_task_id="6f1c2b8e-0d4a-4c1e-9a55-1b2f7a9e0c11"),
                     "uq_analysis_runs_celery_task_id")
    # NULL değerler birden fazla satırda bulunabilir (henüz kuyruğa gönderilmemiş).
    make_run(p2, status="COMPLETED", started_at=at(0), finished_at=at(1))
    assert AnalysisRun.objects.filter(celery_task_id__isnull=True).count() == 1


def test_only_one_active_run_per_project(project):
    make_run(project)
    assert_integrity(lambda: make_run(project, status="ANALYZING", started_at=at(0)),
                     "uq_analysis_runs_one_active_per_project")
    make_run(project, status="COMPLETED", started_at=at(0), finished_at=at(5))  # bitmiş çalıştırmalar serbest


@pytest.mark.parametrize("kw,constraint", [
    ({"status": "QUEUED", "started_at": at(0)}, "ck_analysis_runs_queued_not_started"),
    ({"status": "EXECUTING"}, "ck_analysis_runs_progress_requires_start"),
    ({"status": "COMPLETED", "started_at": at(0)}, "ck_analysis_runs_finished_iff_terminal"),
    ({"status": "ANALYZING", "started_at": at(0), "finished_at": at(1)}, "ck_analysis_runs_finished_iff_terminal"),
    ({"status": "COMPLETED", "started_at": at(10), "finished_at": at(5)}, "ck_analysis_runs_time_order"),
    ({"status": "FAILED", "finished_at": at(5)}, "ck_analysis_runs_failure_has_error_code"),
])
def test_timestamp_and_state_consistency(project, kw, constraint):
    assert_integrity(lambda: make_run(project, **kw), constraint)


def test_failed_before_start_is_allowed(project):
    r = make_run(project, status="FAILED", finished_at=at(1), error_code="INVALID_ARCHIVE",
                 error_message="Arşiv açılamadı")
    assert r.started_at is None and r.error_code == "INVALID_ARCHIVE"


def test_lifecycle_updates(project):
    r = make_run(project, celery_task_id="t-1")
    for status in ["ANALYZING", "GENERATING", "EXECUTING"]:
        r.status, r.started_at = status, at(0)
        r.save()
    r.status, r.finished_at, r.coverage_percent = "COMPLETED", at(120), Decimal("87.50")
    r.save()
    r.refresh_from_db()
    assert (r.status, r.finished_at - r.started_at, r.coverage_percent) == ("COMPLETED", at(120) - at(0),
                                                                           Decimal("87.50"))


@pytest.mark.parametrize("kw,constraint", [
    ({"method": "MAGIC", "llm_provider": "GROQ", "llm_model": "m"}, "ck_analysis_runs_method_valid"),
    ({"method": "RULE_BASED", "llm_provider": "GROQ", "llm_model": "m"}, "ck_analysis_runs_llm_settings"),
    ({"method": "DIRECT_LLM"}, "ck_analysis_runs_llm_settings"),
    ({"method": "DIRECT_LLM", "llm_provider": "GROQ", "llm_model": ""}, "ck_analysis_runs_llm_settings"),
    ({"method": "DIRECT_LLM", "llm_provider": "OPENAI", "llm_model": "m"}, "ck_analysis_runs_llm_provider_valid"),
    ({"coverage_percent": Decimal("100.01")}, "ck_analysis_runs_coverage_range"),
])
def test_method_and_model_settings(project, kw, constraint):
    assert_integrity(lambda: make_run(project, **kw), constraint)


def test_llm_run_and_json_metadata_round_trip(project):
    meta = {"schema_version": 1, "stage_durations_ms": {"analyzing": 4120}, "counts": {"generated_tests": 14}}
    snapshot = [{"requirement_code": "ACC-1", "revision": 2, "specification": {"method": "DELETE"}}]
    ast = {"schema_version": 1, "views": [{"http_methods": ["GET", "POST"]}], "parse_errors": []}
    r = make_run(project, method="HYBRID", llm_provider="GROQ", llm_model="llama-3.3-70b-versatile",
                 processing_metadata=meta, requirements_snapshot=snapshot, ast_results=ast)
    got = AnalysisRun.objects.get(pk=r.pk)
    assert (got.processing_metadata, got.requirements_snapshot, got.ast_results) == (meta, snapshot, ast)
    assert AnalysisRun.objects.filter(processing_metadata__counts__generated_tests=14).get() == got
