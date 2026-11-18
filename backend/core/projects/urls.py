"""Proje API URL'leri — H4-03 / Issue #35. config/urls.py altında /api/ ile bağlanır."""
from rest_framework.routers import SimpleRouter

from .views import ProjectViewSet

app_name = "projects"

router = SimpleRouter()
router.register("projects", ProjectViewSet, basename="project")
urlpatterns = router.urls
