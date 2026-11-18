import pytest
from django.core.exceptions import ValidationError

from core.models import TestExecution

from .conftest import assert_integrity, at, make_execution, make_test

pytestmark = pytest.mark.django_db

ISSUE_33_STATUSES = ["PENDING", "RUNNING", "PASS", "FAIL", "ERROR", "TIMEOUT"]

VALID_ROWS = {
    "PENDING": {},
    "RUNNING": {"started_at": at(0)},
    "PASS": {"started_at": at(0), "finished_at": at(2), "duration_ms": 2000, "observed_status": 200},
    "FAIL": {"started_at": at(0), "finished_at": at(1), "duration_ms": 1000, "observed_status": 200,
             "error_summary": "assert 200 == 403"},
    "ERROR": {"started_at": at(0), "finished_at": at(1), "error_type": "IMPORT", "error_origin": "TEST_CODE"},
    "TIMEOUT": {"started_at": at(0), "finished_at": at(60), "duration_ms": 60000, "error_type": "TIMEOUT",
                "error_origin": "INFRASTRUCTURE"},
    "STOPPED": {"started_at": at(0), "finished_at": at(3)},
    "NOT_RUN": {},
}


@pytest.fixture
def gtest(run):
    return make_test(run)


def test_issue_33_statuses_present_and_default_pending(gtest):
    assert set(ISSUE_33_STATUSES) <= set(TestExecution.Status.values)
    e = make_execution(gtest)
    e.refresh_from_db()
    assert e.status == "PENDING" and (e.started_at, e.finished_at, e.duration_ms) == (None, None, None)
    assert e.created_at is not None


@pytest.mark.parametrize("status", list(VALID_ROWS))
def test_every_status_with_consistent_timing(gtest, status):
    e = make_execution(gtest, status=status, **VALID_ROWS[status])
    got = TestExecution.objects.get(pk=e.pk)
    assert got.status == status and got.generated_test == gtest
    assert got.generated_test.analysis_run == gtest.analysis_run  # çalıştırma ilişkisi FK zinciriyle türetilir
    got.full_clean()


@pytest.mark.parametrize("status", ["QUEUED", "TECHNICAL_ERROR", "pass", "SKIPPED"])
def test_invalid_status_rejected(gtest, status):
    assert_integrity(lambda: make_execution(gtest, status=status), "ck_test_executions_status_valid")
    with pytest.raises(ValidationError):
        TestExecution(generated_test=gtest, attempt_number=1, status=status).full_clean()


@pytest.mark.parametrize("status,kw,constraint", [
    ("PENDING", {"started_at": at(0)}, "ck_test_executions_pending_not_started"),
    ("NOT_RUN", {"finished_at": at(0)}, "ck_test_executions_not_run_not_started"),
    ("RUNNING", {}, "ck_test_executions_running_started"),
    ("RUNNING", {"started_at": at(0), "finished_at": at(1)}, "ck_test_executions_running_started"),
    ("PASS", {"started_at": at(0)}, "ck_test_executions_terminal_finished"),
    ("FAIL", {"finished_at": at(1)}, "ck_test_executions_outcome_requires_start"),
    ("TIMEOUT", {"finished_at": at(1), "error_type": "TIMEOUT"}, "ck_test_executions_outcome_requires_start"),
    ("PASS", {"started_at": at(5), "finished_at": at(1)}, "ck_test_executions_time_order"),
    ("RUNNING", {"started_at": at(0), "duration_ms": 5}, "ck_test_executions_duration_requires_finish"),
    ("PASS", {"started_at": at(0), "finished_at": at(1), "duration_ms": -1}, "ck_test_executions_duration_non_negative"),
])
def test_timing_constraints(gtest, status, kw, constraint):
    assert_integrity(lambda: make_execution(gtest, status=status, **kw), constraint)


@pytest.mark.parametrize("kw,constraint", [
    ({"status": "ERROR", "started_at": at(0), "finished_at": at(1)}, "ck_test_executions_error_has_type"),
    ({"status": "ERROR", "started_at": at(0), "finished_at": at(1), "error_type": "TIMEOUT"},
     "ck_test_executions_error_has_type"),
    ({"status": "TIMEOUT", "started_at": at(0), "finished_at": at(1)}, "ck_test_executions_timeout_consistent"),
    ({"status": "TIMEOUT", "started_at": at(0), "finished_at": at(1), "error_type": "OOM"},
     "ck_test_executions_timeout_consistent"),
    ({"status": "FAIL", "started_at": at(0), "finished_at": at(1), "error_type": "TIMEOUT"},
     "ck_test_executions_timeout_consistent"),
    ({"error_type": "PANIC"}, "ck_test_executions_error_type_valid"),
    ({"error_origin": "USER"}, "ck_test_executions_error_origin_valid"),
    ({"observed_status": 600}, "ck_test_executions_observed_status_range"),
    ({"attempt_number": 0}, "ck_test_executions_attempt_positive"),
])
def test_error_and_value_constraints(gtest, kw, constraint):
    assert_integrity(lambda: make_execution(gtest, **kw), constraint)


def test_attempt_number_unique_per_test_and_retry_creates_new_row(gtest):
    make_execution(gtest, status="ERROR", started_at=at(0), finished_at=at(1), error_type="IMPORT")
    assert_integrity(lambda: make_execution(gtest), "uq_test_executions_test_attempt")
    make_execution(gtest, attempt_number=2)
    assert list(gtest.executions.values_list("attempt_number", "status")) == [(1, "ERROR"), (2, "PENDING")]


def test_output_reference_fields_and_result_details_json(gtest):
    details = {"schema_version": 1, "pytest_outcome": "failed", "nodeid": "test_a.py::test_a",
               "assertion": {"expected": 403, "actual": 200}, "output_truncated": True}
    e = make_execution(gtest, status="FAIL", started_at=at(0), finished_at=at(1), duration_ms=950,
                       output_excerpt="E   assert 200 == 403", error_summary="assert 200 == 403",
                       result_details=details)
    got = TestExecution.objects.get(pk=e.pk)
    assert (got.output_excerpt, got.result_details, got.duration_ms) == ("E   assert 200 == 403", details, 950)


def test_requires_generated_test_and_cascades(gtest):
    assert_integrity(lambda: TestExecution.objects.create(attempt_number=1))
    make_execution(gtest)
    gtest.delete()
    assert not TestExecution.objects.exists()
