from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrAdminForWrites(BasePermission):
    """Okuma: kimliği doğrulanmış herkes. Yazma (PUT/PATCH/DELETE): yalnızca sahip veya yönetici."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.owner_id == request.user.id or request.user.is_staff
