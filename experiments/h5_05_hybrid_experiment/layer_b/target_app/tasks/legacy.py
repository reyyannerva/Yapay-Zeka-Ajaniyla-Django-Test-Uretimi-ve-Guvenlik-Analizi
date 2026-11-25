"""BİLEREK GÜVENSİZ uç — H5-05 Katman B (yalnızca kontrollü deney hedefi).

/api/legacy/tasks/<pk>/ : kimlik doğrulama ister ancak NESNE SAHİPLİĞİNİ DENETLEMEZ
(BOLA/IDOR, OWASP API1:2023). Başka bir kullanıcı PUT/PATCH/DELETE ile kaydı değiştirebilir/silebilir.
Güvenli beklenti (ground truth): sahip olmayan kullanıcıya 403. Bu sınıf yalnızca deney içindir.
"""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Task
from .serializers import TaskSerializer


class LegacyTaskDetail(APIView):
    permission_classes = [IsAuthenticated]  # KUSUR: nesne sahipliği kontrolü yok

    def get(self, request, pk):
        return Response(TaskSerializer(get_object_or_404(Task, pk=pk)).data)

    def _save(self, request, pk, partial):
        task = get_object_or_404(Task, pk=pk)
        serializer = TaskSerializer(task, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def put(self, request, pk):
        return self._save(request, pk, partial=False)

    def patch(self, request, pk):
        return self._save(request, pk, partial=True)

    def delete(self, request, pk):
        get_object_or_404(Task, pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
