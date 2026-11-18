from django.conf import settings
from django.db import models
from django.db.models import Q

from ..choices import SHA256_HEX_REGEX, values
from ..fields import NullableFileField


class ProjectSourceType(models.TextChoices):
    ARCHIVE = "ARCHIVE", "Yüklenen arşiv"
    ALLOWED_DIRECTORY = "ALLOWED_DIRECTORY", "İzinli dizin"


class ProjectValidationStatus(models.TextChoices):
    PENDING = "PENDING", "Bekliyor"
    VALID = "VALID", "Geçerli"
    INVALID = "INVALID", "Geçersiz"


class Project(models.Model):
    """Analiz edilecek Django/DRF projesi (veri sözlüğü 4.2)."""

    SourceType = ProjectSourceType
    ValidationStatus = ProjectValidationStatus

    id = models.BigAutoField(primary_key=True)
    # İndeks uq_projects_owner_name ile sağlanır (owner_id ilk sütun).
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects", db_index=False
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, default="")
    source_type = models.CharField(max_length=20, choices=ProjectSourceType.choices, default=ProjectSourceType.ARCHIVE)
    # Depolama göreli anahtarı; dizin projelerinde NULL ('' değil, bkz. core/fields.py).
    source_archive = NullableFileField(upload_to="project_archives/%Y/%m/", max_length=255, null=True, blank=True)
    # İzinli kök dizine göreli yol; arşiv projelerinde NULL.
    source_directory = models.CharField(max_length=500, null=True, blank=True)
    archive_sha256 = models.CharField(max_length=64, null=True, blank=True)
    validation_status = models.CharField(
        max_length=20, choices=ProjectValidationStatus.choices, default=ProjectValidationStatus.PENDING
    )
    validation_report = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "name"], name="uq_projects_owner_name"),
            models.CheckConstraint(condition=~Q(name=""), name="ck_projects_name_not_blank"),
            models.CheckConstraint(
                condition=Q(source_type__in=values(ProjectSourceType)), name="ck_projects_source_type_valid"
            ),
            models.CheckConstraint(
                condition=Q(validation_status__in=values(ProjectValidationStatus)),
                name="ck_projects_validation_status_valid",
            ),
            models.CheckConstraint(
                condition=~Q(source_type="ARCHIVE")
                | (
                    Q(source_archive__isnull=False)
                    & ~Q(source_archive="")
                    & Q(archive_sha256__isnull=False, source_directory__isnull=True)
                ),
                name="ck_projects_archive_source_present",
            ),
            models.CheckConstraint(
                condition=~Q(source_type="ALLOWED_DIRECTORY")
                | (
                    Q(source_directory__isnull=False)
                    & ~Q(source_directory="")
                    & Q(source_archive__isnull=True, archive_sha256__isnull=True)
                ),
                name="ck_projects_directory_source_present",
            ),
            models.CheckConstraint(
                condition=Q(source_archive__isnull=True)
                | (~Q(source_archive__startswith="/") & ~Q(source_archive__contains="..")),
                name="ck_projects_source_archive_relative",
            ),
            models.CheckConstraint(
                condition=Q(source_directory__isnull=True)
                | (~Q(source_directory__startswith="/") & ~Q(source_directory__contains="..")),
                name="ck_projects_source_directory_relative",
            ),
            models.CheckConstraint(
                condition=Q(archive_sha256__isnull=True) | Q(archive_sha256__regex=SHA256_HEX_REGEX),
                name="ck_projects_archive_sha256_format",
            ),
        ]

    def __str__(self) -> str:
        return self.name
