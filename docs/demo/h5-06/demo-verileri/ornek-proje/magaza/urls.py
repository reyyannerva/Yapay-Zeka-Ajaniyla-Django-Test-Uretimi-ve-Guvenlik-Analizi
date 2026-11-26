"""Örnek mağaza URL yapılandırması (H5-06 demo verisi)."""
from rest_framework.routers import DefaultRouter

from .views import ArticleViewSet

router = DefaultRouter()
router.register(r"articles", ArticleViewSet, basename="article")

urlpatterns = router.urls
