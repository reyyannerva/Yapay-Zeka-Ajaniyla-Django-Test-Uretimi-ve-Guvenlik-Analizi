from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("core.auth.urls")),  # H4-02 / Issue #34
    path("api/", include("core.api.urls")),  # H4-04 / Issue #36 (analysis-runs, reference-requirements)
]
