from django.db import models
from django.db.models import Q

from ..choices import values
from .analysis import AnalysisRun, LlmProvider
from .generation import GeneratedTest


class LlmCallPurpose(models.TextChoices):
    GENERATE = "GENERATE", "Üretim"
    REPAIR = "REPAIR", "Düzeltme"


class LlmCallStatus(models.TextChoices):
    SUCCESS = "SUCCESS", "Başarılı"
    ERROR = "ERROR", "Hata"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED", "Kota aşıldı"
    TIMEOUT = "TIMEOUT", "Zaman aşımı"


class LlmCall(models.Model):
    """LiteLLM üzerinden yapılan tek dil modeli çağrısı (veri sözlüğü 4.10; İST-13). İstem/anahtar saklanmaz."""

    Provider = LlmProvider
    Purpose = LlmCallPurpose
    Status = LlmCallStatus

    id = models.BigAutoField(primary_key=True)
    # İndeks ix_llmcall_run_created ile sağlanır.
    analysis_run = models.ForeignKey(AnalysisRun, on_delete=models.CASCADE, related_name="llm_calls", db_index=False)
    generated_test = models.ForeignKey(
        GeneratedTest, on_delete=models.SET_NULL, null=True, blank=True, related_name="llm_calls", db_index=False
    )
    provider = models.CharField(max_length=20, choices=LlmProvider.choices)
    model = models.CharField(max_length=100)
    purpose = models.CharField(max_length=20, choices=LlmCallPurpose.choices)
    prompt_tokens = models.IntegerField(null=True, blank=True)
    completion_tokens = models.IntegerField(null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=LlmCallStatus.choices)
    error_message = models.CharField(max_length=2000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "llm_calls"
        ordering = ["analysis_run_id", "created_at"]
        indexes = [
            models.Index(fields=["analysis_run", "created_at"], name="ix_llmcall_run_created"),
            models.Index(fields=["generated_test"], name="ix_llmcall_generated_test"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(provider__in=values(LlmProvider)), name="ck_llm_calls_provider_valid"),
            models.CheckConstraint(condition=~Q(model=""), name="ck_llm_calls_model_not_blank"),
            models.CheckConstraint(condition=Q(purpose__in=values(LlmCallPurpose)), name="ck_llm_calls_purpose_valid"),
            models.CheckConstraint(condition=Q(status__in=values(LlmCallStatus)), name="ck_llm_calls_status_valid"),
            models.CheckConstraint(
                condition=(Q(prompt_tokens__isnull=True) | Q(prompt_tokens__gte=0))
                & (Q(completion_tokens__isnull=True) | Q(completion_tokens__gte=0)),
                name="ck_llm_calls_tokens_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(latency_ms__isnull=True) | Q(latency_ms__gte=0), name="ck_llm_calls_latency_non_negative"
            ),
            models.CheckConstraint(
                condition=~Q(status="SUCCESS") | Q(prompt_tokens__isnull=False, completion_tokens__isnull=False),
                name="ck_llm_calls_success_has_tokens",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.provider}/{self.model} {self.purpose}: {self.status}"
