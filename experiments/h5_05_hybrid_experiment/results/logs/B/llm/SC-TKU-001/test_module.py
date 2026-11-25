import pytest
from django.contrib.auth.models import User
from django.urls import reverse

pytestmark = pytest.mark.django_db

def test_sc_tku_001(seeded_db, api_client):
    user = User.objects.get(username="ayse")
    api_client.force_authenticate(user=user)

    url = reverse("task-detail", kwargs={"pk": 1})
    payload = {
        "title": "Rapor (güncel)",
        "notes": "tam güncelleme",
        "is_done": True,
    }

    response = api_client.put(url, payload, format="json")
    assert response.status_code == 200
