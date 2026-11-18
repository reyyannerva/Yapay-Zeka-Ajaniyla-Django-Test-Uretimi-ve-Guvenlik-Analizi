"""API URL'leri — H4-04 / Issue #36. config/urls.py altında /api/ ile bağlanır."""
from rest_framework.routers import SimpleRouter

from .views import AnalysisRunViewSet, ReferenceRequirementViewSet

router = SimpleRouter()
router.register("analysis-runs", AnalysisRunViewSet, basename="analysis-run")
router.register("reference-requirements", ReferenceRequirementViewSet, basename="reference-requirement")

urlpatterns = router.urls
