"""Kontrollü kaynak modeli — H3-01 / Issue #27.

Tek bir kaynak (Article) üzerinden sahiplik, rol ve 5 HTTP metodu senaryoları kurulur.
"""
from django.conf import settings
from django.db import models


class Article(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="articles",
    )
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True, default="")
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Article #{self.pk}: {self.title}"
