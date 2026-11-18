from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Analiz çekirdeği"

    def ready(self):
        # H4-05: drf-spectacular görünüm uzantılarını kaydet (yalnızca şema üretimini etkiler).
        from .api import schema  # noqa: F401

