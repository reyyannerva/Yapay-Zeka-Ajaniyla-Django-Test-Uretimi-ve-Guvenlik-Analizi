"""!!! BİLEREK GÜVENSİZ view'lar — H3-01 / Issue #27 !!!

Bu modüldeki uçlar KASITLI güvenlik hataları içerir ve yalnızca değerlendirme/etiketleme
içindir. `views.py`'deki güvenli muadillerinden AYRI tutulur. Her hata senaryo veri
kümesinde `is_intentional_flaw: true` ile işaretlidir.

Hatalar:
  1) InsecureArticleDetail — Nesne düzeyi yetkilendirme YOK (yalnızca IsAuthenticated).
     Herhangi bir kimliği doğrulanmış kullanıcı BAŞKASININ kaydını güncelleyebilir/silebilir.
     => OWASP API1:2023 Broken Object Level Authorization (BOLA/IDOR).
  2) InsecureArticleList — AllowAny + filtrelemesiz queryset. Yayınlanmamış (taslak)
     kayıtları da herkese açar. => Hassas veri ifşası / bozuk fonksiyon düzeyi yetkilendirme.
"""
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Article
from .serializers import ArticleSerializer


class InsecureArticleDetail(generics.RetrieveUpdateDestroyAPIView):
    # BUG: Nesne düzeyi sahiplik kontrolü yok. Güvenli muadili ownership ister.
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]


class InsecureArticleList(generics.ListAPIView):
    # BUG: Tüm kayıtları (taslaklar dâhil) herkese döndürür.
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [AllowAny]
