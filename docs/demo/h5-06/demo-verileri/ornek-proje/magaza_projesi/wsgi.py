"""Örnek proje WSGI girişi (H5-06 demo verisi)."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "magaza_projesi.settings")
application = get_wsgi_application()
