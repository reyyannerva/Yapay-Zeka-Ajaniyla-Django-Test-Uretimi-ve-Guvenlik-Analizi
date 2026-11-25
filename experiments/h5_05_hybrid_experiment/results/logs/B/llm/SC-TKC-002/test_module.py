import pytest
from django.contrib.auth.models import User
from django.urls import reverse

pytestmark = pytest.mark.django_db

def test_sc_tkc_002(seeded_db, api_client):
    user = User.objects.get(username="mehmet")
    api_client.force_authenticate(user=user)
    url = reverse("task-list")
    payload = {"notes": "başlık yok"}
    response = api_client.post(url, payload, format="json")
    assert response.status_code == 400
