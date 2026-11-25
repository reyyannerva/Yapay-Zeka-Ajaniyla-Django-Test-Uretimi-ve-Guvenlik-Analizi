from django.urls import path
from rest_framework.routers import SimpleRouter

from .legacy import LegacyTaskDetail
from .views import TaskViewSet

router = SimpleRouter(trailing_slash=True)
router.register(r"tasks", TaskViewSet, basename="task")

urlpatterns = [path("legacy/tasks/<int:pk>/", LegacyTaskDetail.as_view(), name="legacy-task-detail")]
urlpatterns += router.urls
