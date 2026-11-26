"""Örnek mağaza API görünümleri (H5-06 demo verisi).

GET/POST/PUT/PATCH/DELETE metotlarını kapsayan basit bir DRF ViewSet; referans gereksinim
JSON'undaki metot kapsamını temsil eder.
"""
from rest_framework import permissions, viewsets

from .models import Article
from .serializers import ArticleSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Article.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
