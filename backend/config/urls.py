from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("core.auth.urls")),  # H4-02 / Issue #34
    path("api/", include("core.projects.urls")),  # H4-03 / Issue #35
    path("api/", include("core.api.urls")),  # H4-04 / Issue #36 (analysis-runs, reference-requirements)
    # H4-05 / Issue #37 — OpenAPI 3 şeması, Swagger UI ve ReDoc (erişim: API_DOCS_PUBLIC)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
