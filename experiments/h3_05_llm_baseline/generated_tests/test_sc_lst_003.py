"""LLM ile üretilmiş test — H3-05 / Issue #31. ELLE DÜZENLEMEYİN.
Senaryo: SC-LST-003 · Model: groq/openai/gpt-oss-120b · Prompt: pytest_v1
Beklenen durum kodu bağımsız referanstan (ground_truth.secure_status) alınmıştır.
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

pytestmark = pytest.mark.django_db

def test_sc_lst_003(seeded_db, api_client):
    admin_user = User.objects.get(username="admin")
    api_client.force_authenticate(user=admin_user)
    url = reverse("article-list")
    response = api_client.get(url, format="json")
    assert response.status_code == 200
