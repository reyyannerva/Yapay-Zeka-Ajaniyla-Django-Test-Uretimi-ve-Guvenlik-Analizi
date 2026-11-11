"""LLM ile üretilmiş test — H3-05 / Issue #31. ELLE DÜZENLEMEYİN.
Senaryo: SC-UPD-002 · Model: groq/openai/gpt-oss-120b · Prompt: pytest_v1
Beklenen durum kodu bağımsız referanstan (ground_truth.secure_status) alınmıştır.
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

pytestmark = pytest.mark.django_db

def test_sc_upd_002(seeded_db, api_client):
    admin_user = User.objects.get(username="admin")
    api_client.force_authenticate(user=admin_user)

    url = reverse("article-detail", kwargs={"pk": 3})
    payload = {"title": "Örnek Başlık", "body": "örnek içerik"}

    response = api_client.put(url, payload, format="json")
    assert response.status_code == 200
