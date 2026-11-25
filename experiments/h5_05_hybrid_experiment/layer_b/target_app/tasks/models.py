"""Görev kaynağı — H5-05 Katman B kontrollü hedef uygulaması."""
from django.conf import settings
from django.db import models


class Task(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=120)
    notes = models.TextField(blank=True, default="")
    is_done = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.title
