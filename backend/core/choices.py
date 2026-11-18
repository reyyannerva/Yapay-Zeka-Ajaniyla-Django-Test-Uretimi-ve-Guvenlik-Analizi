"""Ortak denetimli değer kümeleri — H4-01 / Issue #33.

Denetimli değerler veritabanında BÜYÜK HARF saklanır (docs/database/data_dictionary.md).
"""
from django.db import models


class HttpMethod(models.TextChoices):
    """Desteklenen HTTP yöntemleri (İST-04). HEAD ve OPTIONS bilinçli olarak dışarıdadır."""

    GET = "GET", "GET"
    POST = "POST", "POST"
    PUT = "PUT", "PUT"
    PATCH = "PATCH", "PATCH"
    DELETE = "DELETE", "DELETE"


HTTP_METHODS: tuple[str, ...] = tuple(HttpMethod.values)
SHA256_HEX_REGEX = r"^[0-9a-f]{64}$"


def values(choices: type[models.TextChoices]) -> list[str]:
    """CheckConstraint'lerde kullanılan değer listesi; tek kaynaktan türetilir."""
    return list(choices.values)
