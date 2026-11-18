"""Proje yönetimi API'si — H4-03 / Issue #35.

| Yöntem | URL | İşlem |
|---|---|---|
| POST | /api/projects/ | multipart arşiv yükleme ile proje oluşturma (201) |
| GET | /api/projects/ | yalnızca kullanıcının projeleri (200, sayfalı) |
| GET | /api/projects/{id}/ | proje detayı (200) |
| PATCH / PUT | /api/projects/{id}/ | ad/açıklama güncelleme (200) |
| DELETE | /api/projects/{id}/ | proje ve bağlı analiz kayıtlarını silme (204) |

Kimlik doğrulama SimpleJWT (H4-02 ``DEFAULT_AUTHENTICATION_CLASSES``); sahiplik H4-02
``OwnedQuerysetMixin``/``IsProjectOwner`` ile sağlanır. Başkasının projesi queryset dışında kaldığı için
404 döner (varlığı ifşa edilmez).
"""
from __future__ import annotations

from django.conf import settings
from django.db.models import Count
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import UnsupportedMediaType, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from ..auth.permissions import OwnedQuerysetMixin
from ..models import Project
from . import services
from .archive import ArchiveRejected
from .exceptions import UploadTooLarge
from .serializers import ProjectCreateSerializer, ProjectSerializer, ProjectUpdateSerializer
from .upload import MaxSizeUploadHandler

# multipart sınırları ve form alanları için tanınan pay (bayt).
_MULTIPART_OVERHEAD = 64 * 1024


class ProjectPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ProjectViewSet(OwnedQuerysetMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    pagination_class = ProjectPagination
    parser_classes = [MultiPartParser, JSONParser]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return super().get_queryset().annotate(analysis_run_count=Count("analysis_runs")).order_by("-created_at")

    def get_throttles(self):
        if self.action == "create":
            self.throttle_scope = "project_upload"
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def _limit(self) -> int:
        return int(settings.PROJECT_UPLOAD_LIMITS["max_upload_bytes"])

    # ---- oluşturma ----------------------------------------------------------------------------
    def create(self, request, *args, **kwargs):
        if not (request.content_type or "").startswith("multipart/form-data"):
            raise UnsupportedMediaType(request.content_type or "",
                                       detail="Proje oluşturma multipart/form-data ile yapılmalıdır.")
        limit = self._limit()
        try:
            declared = int(request.META.get("CONTENT_LENGTH") or 0)
        except ValueError:
            declared = 0
        if declared > limit + _MULTIPART_OVERHEAD:
            raise UploadTooLarge(f"Yüklenen dosya en fazla {limit} bayt olabilir.")
        handler = MaxSizeUploadHandler(request._request, limit)
        request._request.upload_handlers = [handler, *request._request.upload_handlers]
        data = request.data  # gövde burada, sınırlı işleyiciyle ayrıştırılır
        if handler.exceeded:
            raise UploadTooLarge(f"Yüklenen dosya en fazla {limit} bayt olabilir.")
        if len(request.FILES.getlist("archive")) > 1 or len(handler.file_fields) > 1:
            raise ValidationError({"archive": ["Tek bir arşiv dosyası yüklenmelidir."]})

        serializer = ProjectCreateSerializer(data=data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data
        try:
            project = services.create_project(request.user, v["name"], v.get("description", ""), v["archive"])
        except ArchiveRejected as exc:
            raise ValidationError({"archive": [exc.as_dict()]}) from None
        except services.DuplicateProjectName:
            raise ValidationError({"name": ["Bu adla kayıtlı bir projeniz zaten var."]}) from None
        project = self.get_queryset().get(pk=project.pk)
        return Response(ProjectSerializer(project, context=self.get_serializer_context()).data,
                        status=status.HTTP_201_CREATED)

    # ---- güncelleme ---------------------------------------------------------------------------
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        if request.FILES:
            raise ValidationError({"archive": ["Arşiv güncellenemez; yeni arşiv için yeni proje oluşturun."]})
        serializer = ProjectUpdateSerializer(instance, data=request.data, partial=partial,
                                             context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance = self.get_queryset().get(pk=instance.pk)
        return Response(ProjectSerializer(instance, context=self.get_serializer_context()).data)

    # ---- silme ---------------------------------------------------------------------------------
    def destroy(self, request, *args, **kwargs):
        services.delete_project(self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)
