import pytest
from django.contrib.auth.models import User
from django.urls import reverse

pytestmark = pytest.mark.django_db

def test_sc_auz_002(seeded_db, api_client):
    user = User.objects.get(username="carol")
    api_client.force_authenticate(user=user)
    url = reverse("article-detail", kwargs={"pk": 1})
    payload = {"title": "Örnek Başlık"}
    response = api_client.patch(url, payload, format="json")
    assert response.status_code == 403
