import pytest
from django.contrib.auth.models import User
from django.urls import reverse

pytestmark = pytest.mark.django_db

def test_sc_tkd_001(seeded_db, api_client):
    user = User.objects.get(username="ayse")
    api_client.force_authenticate(user=user)
    url = reverse("task-detail", kwargs={"pk": 1})
    response = api_client.delete(url, format="json")
    assert response.status_code == 204
