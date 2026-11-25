import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_aut_005_post_anonymous_401(seeded_db, api_client):
    """SC-AUT-005 · POST /api/articles/2/publish/ · anonim · beklenen 401
    
    Beklenen davranış: Anonim kullanıcı yayınlama yapamaz.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHENTICATION
    Endpoint: EP-ARTICLE-PUBLISH (article-publish), işlem: custom_action; yan etki kuralı: none
    """
    url = reverse('article-publish', kwargs={'pk': 2})
    assert url == '/api/articles/2/publish/', route_message('SC-AUT-005', '/api/articles/2/publish/', url)
    response = api_client.post(url, format='json')
    assert response.status_code == 401, status_message('SC-AUT-005', 401, response, 'Anonim kullanıcı yayınlama yapamaz.')
