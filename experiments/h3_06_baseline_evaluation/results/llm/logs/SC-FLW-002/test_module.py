import pytest
from django.contrib.auth.models import User
from django.urls import reverse

pytestmark = pytest.mark.django_db

def test_sc_flw_002(seeded_db, api_client):
    user = User.objects.get(username="carol")
    api_client.force_authenticate(user=user)
    url = reverse("insecure-article-detail", kwargs={"pk": 3})
    response = api_client.delete(url, format="json")
    assert response.status_code == 403
