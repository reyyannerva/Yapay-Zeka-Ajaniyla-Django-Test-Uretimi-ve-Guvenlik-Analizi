from django.db import models
from django.db.models import Q

from ..choices import SHA256_HEX_REGEX, values
from .analysis import AnalysisRun
from .endpoint import Endpoint
from .execution import TestExecution


class FindingSource(models.TextChoices):
    AUTH_TEST = "AUTH_TEST", "Yetkilendirme testi"
    BANDIT = "BANDIT", "Bandit"
    CHECK_DEPLOY = "CHECK_DEPLOY", "manage.py check --deploy"


class Severity(models.TextChoices):
    HIGH = "HIGH", "Yüksek"
    MEDIUM = "MEDIUM", "Orta"
    LOW = "LOW", "Düşük"
    UNKNOWN = "UNKNOWN", "Bilinmiyor"


class FindingClassification(models.TextChoices):
    VERIFIED = "VERIFIED", "Doğrulanmış"
    POSSIBLE = "POSSIBLE", "Olası"
    UNCERTAIN = "UNCERTAIN", "Belirsiz"


class SecurityFinding(models.Model):
    """Güvenlik bulgusu (veri sözlüğü 4.7, 13.4). Analiz edilen projedeki gizli değerler saklanmaz."""

    Source = FindingSource
    Severity = Severity
    Classification = FindingClassification

    id = models.BigAutoField(primary_key=True)
    # İndeks uq_security_findings_run_fingerprint ile sağlanır.
    analysis_run = models.ForeignKey(
        AnalysisRun, on_delete=models.CASCADE, related_name="security_findings", db_index=False
    )
    # Bulguyu kanıtlayan yürütme; aynı çalıştırmaya ait olmalı (uygulama kuralı).
    test_execution = models.ForeignKey(
        TestExecution, on_delete=models.SET_NULL, null=True, blank=True, related_name="security_findings",
        db_index=False,
    )
    endpoint = models.ForeignKey(
        Endpoint, on_delete=models.SET_NULL, null=True, blank=True, related_name="security_findings", db_index=False
    )
    source = models.CharField(max_length=20, choices=FindingSource.choices)
    rule_id = models.CharField(max_length=100)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    classification = models.CharField(
        max_length=20, choices=FindingClassification.choices, default=FindingClassification.POSSIBLE
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    file_path = models.CharField(max_length=500, blank=True, default="")
    line_number = models.IntegerField(null=True, blank=True)
    # Maskelenmiş kanıt kesiti.
    evidence_excerpt = models.CharField(max_length=1000, blank=True, default="")
    recommendation_key = models.CharField(max_length=50, null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    fingerprint = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "security_findings"
        ordering = ["analysis_run_id", "-created_at"]
        indexes = [
            models.Index(fields=["analysis_run", "severity"], name="ix_finding_run_severity"),
            models.Index(fields=["test_execution"], name="ix_finding_execution"),
            models.Index(fields=["endpoint"], name="ix_finding_endpoint"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["analysis_run", "fingerprint"], name="uq_security_findings_run_fingerprint"),
            models.CheckConstraint(
                condition=Q(source__in=values(FindingSource)), name="ck_security_findings_source_valid"
            ),
            models.CheckConstraint(
                condition=Q(severity__in=values(Severity)), name="ck_security_findings_severity_valid"
            ),
            models.CheckConstraint(
                condition=Q(classification__in=values(FindingClassification)),
                name="ck_security_findings_classification_valid",
            ),
            models.CheckConstraint(condition=~Q(rule_id=""), name="ck_security_findings_rule_id_not_blank"),
            models.CheckConstraint(condition=~Q(title=""), name="ck_security_findings_title_not_blank"),
            models.CheckConstraint(
                condition=~Q(file_path__startswith="/") & ~Q(file_path__contains=".."),
                name="ck_security_findings_file_path_relative",
            ),
            models.CheckConstraint(
                condition=Q(line_number__isnull=True) | Q(line_number__gte=1),
                name="ck_security_findings_line_number_positive",
            ),
            models.CheckConstraint(
                condition=Q(fingerprint__regex=SHA256_HEX_REGEX), name="ck_security_findings_fingerprint_format"
            ),
        ]

    def __str__(self) -> str:
        return f"[{self.severity}] {self.rule_id}: {self.title}"
