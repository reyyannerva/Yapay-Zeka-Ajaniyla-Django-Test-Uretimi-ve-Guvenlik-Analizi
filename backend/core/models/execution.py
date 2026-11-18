from django.db import models
from django.db.models import F, Q

from ..choices import values
from .generation import GeneratedTest


class ExecutionStatus(models.TextChoices):
    """Test yürütme durumları.

    Issue #33: PENDING, RUNNING, PASS, FAIL, ERROR, TIMEOUT. Kanonik revizyon 3'teki QUEUED → PENDING ve
    TECHNICAL_ERROR → ERROR olarak yeniden adlandırılmış, TIMEOUT ayrı bir durum olmuştur. İptal ekranı
    (Figma 29) için kanonik STOPPED ve NOT_RUN korunmuştur (docs/database/schema_changes_h4_01.md).
    """

    PENDING = "PENDING", "Bekliyor"
    RUNNING = "RUNNING", "Çalışıyor"
    PASS = "PASS", "Geçti"
    FAIL = "FAIL", "Başarısız"
    ERROR = "ERROR", "Teknik hata"
    TIMEOUT = "TIMEOUT", "Zaman aşımı"
    STOPPED = "STOPPED", "Durduruldu"
    NOT_RUN = "NOT_RUN", "Çalıştırılmadı"


class ErrorType(models.TextChoices):
    IMPORT = "IMPORT", "İçe aktarma hatası"
    FIXTURE = "FIXTURE", "Fixture hatası"
    SYNTAX = "SYNTAX", "Sözdizimi hatası"
    TIMEOUT = "TIMEOUT", "Zaman aşımı"
    OOM = "OOM", "Bellek aşımı"
    OTHER = "OTHER", "Diğer"


class ErrorOrigin(models.TextChoices):
    TEST_CODE = "TEST_CODE", "Üretilen test kodu"
    TARGET_APP = "TARGET_APP", "Hedef uygulama"
    INFRASTRUCTURE = "INFRASTRUCTURE", "Altyapı"


#: Sonuçlanmış (ilerleme hesabında "tamamlanan") durumlar; bu durumdaki deneme değiştirilmez.
TERMINAL_EXECUTION_STATUSES = ["PASS", "FAIL", "ERROR", "TIMEOUT", "STOPPED", "NOT_RUN"]
#: finished_at zorunlu olan durumlar (NOT_RUN hiç başlamadığı için hariç).
FINISHED_EXECUTION_STATUSES = ["PASS", "FAIL", "ERROR", "TIMEOUT", "STOPPED"]
#: Sonuç üreten (başlamış olması gereken) durumlar.
OUTCOME_EXECUTION_STATUSES = ["PASS", "FAIL", "TIMEOUT"]


