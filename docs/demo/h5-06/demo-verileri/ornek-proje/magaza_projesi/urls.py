"""Örnek proje URL yapılandırması (H5-06 demo verisi)."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("magaza.urls")),
]
