"""API dokümantasyonu erişim politikası — H4-05 / Issue #37.

``API_DOCS_PUBLIC=true`` (geliştirme varsayılanı, DEBUG ile aynı) iken şema, Swagger UI ve ReDoc herkese
açıktır. ``false`` iken yalnızca personel (``is_staff``) kullanıcılar erişebilir; böylece üretimde API
yüzeyi varsayılan olarak yayımlanmaz. Bu izin yalnızca dokümantasyon görünümlerine uygulanır; API uç
noktalarının kimlik doğrulama ve yetkilendirme kuralları değişmez.
"""
from django.conf import settings
from rest_framework.permissions import BasePermission


class ApiDocsPermission(BasePermission):
    def has_permission(self, request, view):
        if getattr(settings, "API_DOCS_PUBLIC", False):
            return True
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.is_staff)
