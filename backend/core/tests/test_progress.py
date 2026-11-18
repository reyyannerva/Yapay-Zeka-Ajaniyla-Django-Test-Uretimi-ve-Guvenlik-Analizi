import pytest

from core.progress import execution_progress

from .conftest import at, make_execution, make_run, make_test

pytestmark = pytest.mark.django_db


def test_no_executions_is_not_zero_percent(run):
    p = execution_progress(run)
    assert (p.total, p.completed, p.percent) == (0, 0, None)


def test_progress_counts_latest_attempt_per_test(project):
    run = make_run(project, status="EXECUTING", started_at=at(0))
    t1, t2, t3, t4 = (make_test(run) for _ in range(4))
    make_execution(t1, status="PASS", started_at=at(0), finished_at=at(2), duration_ms=2000)
    make_execution(t2, status="ERROR", started_at=at(0), finished_at=at(1), duration_ms=500, error_type="IMPORT")
    make_execution(t2, attempt_number=2, status="RUNNING", started_at=at(3))   # düzeltilip yeniden çalışıyor
    make_execution(t3, status="TIMEOUT", started_at=at(0), finished_at=at(60), duration_ms=60000,
                   error_type="TIMEOUT")
    make_execution(t4)                                                          # PENDING
    make_test(run)                                                              # henüz kuyruğa alınmamış
    p = execution_progress(run)
    assert (p.total, p.completed, p.running, p.pending) == (4, 2, 1, 1)
    assert p.by_status == {"PASS": 1, "PENDING": 1, "RUNNING": 1, "TIMEOUT": 1}
    assert (p.completed_duration_ms_total, p.completed_with_duration) == (62000, 2)
    assert p.percent == 50.0 and p.run_started_at == at(0)


def test_progress_is_scoped_to_run(user):
    from .conftest import make_project
    a, b = make_run(make_project(user)), make_run(make_project(user))
    make_execution(make_test(a), status="PASS", started_at=at(0), finished_at=at(1))
    assert execution_progress(b).total == 0 and execution_progress(a).completed == 1
