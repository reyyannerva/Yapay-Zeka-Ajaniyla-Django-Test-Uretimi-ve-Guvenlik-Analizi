"""GÜVENLİ view'lar — H3-01 / Issue #27.

Beklenen DOĞRU davranışı temsil eder. 5 HTTP metodu (GET/POST/PUT/PATCH/DELETE) ve
APIView örneği (publish) içerir. Bilerek güvensiz varyantlar `insecure.py` içindedir.
"""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Article
from .permissions import IsOwnerOrAdminOrReadOnly
from .serializers import ArticleSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    """GET list/detail, POST create, PUT/PATCH update, DELETE destroy.

    Görünürlük: anonim yalnızca yayınlananları; kimliği doğrulanmış kullanıcı kendi
    kayıtları + yayınlananları; yönetici tümünü görür. Böylece başkasının taslağına
    erişim 404 üretir.
    """

    serializer_class = ArticleSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        qs = Article.objects.all()
        if user.is_authenticated:
            if user.is_staff:
                return qs
            return qs.filter(Q(is_published=True) | Q(owner=user))
        return qs.filter(is_published=True)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ArticlePublishView(APIView):
    """APIView örneği: POST /api/articles/<pk>/publish/ — kaynağı yayınlar.

    Yalnızca sahip veya yönetici yayınlayabilir (aksi 403; anonim 401).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        article = get_object_or_404(Article, pk=pk)
        if not (article.owner_id == request.user.id or request.user.is_staff):
            raise PermissionDenied("Yalnızca sahip veya yönetici yayınlayabilir.")
        article.is_published = True
        article.save(update_fields=["is_published"])
        return Response(ArticleSerializer(article).data, status=status.HTTP_200_OK)
