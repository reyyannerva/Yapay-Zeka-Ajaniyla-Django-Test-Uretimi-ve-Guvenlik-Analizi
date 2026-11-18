"""Proje oluşturma ve silme servisleri; dosya ↔ veritabanı tutarlılığı — H4-03 / Issue #35.

Dosya deposu ile PostgreSQL işlemi birlikte atomik değildir. Bu nedenle:

* **Oluşturma:** Arşiv önce tamamen doğrulanır (dosya yazılmadan). Sonra sunucu tarafından üretilen benzersiz
  bir adla depoya yazılır ve kayıt aynı işlem içinde kaydedilir. Veritabanı kaydı başarısız olursa yazılan
  dosya hemen silinir; silme de başarısız olursa olay ``WARNING`` ile günlüğe yazılır ve dosya
  ``cleanup_project_archives`` komutuyla bulunup temizlenebilir (öksüz dosya tespit edilebilir kalır).
* **Silme:** Önce kayıt (ve CASCADE ile bağlı analiz kayıtları) silinir; arşiv dosyası yalnızca işlem
  başarıyla tamamlandıktan sonra (``transaction.on_commit``) silinir. Böylece geri alınan bir işlem dosyayı
  kaybettirmez. Dosya silme başarısız olursa kayıt zaten silinmiştir; dosya öksüz kalır, günlüğe yazılır ve
  aynı komutla temizlenir.
* Arşiv değiştirme bu sürümde desteklenmez; güncelleme yalnızca metadata içindir.
"""
from __future__ import annotations

import logging
import uuid

from django.core.files import File
from django.db import IntegrityError, transaction
from django.utils import timezone

from ..models import AnalysisRun, Project
from . import structure
from .archive import ArchiveInspection, ArchiveLimits, ArchiveRejected, inspect_zip
from .exceptions import ProjectBusy

logger = logging.getLogger("core.projects")

REPORT_SCHEMA_VERSION = 1


class DuplicateProjectName(Exception):
    pass


def safe_display_name(filename: str) -> str:
    """İstemci dosya adının yalnızca son bileşeni, yalnızca metadata olarak (yol olarak kullanılmaz)."""
    name = (filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    name = "".join(c for c in name if c.isprintable())[:200]
    return name or "archive.zip"


def validate_archive(uploaded, limits: ArchiveLimits | None = None) -> tuple[ArchiveInspection, dict]:
    """Arşivi güvenlik ve Django yapısı açısından doğrular; ``validation_report`` sözlüğünü döndürür."""
    limits = limits or ArchiveLimits.from_settings()
    inspection = inspect_zip(uploaded, uploaded.name, limits, text_wanted=structure.wants_text)
    django = structure.analyze(inspection.files, inspection.texts)
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "checked_at": timezone.now().isoformat(timespec="seconds"),
        "archive": {
            "format": "zip",
            "original_name": safe_display_name(uploaded.name),
            "size_bytes": inspection.size_bytes,
            "file_count": inspection.file_count,
            "dir_count": inspection.dir_count,
            "uncompressed_bytes": inspection.uncompressed_bytes,
        },
        **{k: v for k, v in django.items() if k != "warnings"},
        "rejected_entries": inspection.excluded,
        "warnings": django["warnings"],
    }
    return inspection, report


def _delete_stored_archive(storage, name: str, reason: str) -> bool:
    try:
        storage.delete(name)
        return True
    except Exception:  # pragma: no cover - depoya bağlı; testte zorlanır
        logger.warning("Proje arşivi depodan silinemedi (%s): %s — cleanup_project_archives ile temizleyin.",
                       reason, name, exc_info=True)
        return False


def name_taken(owner, name: str) -> bool:
    return Project.objects.filter(owner=owner, name=name).exists()


def create_project(owner, name: str, description: str, uploaded) -> Project:
    """Doğrulanmış arşivle yeni proje oluşturur. Hata durumunda depoda dosya bırakmaz."""
    inspection, report = validate_archive(uploaded)
    if name_taken(owner, name):
        raise DuplicateProjectName(name)
    project = Project(
        owner=owner, name=name, description=description, source_type=Project.SourceType.ARCHIVE,
        archive_sha256=inspection.sha256, validation_status=Project.ValidationStatus.VALID,
        validation_report=report,
    )
    storage = project.source_archive.storage
    uploaded.seek(0)
    stored_name = None
    try:
        # Sunucu tarafında üretilen ad: istemci dosya adı yol olarak hiçbir zaman kullanılmaz.
        project.source_archive.save(f"{uuid.uuid4().hex}.zip", File(uploaded), save=False)
        stored_name = project.source_archive.name
        with transaction.atomic():
            project.save()
    except IntegrityError as exc:
        if stored_name:
            _delete_stored_archive(storage, stored_name, "kayıt oluşturulamadı")
        if "uq_projects_owner_name" in str(exc):
            raise DuplicateProjectName(name) from None
        raise
    except BaseException:
        if stored_name:
            _delete_stored_archive(storage, stored_name, "kayıt oluşturulamadı")
        raise
    logger.info("Proje oluşturuldu: id=%s owner=%s", project.pk, owner.pk)
    return project


def delete_project(project: Project) -> None:
    """Projeyi ve CASCADE ile bağlı analiz kayıtlarını siler; arşivi işlem başarılı olunca kaldırır."""
    if project.analysis_runs.filter(status__in=AnalysisRun.ACTIVE_STATUSES).exists():
        raise ProjectBusy()
    storage = project.source_archive.storage
    name = project.source_archive.name or None
    project_id = project.pk
    with transaction.atomic():
        project.delete()
        if name:
            transaction.on_commit(lambda: _delete_stored_archive(storage, name, f"proje {project_id} silindi"))


__all__ = ["ArchiveRejected", "DuplicateProjectName", "create_project", "delete_project", "validate_archive"]
