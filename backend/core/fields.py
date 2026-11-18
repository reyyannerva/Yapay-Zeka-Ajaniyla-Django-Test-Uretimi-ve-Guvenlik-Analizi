"""Özel model alanları — H4-01 / Issue #33."""
from django.db import models


class NullableFileField(models.FileField):
    """Dosya yokken veritabanına ``''`` yerine ``NULL`` yazan FileField.

    Django'nun FileField'ı ``null=True`` olsa bile boş dosyayı ``''`` olarak saklar. Kanonik şema ise
    "arşiv yok" durumunu ``source_archive IS NULL`` ile tanımlar (ck_projects_directory_source_present).
    Bu alt sınıf şema anlamını korur; sütun tipi ve migration davranışı FileField ile aynıdır.
    """

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return value or None
