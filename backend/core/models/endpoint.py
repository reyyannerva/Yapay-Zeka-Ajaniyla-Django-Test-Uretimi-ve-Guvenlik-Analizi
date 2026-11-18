from django.db import models
from django.db.models import Q

from ..choices import HttpMethod, values
from .analysis import AnalysisRun


class UnsupportedReason(models.TextChoices):
    DYNAMIC_ROUTE = "DYNAMIC_ROUTE", "Dinamik rota"
    CUSTOM_PERMISSION = "CUSTOM_PERMISSION", "Özel izin sınıfı"


class Endpoint(models.Model):
    """AST analiziyle bulunan tek HTTP uç noktası (veri sözlüğü 4.8); ham çıktı ast_results'tadır."""

    HttpMethod = HttpMethod
    UnsupportedReason = UnsupportedReason

    id = models.BigAutoField(primary_key=True)
    # İndeks uq_endpoints_run_path_method ile sağlanır.
    analysis_run = models.ForeignKey(AnalysisRun, on_delete=models.CASCADE, related_name="endpoints", db_index=False)
    path = models.CharField(max_length=500)
    http_method = models.CharField(max_length=10, choices=HttpMethod.choices)
    view_name = models.CharField(max_length=255)
    auth_type = models.CharField(max_length=50, blank=True, default="")
    permission_classes = models.JSONField(default=list, blank=True)
    is_supported = models.BooleanField(default=True)
    unsupported_reason = models.CharField(max_length=50, choices=UnsupportedReason.choices, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "endpoints"
        ordering = ["path", "http_method"]
        constraints = [
            models.UniqueConstraint(fields=["analysis_run", "path", "http_method"], name="uq_endpoints_run_path_method"),
            models.CheckConstraint(condition=~Q(path=""), name="ck_endpoints_path_not_blank"),
            models.CheckConstraint(
                condition=Q(http_method__in=values(HttpMethod)), name="ck_endpoints_http_method_valid"
            ),
            models.CheckConstraint(
                condition=Q(unsupported_reason__isnull=True) | Q(unsupported_reason__in=values(UnsupportedReason)),
                name="ck_endpoints_unsupported_reason_valid",
            ),
            models.CheckConstraint(
                condition=Q(is_supported=True) | Q(unsupported_reason__isnull=False),
                name="ck_endpoints_unsupported_has_reason",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.http_method} {self.path}"
