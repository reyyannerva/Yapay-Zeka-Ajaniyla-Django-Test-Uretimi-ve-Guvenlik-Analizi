"""URL yönlendirmeleri — kontrollü DRF hedef uygulaması (H3-01 / Issue #27)."""
from django.urls import include, path

urlpatterns = [
    path("api/", include("catalog.urls")),
]
