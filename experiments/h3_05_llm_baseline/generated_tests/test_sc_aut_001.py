"""LLM ile üretilmiş test — H3-05 / Issue #31. ELLE DÜZENLEMEYİN.
Senaryo: SC-AUT-001 · Model: groq/openai/gpt-oss-120b · Prompt: pytest_v1
Beklenen durum kodu bağımsız referanstan (ground_truth.secure_status) alınmıştır.
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

pytestmark = pytest.mark.django_db

def test_sc_aut_001(seeded_db, api_client):
    url = reverse("article-list")
    payload = {"title": "Örnek Başlık", "body": "örnek içerik"}
    response = api_client.post(url, payload, format="json")
    assert response.status_code == 401
