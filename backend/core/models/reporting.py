from django.db import models
from django.db.models import Q

from ..choices import values
from .analysis import AnalysisRun


class ReportFormat(models.TextChoices):
    PDF = "PDF", "PDF"
    JSON = "JSON", "JSON"


class ReportScope(models.TextChoices):
    FULL = "FULL", "Tam"
    PARTIAL = "PARTIAL", "Kısmi"


class Report(models.Model):
    """Dışa aktarılmış rapor dosyası (veri sözlüğü 4.9). Dosyanın silinmesi uygulamanın sorumluluğundadır."""

    Format = ReportFormat
    Scope = ReportScope

    id = models.BigAutoField(primary_key=True)
    # İndeks ix_report_run_created ile sağlanır.
    analysis_run = models.ForeignKey(AnalysisRun, on_delete=models.CASCADE, related_name="reports", db_index=False)
    format = models.CharField(max_length=10, choices=ReportFormat.choices)
    # FAILED ve CANCELLED çalıştırmalar için PARTIAL (uygulama kuralı).
    scope = models.CharField(max_length=10, choices=ReportScope.choices)
    sections = models.JSONField(default=list, blank=True)
    file_path = models.CharField(max_length=500)
    file_size_bytes = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reports"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["analysis_run", "-created_at"], name="ix_report_run_created")]
        constraints = [
            models.CheckConstraint(condition=Q(format__in=values(ReportFormat)), name="ck_reports_format_valid"),
            models.CheckConstraint(condition=Q(scope__in=values(ReportScope)), name="ck_reports_scope_valid"),
            models.CheckConstraint(
                condition=~Q(file_path="") & ~Q(file_path__startswith="/") & ~Q(file_path__contains=".."),
                name="ck_reports_file_path_relative",
            ),
            models.CheckConstraint(condition=Q(file_size_bytes__gte=0), name="ck_reports_file_size_non_negative"),
        ]

    def __str__(self) -> str:
        return f"Report #{self.pk} ({self.format}, {self.scope})"