class TestExecution(models.Model):
    """Üretilen bir testin tek yürütme denemesi (veri sözlüğü 4.6, 9.2).

    Analiz çalıştırması ``generated_test.analysis_run`` üzerinden türetilir (veri sözlüğü 6.2).
    """

    __test__ = False  # pytest'in sınıfı test olarak toplamasını engeller

    Status = ExecutionStatus
    ErrorType = ErrorType
    ErrorOrigin = ErrorOrigin
    TERMINAL_STATUSES = TERMINAL_EXECUTION_STATUSES

    id = models.BigAutoField(primary_key=True)
    # İndeks uq_test_executions_test_attempt ile sağlanır.
    generated_test = models.ForeignKey(
        GeneratedTest, on_delete=models.CASCADE, related_name="executions", db_index=False
    )
    attempt_number = models.IntegerField()
    status = models.CharField(max_length=20, choices=ExecutionStatus.choices, default=ExecutionStatus.PENDING)
    observed_status = models.SmallIntegerField(null=True, blank=True)
    error_type = models.CharField(max_length=20, choices=ErrorType.choices, null=True, blank=True)
    error_origin = models.CharField(max_length=20, choices=ErrorOrigin.choices, null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)
    # Maskelenmiş çıktı özeti; tam log veritabanında tutulmaz.
    output_excerpt = models.CharField(max_length=10000, blank=True, default="")
    error_summary = models.CharField(max_length=2000, blank=True, default="")
    result_details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "test_executions"
        ordering = ["generated_test_id", "attempt_number"]
        constraints = [
            models.UniqueConstraint(fields=["generated_test", "attempt_number"], name="uq_test_executions_test_attempt"),
            models.CheckConstraint(
                condition=Q(status__in=values(ExecutionStatus)), name="ck_test_executions_status_valid"
            ),
            models.CheckConstraint(
                condition=Q(observed_status__isnull=True) | Q(observed_status__gte=100, observed_status__lte=599),
                name="ck_test_executions_observed_status_range",
            ),
            models.CheckConstraint(
                condition=Q(error_type__isnull=True) | Q(error_type__in=values(ErrorType)),
                name="ck_test_executions_error_type_valid",
            ),
            models.CheckConstraint(
                condition=Q(error_origin__isnull=True) | Q(error_origin__in=values(ErrorOrigin)),
                name="ck_test_executions_error_origin_valid",
            ),
            # ERROR'da hata türü zorunlu ve TIMEOUT dışında bir tür olmalı.
            models.CheckConstraint(
                condition=~Q(status="ERROR") | (Q(error_type__isnull=False) & ~Q(error_type="TIMEOUT")),
                name="ck_test_executions_error_has_type",
            ),
            # TIMEOUT durumu ile TIMEOUT hata türü birlikte bulunur (belirsizlik yok).
            models.CheckConstraint(
                # error_type__isnull=False: NULL karşılaştırması CHECK'i "bilinmiyor" ile geçirmesin.
                condition=Q(status="TIMEOUT", error_type__isnull=False, error_type="TIMEOUT")
                | (~Q(status="TIMEOUT") & (Q(error_type__isnull=True) | ~Q(error_type="TIMEOUT"))),
                name="ck_test_executions_timeout_consistent",
            ),
            models.CheckConstraint(condition=Q(attempt_number__gte=1), name="ck_test_executions_attempt_positive"),
            models.CheckConstraint(
                condition=Q(duration_ms__isnull=True) | Q(duration_ms__gte=0),
                name="ck_test_executions_duration_non_negative",
            ),
            models.CheckConstraint(
                condition=~Q(status="PENDING") | Q(started_at__isnull=True, finished_at__isnull=True),
                name="ck_test_executions_pending_not_started",
            ),
            models.CheckConstraint(
                condition=~Q(status="NOT_RUN") | Q(started_at__isnull=True, finished_at__isnull=True),
                name="ck_test_executions_not_run_not_started",
            ),
            models.CheckConstraint(
                condition=~Q(status="RUNNING") | Q(started_at__isnull=False, finished_at__isnull=True),
                name="ck_test_executions_running_started",
            ),
            models.CheckConstraint(
                condition=~Q(status__in=FINISHED_EXECUTION_STATUSES) | Q(finished_at__isnull=False),
                name="ck_test_executions_terminal_finished",
            ),
            # PASS/FAIL/TIMEOUT bir pytest sürecinin başlamış olmasını gerektirir.
            models.CheckConstraint(
                condition=~Q(status__in=OUTCOME_EXECUTION_STATUSES) | Q(started_at__isnull=False),
                name="ck_test_executions_outcome_requires_start",
            ),
            models.CheckConstraint(
                condition=Q(started_at__isnull=True) | Q(finished_at__isnull=True) | Q(finished_at__gte=F("started_at")),
                name="ck_test_executions_time_order",
            ),
            models.CheckConstraint(
                condition=Q(duration_ms__isnull=True) | Q(finished_at__isnull=False),
                name="ck_test_executions_duration_requires_finish",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.generated_test} deneme {self.attempt_number}: {self.status}"

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_EXECUTION_STATUSES
