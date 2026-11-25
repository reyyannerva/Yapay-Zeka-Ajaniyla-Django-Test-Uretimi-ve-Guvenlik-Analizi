"""LLM ile üretilmiş test — H3-05 / Issue #31. ELLE DÜZENLEMEYİN.
Senaryo: SC-TKX-004 · Model: groq/openai/gpt-oss-120b · Prompt: pytest_v1
Beklenen durum kodu bağımsız referanstan (ground_truth.secure_status) alınmıştır.
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

pytestmark = pytest.mark.django_db

def test_sc_tkx_004(seeded_db, api_client):
    user = User.objects.get(username="ayse")
    api_client.force_authenticate(user=user)
    url = reverse("legacy-task-detail", kwargs={"pk": 1})
    payload = {"notes": "sahip notu"}
    response = api_client.patch(url, payload, format="json")
    assert response.status_code == 200
