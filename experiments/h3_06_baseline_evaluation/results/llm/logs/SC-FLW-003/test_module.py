import pytest
from django.contrib.auth.models import User
from django.urls import reverse

pytestmark = pytest.mark.django_db

def test_sc_flw_003(seeded_db, api_client):
    url = reverse("insecure-article-list")
    response = api_client.get(url, format="json")
    assert response.status_code == 200
