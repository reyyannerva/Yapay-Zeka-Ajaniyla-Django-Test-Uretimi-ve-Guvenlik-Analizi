"""GÜVENLİ görev uçları — H5-05 Katman B.

/api/tasks/       GET (list), POST (create)          — kimlik doğrulama zorunlu
/api/tasks/<pk>/  GET, PUT, PATCH, DELETE            — yazma işlemleri yalnızca sahip/yönetici (aksi 403)
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Task
from .permissions import IsOwnerOrAdminForWrites
from .serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdminForWrites]
    queryset = Task.objects.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
