"""Kimlik doğrulama istisnaları — H4-02 / Issue #34 (kalan süre bilgisi: H5-03 / Issue #41)."""
from __future__ import annotations

import math
from datetime import datetime

from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException

LOCKED_DETAIL = (
    "Çok fazla başarısız giriş denemesi. Hesap geçici olarak kilitlendi; "
    "lütfen bir süre sonra tekrar deneyin."
)


class AccountLocked(APIException):
    """Üç başarısız denemeden sonra hesap geçici olarak kilitli (django-axes).

    Gövde geriye uyumludur (``detail`` korunur). H5-03 / #41 ile frontend'in kilidi istek sınırlamasından
    (aynı 429) ayırabilmesi ve kalan süreyi gösterebilmesi için ``code``, ``locked_until`` ve
    ``retry_after_seconds`` eklenir; ``Retry-After`` başlığı da gönderilir. Kilit bitiş zamanı django-axes'in
    kalıcı ``expires_at`` değeridir; güvenlik kararı yine axes tarafından verilir.
    """

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = LOCKED_DETAIL
    default_code = "account_locked"

    def __init__(self, locked_until: datetime | None = None):
        super().__init__()
        self.retry_after_seconds: int | None = None
        self.locked_until: datetime | None = locked_until
        if locked_until is not None:
            self.retry_after_seconds = max(0, math.ceil((locked_until - timezone.now()).total_seconds()))

    def payload(self) -> dict:
        """Yanıt gövdesi (sayısal alanlar DRF hata dizgesine çevrilmeden)."""
        return {
            "detail": LOCKED_DETAIL,
            "code": self.default_code,
            "locked_until": self.locked_until.isoformat() if self.locked_until else None,
            "retry_after_seconds": self.retry_after_seconds,
        }

    def to_response(self):
        from rest_framework.response import Response

        headers = {}
        if self.retry_after_seconds is not None:
            headers["Retry-After"] = str(self.retry_after_seconds)
        return Response(self.payload(), status=self.status_code, headers=headers)
