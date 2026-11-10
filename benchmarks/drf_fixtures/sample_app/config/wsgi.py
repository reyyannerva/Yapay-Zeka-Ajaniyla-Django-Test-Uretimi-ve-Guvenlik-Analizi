"""WSGI girişi — kontrollü DRF hedef uygulaması (H3-01 / Issue #27)."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
