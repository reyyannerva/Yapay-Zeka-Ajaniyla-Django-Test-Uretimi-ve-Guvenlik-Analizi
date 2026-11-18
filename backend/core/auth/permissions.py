"""Proje sahipliği bazlı yetkilendirme — H4-02 / Issue #34.

Tüm uygulama kayıtlarının sahipliği ``Project.owner`` üzerinden türetilir (veri sözlüğü: her proje
tek kullanıcıya aittir). Başkasına ait kayıtlar bilgi sızdırmadan gizlenir: queryset kullanıcıya
göre filtrelendiğinden erişim denemesi 404 döner; nesne bulunup sahiplik başarısız olursa 403.
"""
from rest_framework.permissions import BasePermission

# Her model için ``Project.owner``'a giden queryset lookup'ı.
OWNER_LOOKUPS = {
    "Project": "owner",
    "AnalysisRun": "project__owner",
    "ReferenceRequirement": "project__owner",
    "Endpoint": "analysis_run__project__owner",
    "GeneratedTest": "analysis_run__project__owner",
    "TestExecution": "generated_test__analysis_run__project__owner",
    "SecurityFinding": "analysis_run__project__owner",
    "Report": "analysis_run__project__owner",
    "LlmCall": "analysis_run__project__owner",
}


def owner_lookup(model) -> str:
    try:
        return OWNER_LOOKUPS[model.__name__]
    except KeyError as exc:  # pragma: no cover
        raise KeyError(f"{model.__name__} için sahiplik lookup'ı tanımlı değil (OWNER_LOOKUPS).") from exc


def owned_queryset(queryset, user):
    """Queryset'i yalnızca ``user``'a ait kayıtlara indirger."""
    return queryset.filter(**{owner_lookup(queryset.model): user})


def _project_of(obj):
    """Nesneden ``Project``'e FK zinciriyle ulaşır."""
    current = obj
    for _ in range(5):
        if type(current).__name__ == "Project":
            return current
        for attr in ("project", "analysis_run", "generated_test"):
            if hasattr(current, attr):
                current = getattr(current, attr)
                break
        else:
            return None
    return None


def owning_user_id(obj):
    project = _project_of(obj)
    return project.owner_id if project is not None else None


class IsProjectOwner(BasePermission):
    """Kimlik doğrulaması şart; nesne düzeyinde yalnızca kaynağın sahibi erişebilir."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return owning_user_id(obj) == request.user.id


class OwnedQuerysetMixin:
    """ViewSet/generic view'lar için: get_queryset'i kullanıcıya göre filtreler ve IsProjectOwner uygular.

    Alt sınıf ``queryset`` (veya ``model``) tanımlar. Böylece liste/detay/güncelleme/silme yalnızca
    sahibin kayıtlarında çalışır; başkasının kaydı queryset dışı kaldığından 404 döner.
    """

    permission_classes = [IsProjectOwner]

    def get_queryset(self):
        return owned_queryset(super().get_queryset(), self.request.user)
