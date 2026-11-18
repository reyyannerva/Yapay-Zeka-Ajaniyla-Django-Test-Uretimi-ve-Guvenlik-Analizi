"""Kimlik doğrulama istisnaları — H4-02 / Issue #34."""
from rest_framework import status
from rest_framework.exceptions import APIException


class AccountLocked(APIException):
    """Üç başarısız denemeden sonra hesap geçici olarak kilitli (django-axes)."""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = (
        "Çok fazla başarısız giriş denemesi. Hesap geçici olarak kilitlendi; "
        "lütfen bir süre sonra tekrar deneyin."
    )
    default_code = "account_locked"
