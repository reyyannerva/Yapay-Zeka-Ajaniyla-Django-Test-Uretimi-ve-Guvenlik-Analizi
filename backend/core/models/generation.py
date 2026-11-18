from django.db import models
from django.db.models import Q

from ..choices import SHA256_HEX_REGEX, values
from .analysis import AnalysisRun
from .endpoint import Endpoint


class GenerationMethod(models.TextChoices):
    LLM = "LLM", "LLM"
    RULE_BASED = "RULE_BASED", "Kural tabanlı"


class TestValidationStatus(models.TextChoices):
    PENDING = "PENDING", "Bekliyor"
    VALID = "VALID", "Geçerli"
    INVALID_SYNTAX = "INVALID_SYNTAX", "Sözdizimi geçersiz"
    REJECTED_POLICY = "REJECTED_POLICY", "Politika nedeniyle reddedildi"


class GeneratedTest(models.Model):
    """Üretilen tek Pytest testi (veri sözlüğü 4.5, 9.1). Model adı ve token kullanımı llm_calls'tadır."""

    __test__ = False  # pytest'in sınıfı test olarak toplamasını engeller

    GenerationMethod = GenerationMethod
    ValidationStatus = TestValidationStatus

    id = models.BigAutoField(primary_key=True)
    # İndeks uq_generated_tests_run_module_name ile sağlanır.
    analysis_run = models.ForeignKey(
        AnalysisRun, on_delete=models.CASCADE, related_name="generated_tests", db_index=False
    )
    # Aynı çalıştırmaya ait olmalıdır (uygulama kuralı, veri sözlüğü 7.2).
    endpoint = models.ForeignKey(
        Endpoint, on_delete=models.SET_NULL, null=True, blank=True, related_name="generated_tests", db_index=False
    )
    test_module = models.CharField(max_length=150)
    test_name = models.CharField(max_length=150)
    generation_method = models.CharField(max_length=20, choices=GenerationMethod.choices)
    # AnalysisRun.requirements_snapshot girdisine karşılık gelir; canlı FK değildir.
    requirement_code = models.CharField(max_length=50, blank=True, default="")
    role = models.CharField(max_length=50, blank=True, default="")
    expected_status = models.SmallIntegerField(null=True, blank=True)
    is_security_test = models.BooleanField(default=False)
    source_code = models.TextField()
    code_sha256 = models.CharField(max_length=64)
    # Yalnızca VALID testler yürütülebilir (uygulama kuralı).
    validation_status = models.CharField(
        max_length=20, choices=TestValidationStatus.choices, default=TestValidationStatus.PENDING
    )
    validation_errors = models.JSONField(default=list, blank=True)
    repair_count = models.SmallIntegerField(default=0)
    generation_metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "generated_tests"
        ordering = ["test_module", "test_name"]
        indexes = [models.Index(fields=["endpoint"], name="ix_gentest_endpoint")]
        constraints = [
            models.UniqueConstraint(
                fields=["analysis_run", "test_module", "test_name"], name="uq_generated_tests_run_module_name"
            ),
            models.CheckConstraint(
                condition=Q(test_module__regex=r"^test_[A-Za-z0-9_]+\.py$"), name="ck_generated_tests_module_format"
            ),
            models.CheckConstraint(
                condition=Q(test_name__regex=r"^test_[A-Za-z0-9_]+$"), name="ck_generated_tests_name_format"
            ),
            models.CheckConstraint(
                condition=Q(generation_method__in=values(GenerationMethod)), name="ck_generated_tests_method_valid"
            ),
            models.CheckConstraint(
                condition=Q(expected_status__isnull=True) | Q(expected_status__gte=100, expected_status__lte=599),
                name="ck_generated_tests_expected_status_range",
            ),
            models.CheckConstraint(
                condition=Q(validation_status__in=values(TestValidationStatus)),
                name="ck_generated_tests_validation_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(repair_count__gte=0, repair_count__lte=1), name="ck_generated_tests_repair_count_range"
            ),
            models.CheckConstraint(
                condition=Q(code_sha256__regex=SHA256_HEX_REGEX), name="ck_generated_tests_code_sha256_format"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.test_module}::{self.test_name}"
