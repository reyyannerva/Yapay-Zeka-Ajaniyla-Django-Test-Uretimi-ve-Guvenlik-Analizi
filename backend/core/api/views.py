"""API viewset'leri — H4-04 / Issue #36.

Sahiplik H4-02 (#34) `OwnedQuerysetMixin` ile uygulanır: queryset kullanıcıya göre filtrelenir,
başkasının kaydı 404 döner. Analiz oluşturma gerçek işlem başlatmaz (durum QUEUED).
"""
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from ..auth.permissions import OwnedQuerysetMixin
from ..models import AnalysisRun, ReferenceRequirement
from .serializers import (
    AnalysisRunCreateSerializer,
    AnalysisRunDetailSerializer,
    AnalysisRunListSerializer,
    ReferenceRequirementAPISerializer,
)


class AnalysisRunViewSet(OwnedQuerysetMixin, mixins.CreateModelMixin, mixins.ListModelMixin,
                         mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Analiz oluşturma (QUEUED), listeleme ve detay (ilerlemeyle). Güncelleme/silme kapsam dışıdır."""

    queryset = AnalysisRun.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return AnalysisRunCreateSerializer
        if self.action == "retrieve":
            return AnalysisRunDetailSerializer
        return AnalysisRunListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = serializer.save()
        detail = AnalysisRunDetailSerializer(run, context=self.get_serializer_context())
        return Response(detail.data, status=status.HTTP_201_CREATED)


class ReferenceRequirementViewSet(OwnedQuerysetMixin, viewsets.ModelViewSet):
    """Referans gereksinim JSON CRUD (GET/POST/PUT/PATCH/DELETE). Doğrulama #33 serializer'ında."""

    queryset = ReferenceRequirement.objects.all()
    serializer_class = ReferenceRequirementAPISerializer

    def perform_update(self, serializer):
        # Beklenen davranış değiştiğinde revizyon artırılır (model sözleşmesi).
        serializer.save(revision=serializer.instance.revision + 1)
