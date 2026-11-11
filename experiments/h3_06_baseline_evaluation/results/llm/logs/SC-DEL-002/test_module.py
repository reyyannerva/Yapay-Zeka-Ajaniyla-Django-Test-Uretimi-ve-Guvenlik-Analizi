import pytest
from django.contrib.auth.models import User
from django.urls import reverse

pytestmark = pytest.mark.django_db

def test_sc_del_002(seeded_db, api_client):
    admin_user = User.objects.get(username="admin")
    api_client.force_authenticate(user=admin_user)
    url = reverse("article-detail", kwargs={"pk": 3})
    response = api_client.delete(url, format="json")
    assert response.status_code == 204
