"""catalog URL yönlendirmeleri — H3-01 / Issue #27.

Güvenli uçlar:
  /api/articles/                 GET(list), POST(create)
  /api/articles/<pk>/            GET, PUT, PATCH, DELETE
  /api/articles/<pk>/publish/    POST (APIView)
Bilerek güvensiz uçlar (ayrı prefix):
  /api/insecure/articles/        GET (taslakları ifşa eder)
  /api/insecure/articles/<pk>/   GET, PUT, PATCH, DELETE (sahiplik kontrolü yok)
"""
from django.urls import path
from rest_framework.routers import SimpleRouter

from .insecure import InsecureArticleDetail, InsecureArticleList
from .views import ArticlePublishView, ArticleViewSet

router = SimpleRouter(trailing_slash=True)
router.register(r"articles", ArticleViewSet, basename="article")

urlpatterns = [
    path("articles/<int:pk>/publish/", ArticlePublishView.as_view(), name="article-publish"),
    path("insecure/articles/", InsecureArticleList.as_view(), name="insecure-article-list"),
    path("insecure/articles/<int:pk>/", InsecureArticleDetail.as_view(), name="insecure-article-detail"),
]
urlpatterns += router.urls
