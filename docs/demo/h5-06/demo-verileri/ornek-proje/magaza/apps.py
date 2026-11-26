"""Örnek mağaza uygulama yapılandırması (H5-06 demo verisi)."""
from django.apps import AppConfig


class MagazaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "magaza"
