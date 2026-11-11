import pytest
from django.contrib.auth.models import User
from django.urls import reverse

pytestmark = pytest.mark.django_db

def test_sc_upd_004(seeded_db, api_client):
    # Authenticate as admin user
    admin_user = User.objects.get(username="admin")
    api_client.force_authenticate(user=admin_user)

    # Prepare request
    url = reverse("article-detail", kwargs={"pk": 3})
    payload = {"title": "Örnek Başlık"}

    # Send PATCH request
    response = api_client.patch(url, payload, format="json")

    # Verify response
    assert response.status_code == 200
