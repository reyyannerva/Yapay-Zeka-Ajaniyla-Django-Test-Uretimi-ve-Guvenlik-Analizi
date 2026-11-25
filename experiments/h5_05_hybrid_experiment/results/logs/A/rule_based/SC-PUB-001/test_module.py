import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_pub_001_post_owner_200(seeded_db, api_client):
    """SC-PUB-001 · POST /api/articles/2/publish/ · owner (alice; fixture ilişkisi: kaynak_sahibi) · beklenen 200
    
    Beklenen davranış: Sahip kendi taslağını yayınlar (is_published=true).
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHORIZATION
    Endpoint: EP-ARTICLE-PUBLISH (article-publish), işlem: custom_action; yan etki kuralı: none
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-publish', kwargs={'pk': 2})
    assert url == '/api/articles/2/publish/', route_message('SC-PUB-001', '/api/articles/2/publish/', url)
    response = api_client.post(url, format='json')
    assert response.status_code == 200, status_message('SC-PUB-001', 200, response, 'Sahip kendi taslağını yayınlar (is_published=true).')
