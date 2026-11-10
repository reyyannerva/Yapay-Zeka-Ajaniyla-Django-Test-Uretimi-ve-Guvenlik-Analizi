"""Serializer — H3-01 / Issue #27. Girdi doğrulama senaryolarının (400) kaynağı."""
from rest_framework import serializers

from .models import Article


class ArticleSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = Article
        fields = ["id", "owner", "title", "body", "is_published", "created_at"]
        read_only_fields = ["id", "owner", "created_at"]

    def validate_title(self, value):
        # Boş/yalnızca boşluk başlıklar girdi doğrulama hatası (400) üretir.
        if not value.strip():
            raise serializers.ValidationError("Başlık boş olamaz.")
        return value
