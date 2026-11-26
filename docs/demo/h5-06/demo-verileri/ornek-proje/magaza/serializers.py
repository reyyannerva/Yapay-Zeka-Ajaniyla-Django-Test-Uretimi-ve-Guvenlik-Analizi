"""Örnek mağaza serileştiricisi (H5-06 demo verisi)."""
from rest_framework import serializers

from .models import Article


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["id", "title", "body", "is_published", "created_at"]
        read_only_fields = ["id", "created_at"]
