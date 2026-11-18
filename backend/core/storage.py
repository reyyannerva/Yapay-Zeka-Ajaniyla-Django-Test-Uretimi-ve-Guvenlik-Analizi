"""Yüklenen proje arşivleri için özel (herkese açık olmayan) depolama — H4-03 / Issue #35.

* Konum ``settings.PROJECT_ARCHIVE_ROOT`` (varsayılan ``backend/private_storage``); ``MEDIA_ROOT`` ve
  statik dizinlerden ayrıdır ve hiçbir URL ile sunulmaz.
* ``url()`` bilinçli olarak desteklenmez: arşivlere doğrudan bağlantı verilmez.
* Dosya izinleri 0600, dizin izinleri 0700 (POSIX); dosyalar çalıştırılabilir değildir.
* Konum her erişimde ayarlardan okunur; böylece testler ``settings`` ile geçici bir kök verebilir ve
  migration dosyasına ortamdan bağımsız bir değer yazılmaz.
"""
from __future__ import annotations

import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible(path="core.storage.ProjectArchiveStorage")
class ProjectArchiveStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(file_permissions_mode=0o600, directory_permissions_mode=0o700)

    @property
    def base_location(self):  # type: ignore[override]
        return str(settings.PROJECT_ARCHIVE_ROOT)

    @property
    def location(self):  # type: ignore[override]
        return os.path.abspath(self.base_location)

    @property
    def base_url(self):  # type: ignore[override]
        return None

    def url(self, name):
        raise NotImplementedError("Proje arşivleri herkese açık URL ile sunulmaz.")
