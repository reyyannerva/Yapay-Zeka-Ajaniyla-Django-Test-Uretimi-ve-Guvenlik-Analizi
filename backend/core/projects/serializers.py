"""Proje API serializer'ları — H4-03 / Issue #35.

Toplu atama (mass assignment) koruması: Her yazma serializer'ı yalnızca açıkça izin verilen alanları kabul
eder; izin verilmeyen bir alan gönderilirse (ör. ``owner``, ``validation_status``, ``source_archive``,
``archive_sha256``) sessizce yok sayılmaz, 400 ile reddedilir. Sahip her zaman sunucu tarafında
``request.user`` olarak atanır. Yanıtlar depolama yolunu, sunucu dosya adını veya mutlak yolu içermez.
"""
from __future__ import annotations

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ..models import Project


class _StrictFieldsMixin:
    """``initial_data`` içinde izin verilmeyen anahtar varsa doğrulama hatası verir."""

    allowed_input_fields: tuple[str, ...] = ()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        extra = sorted(set(getattr(self, "initial_data", {}) or {}) - set(self.allowed_input_fields))
        if extra:
            raise serializers.ValidationError(
                {name: ["Bu alan istemci tarafından gönderilemez veya değiştirilemez."] for name in extra})
        return attrs


def _clean_name(value: str) -> str:
    value = value.strip()
    if not value:
        raise serializers.ValidationError("Proje adı boş olamaz.")
    if any(not c.isprintable() for c in value):
        raise serializers.ValidationError("Proje adı denetim karakteri içeremez.")
    return value


class ProjectCreateSerializer(_StrictFieldsMixin, serializers.Serializer):
    """Proje oluşturma isteği (multipart/form-data): ``name``, isteğe bağlı ``description`` ve ``archive`` (.zip)."""

    allowed_input_fields = ("name", "description", "archive")

    name = serializers.CharField(max_length=150)
    description = serializers.CharField(required=False, allow_blank=True, default="", max_length=5000)
    archive = serializers.FileField(allow_empty_file=True, use_url=False)

    def validate_name(self, value):
        value = _clean_name(value)
        owner = self.context["request"].user
        if Project.objects.filter(owner=owner, name=value).exists():
            raise serializers.ValidationError("Bu adla kayıtlı bir projeniz zaten var.")
        return value


class ProjectUpdateSerializer(_StrictFieldsMixin, serializers.ModelSerializer):
    """Yalnızca ``name`` ve ``description`` güncellenebilir; arşiv değiştirme desteklenmez."""

    allowed_input_fields = ("name", "description")

    class Meta:
        model = Project
        fields = ["name", "description"]
        extra_kwargs = {"description": {"required": False, "allow_blank": True, "max_length": 5000}}

    def validate_name(self, value):
        value = _clean_name(value)
        qs = Project.objects.filter(owner=self.instance.owner, name=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Bu adla kayıtlı bir projeniz zaten var.")
        return value


class ArchiveInfoSerializer(serializers.Serializer):
    """Yüklenen arşivin görüntüleme bilgileri; depolama anahtarı ve sunucu yolu içermez."""

    original_name = serializers.CharField(help_text="İstemcinin gönderdiği dosya adı (yalnızca görüntüleme).")
    size_bytes = serializers.IntegerField()
    sha256 = serializers.CharField()
    uploaded_at = serializers.DateTimeField()


class ProjectSerializer(serializers.ModelSerializer):
    """Okuma gösterimi. Depolama anahtarı, sunucu dosya adı ve mutlak yol döndürülmez."""

    archive = serializers.SerializerMethodField()
    analysis_run_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ["id", "name", "description", "source_type", "validation_status", "archive",
                  "validation_report", "analysis_run_count", "created_at", "updated_at"]
        read_only_fields = fields

    @extend_schema_field(ArchiveInfoSerializer(allow_null=True))
    def get_archive(self, obj):
        if obj.source_type != Project.SourceType.ARCHIVE:
            return None
        meta = (obj.validation_report or {}).get("archive", {})
        return {"original_name": meta.get("original_name"), "size_bytes": meta.get("size_bytes"),
                "sha256": obj.archive_sha256,
                "uploaded_at": serializers.DateTimeField().to_representation(obj.created_at)}

    def get_analysis_run_count(self, obj) -> int:
        value = getattr(obj, "analysis_run_count", None)
        return value if value is not None else obj.analysis_runs.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        report = dict(data.get("validation_report") or {})
        report.pop("archive", None)  # dosya bilgileri ``archive`` alanında; iç ayrıntı tekrar edilmez
        data["validation_report"] = report
        return data
