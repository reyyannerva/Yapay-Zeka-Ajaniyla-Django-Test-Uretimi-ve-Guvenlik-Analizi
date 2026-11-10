"""İzin sınıfları — H3-01 / Issue #27.

DOĞRU (güvenli) yetkilendirme kuralı: güvenli metotlar (GET/HEAD/OPTIONS) herkese açık;
değiştiren metotlar (POST/PUT/PATCH/DELETE) için kimlik doğrulama şart, nesne düzeyinde
ise yalnızca kaynak sahibi veya yönetici (is_staff) yetkilidir.
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        # POST ve nesne düzeyi öncesi: kimlik doğrulama şart (anonim -> 401).
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        # Yalnızca sahip veya yönetici değiştirebilir (aksi -> 403).
        return obj.owner_id == request.user.id or request.user.is_staff
