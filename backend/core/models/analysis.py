from django.db import models
from django.db.models import F, Q

from ..choices import values
from .project import Project


class AnalysisRunStatus(models.TextChoices):
    """Çalıştırma durumları (veri sözlüğü 8.1).

    Issue #33'ün altı durumu (QUEUED, ANALYZING, GENERATING, EXECUTING, COMPLETED, FAILED) birebir
    bulunur. VALIDATING, SCANNING ve CANCELLED kanonik revizyon 3'te Figma ekranları için eklenmiş
    durumlardır ve korunmuştur (docs/database/schema_changes_h4_01.md).
    """

    QUEUED = "QUEUED", "Kuyrukta"
    ANALYZING = "ANALYZING", "Analiz ediliyor"
    GENERATING = "GENERATING", "Test üretiliyor"
    VALIDATING = "VALIDATING", "Testler doğrulanıyor"
    EXECUTING = "EXECUTING", "Testler çalıştırılıyor"
    SCANNING = "SCANNING", "Güvenlik taraması"
    COMPLETED = "COMPLETED", "Tamamlandı"
    FAILED = "FAILED", "Başarısız"
    CANCELLED = "CANCELLED", "İptal edildi"


class AnalysisMethod(models.TextChoices):
    RULE_BASED = "RULE_BASED", "Kural tabanlı"
    DIRECT_LLM = "DIRECT_LLM", "Doğrudan LLM"
    HYBRID = "HYBRID", "Hibrit"


class LlmProvider(models.TextChoices):
    GROQ = "GROQ", "Groq"
    GEMINI = "GEMINI", "Gemini"
    OLLAMA = "OLLAMA", "Ollama"


ACTIVE_RUN_STATUSES = ["QUEUED", "ANALYZING", "GENERATING", "VALIDATING", "EXECUTING", "SCANNING"]
TERMINAL_RUN_STATUSES = ["COMPLETED", "FAILED", "CANCELLED"]
STARTED_RUN_STATUSES = ["ANALYZING", "GENERATING", "VALIDATING", "EXECUTING", "SCANNING", "COMPLETED"]


class AnalysisRun(models.Model):
    """Bir projenin tek analiz çalıştırması; Celery göreviyle eşlenir (veri sözlüğü 4.4, 8)."""

    Status = AnalysisRunStatus
    Method = AnalysisMethod
    LlmProvider = LlmProvider
    ACTIVE_STATUSES = ACTIVE_RUN_STATUSES
    TERMINAL_STATUSES = TERMINAL_RUN_STATUSES

    id = models.BigAutoField(primary_key=True)
    # İndeks ix_analysisrun_project_created ile sağlanır.
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="analysis_runs", db_index=False)
    status = models.CharField(max_length=20, choices=AnalysisRunStatus.choices, default=AnalysisRunStatus.QUEUED)
    method = models.CharField(max_length=20, choices=AnalysisMethod.choices)
    llm_provider = models.CharField(max_length=20, choices=LlmProvider.choices, null=True, blank=True)
    llm_model = models.CharField(max_length=100, null=True, blank=True)
    # Seçilen model erişilemezse kural tabanlı üretime düş (ekran 05).
    fallback_enabled = models.BooleanField(default=True)
    # Celery'ye gönderilene kadar NULL; doluyken tekil.
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)
    requirements_snapshot = models.JSONField(default=list, blank=True)
    ast_results = models.JSONField(default=dict, blank=True)
    processing_metadata = models.JSONField(default=dict, blank=True)
    coverage_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    error_code = models.CharField(max_length=50, blank=True, default="")
    error_message = models.CharField(max_length=2000, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analysis_runs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "-created_at"], name="ix_analysisrun_project_created"),
            models.Index(fields=["status", "created_at"], name="ix_analysisrun_status_created"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["celery_task_id"], name="uq_analysis_runs_celery_task_id"),
            models.UniqueConstraint(
                fields=["project"],
                condition=Q(status__in=ACTIVE_RUN_STATUSES),
                name="uq_analysis_runs_one_active_per_project",
            ),
            models.CheckConstraint(
                condition=Q(status__in=values(AnalysisRunStatus)), name="ck_analysis_runs_status_valid"
            ),
            models.CheckConstraint(
                condition=Q(method__in=values(AnalysisMethod)), name="ck_analysis_runs_method_valid"
            ),
            models.CheckConstraint(
                condition=Q(llm_provider__isnull=True) | Q(llm_provider__in=values(LlmProvider)),
                name="ck_analysis_runs_llm_provider_valid",
            ),
            models.CheckConstraint(
                condition=Q(method="RULE_BASED", llm_provider__isnull=True, llm_model__isnull=True)
                | (
                    ~Q(method="RULE_BASED")
                    & Q(llm_provider__isnull=False, llm_model__isnull=False)
                    & ~Q(llm_model="")
                ),
                name="ck_analysis_runs_llm_settings",
            ),
            models.CheckConstraint(
                condition=Q(coverage_percent__isnull=True) | Q(coverage_percent__gte=0, coverage_percent__lte=100),
                name="ck_analysis_runs_coverage_range",
            ),
            models.CheckConstraint(
                condition=~Q(status="QUEUED") | Q(started_at__isnull=True),
                name="ck_analysis_runs_queued_not_started",
            ),
            models.CheckConstraint(
                condition=~Q(status__in=STARTED_RUN_STATUSES) | Q(started_at__isnull=False),
                name="ck_analysis_runs_progress_requires_start",
            ),
            models.CheckConstraint(
                condition=Q(status__in=TERMINAL_RUN_STATUSES, finished_at__isnull=False)
                | (~Q(status__in=TERMINAL_RUN_STATUSES) & Q(finished_at__isnull=True)),
                name="ck_analysis_runs_finished_iff_terminal",
            ),
            models.CheckConstraint(
                condition=Q(started_at__isnull=True)
                | Q(finished_at__isnull=True)
                | Q(finished_at__gte=F("started_at")),
                name="ck_analysis_runs_time_order",
            ),
            models.CheckConstraint(
                condition=~Q(status="FAILED") | ~Q(error_code=""),
                name="ck_analysis_runs_failure_has_error_code",
            ),
        ]

    def __str__(self) -> str:
        return f"AnalysisRun #{self.pk} ({self.status})"

    @property
    def is_active(self) -> bool:
        return self.status in ACTIVE_RUN_STATUSES
