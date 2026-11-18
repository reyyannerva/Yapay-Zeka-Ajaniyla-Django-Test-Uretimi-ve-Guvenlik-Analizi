"""API serializer'ları — H4-04 / Issue #36."""
from rest_framework import serializers

from ..models import AnalysisRun, GeneratedTest, Project
from ..progress import execution_progress
from ..serializers import ReferenceRequirementSerializer


class _OwnedProjectMixin:
    """`project` alanının queryset'ini istekteki kullanıcının projelerine indirger.

    Böylece başkasına ait / var olmayan proje kimliği, varlığı ifşa etmeden geçersiz pk (400) olur.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request is not None and "project" in self.fields:
            self.fields["project"].queryset = Project.objects.filter(owner=request.user)


# --- AnalysisRun ---
class AnalysisRunListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisRun
        fields = [
            "id", "project", "status", "method", "llm_provider", "llm_model", "fallback_enabled",
            "celery_task_id", "coverage_percent", "error_code", "error_message",
            "created_at", "started_at", "finished_at", "updated_at",
        ]
        read_only_fields = fields


class AnalysisRunDetailSerializer(AnalysisRunListSerializer):
    progress = serializers.SerializerMethodField()
    # Üretilmiş test sayısı (TestExecution bazlı ilerlemeden ayrı; henüz çalıştırılmamış testleri de sayar).
    generated_test_count = serializers.SerializerMethodField()
    requirements_snapshot = serializers.JSONField(read_only=True)

    class Meta(AnalysisRunListSerializer.Meta):
        fields = AnalysisRunListSerializer.Meta.fields + [
            "requirements_snapshot", "generated_test_count", "progress",
        ]
        read_only_fields = fields

    def get_generated_test_count(self, obj) -> int:
        return GeneratedTest.objects.filter(analysis_run=obj).count()

    def get_progress(self, obj) -> dict:
        # Henüz yürütme kaydı yoksa percent None döner; yanıltıcı 0 ilerleme üretilmez.
        return execution_progress(obj).as_dict()


class AnalysisRunCreateSerializer(_OwnedProjectMixin, serializers.ModelSerializer):
    class Meta:
        model = AnalysisRun
        fields = ["id", "project", "method", "llm_provider", "llm_model", "fallback_enabled", "status"]
        read_only_fields = ["id", "status"]

    def validate(self, attrs):
        method = attrs.get("method")
        provider = attrs.get("llm_provider")
        model = attrs.get("llm_model")
        if method == AnalysisRun.Method.RULE_BASED:
            if provider or model:
                raise serializers.ValidationError(
                    {"llm_provider": "RULE_BASED yönteminde LLM sağlayıcı/model verilmez."}
                )
        else:
            if not provider or not model:
                raise serializers.ValidationError(
                    {"llm_model": "LLM yöntemlerinde llm_provider ve llm_model zorunludur."}
                )
        project = attrs["project"]
        if AnalysisRun.objects.filter(project=project, status__in=AnalysisRun.ACTIVE_STATUSES).exists():
            raise serializers.ValidationError(
                {"project": "Bu proje için zaten aktif (sonlanmamış) bir analiz var."}
            )
        return attrs

    def create(self, validated_data):
        project = validated_data["project"]
        # Aktif referans gereksinimlerin anlık görüntüsü; her analiz kendi referans kümesini taşır.
        snapshot = ReferenceRequirementSerializer(
            project.reference_requirements.filter(is_active=True), many=True
        ).data
        # Gerçek AST/LLM/Docker tetiklenmez: durum QUEUED, celery_task_id yok.
        return AnalysisRun.objects.create(
            status=AnalysisRun.Status.QUEUED, requirements_snapshot=snapshot, **validated_data
        )


# --- ReferenceRequirement ---
class ReferenceRequirementAPISerializer(_OwnedProjectMixin, ReferenceRequirementSerializer):
    """#33'ün doğrulamasını (kategori/spesifikasyon/HTTP metodu) miras alır; projeyi sahibe sınırlar."""
