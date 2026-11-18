"""AnalysisRun test ilerlemesinin TestExecution kayıtlarından türetilmesi — H4-01 / Issue #33.

Sayaçlar ayrı ve değiştirilebilir alanlar olarak **saklanmaz**; eşzamanlı yürütmelerde tutarsızlık
riskini önlemek için her sorguda ``test_executions`` tablosundan türetilir.

Tanımlar:

* Bir testin durumu, o testin **en yüksek ``attempt_number``'lı** yürütme denemesinin durumudur.
* ``total``     — çalıştırmanın en az bir yürütme kaydı olan testleri (deneme kuyruğa alınırken PENDING
  olarak oluşturulur).
* ``completed`` — son denemesi sonuçlanmış testler: PASS, FAIL, ERROR, TIMEOUT, STOPPED, NOT_RUN.
* ``running``   — son denemesi RUNNING olan testler; ``pending`` — son denemesi PENDING olan testler.

Tahmini kalan süre algoritması bu issue'nun kapsamında değildir; yalnızca girdi verisi
(tamamlanan testlerin ``duration_ms`` toplamı/sayısı, çalıştırmanın ``started_at`` değeri) sağlanır.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime

from .models import AnalysisRun, TestExecution
from .models.execution import TERMINAL_EXECUTION_STATUSES


@dataclass(frozen=True)
class ExecutionProgress:
    total: int
    completed: int
    running: int
    pending: int
    by_status: dict[str, int] = field(default_factory=dict)
    completed_duration_ms_total: int = 0
    completed_with_duration: int = 0
    run_started_at: datetime | None = None

    @property
    def percent(self) -> float | None:
        """Tamamlanma yüzdesi; henüz yürütme kaydı yoksa ``None`` (0 ile doldurulmaz)."""
        return None if self.total == 0 else round(100 * self.completed / self.total, 2)

    def as_dict(self) -> dict:
        data = asdict(self)
        data["percent"] = self.percent
        return data


def latest_executions(run: AnalysisRun):
    """Çalıştırmadaki her testin son yürütme denemesi (PostgreSQL ``DISTINCT ON``)."""
    return (
        TestExecution.objects.filter(generated_test__analysis_run=run)
        .order_by("generated_test_id", "-attempt_number")
        .distinct("generated_test_id")
    )


def execution_progress(run: AnalysisRun) -> ExecutionProgress:
    latest = list(latest_executions(run).only("status", "duration_ms"))
    statuses = Counter(e.status for e in latest)
    done = [e for e in latest if e.status in TERMINAL_EXECUTION_STATUSES]
    durations = [e.duration_ms for e in done if e.duration_ms is not None]
    return ExecutionProgress(
        total=len(latest),
        completed=len(done),
        running=statuses.get(TestExecution.Status.RUNNING, 0),
        pending=statuses.get(TestExecution.Status.PENDING, 0),
        by_status=dict(sorted(statuses.items())),
        completed_duration_ms_total=sum(durations),
        completed_with_duration=len(durations),
        run_started_at=run.started_at,
    )
