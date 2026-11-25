import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_ret_002_get_anonymous_404(seeded_db, api_client):
    """SC-RET-002 · GET /api/articles/2/ · anonim · beklenen 404
    
    Beklenen davranış: Taslak kayıt anonim kullanıcıya görünmez (queryset dışı -> 404).
    Referans: ground_truth.json (FIXTURE_DESIGN, verified); kategori: AUTHORIZATION
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: retrieve; yan etki kuralı: none
    """
    url = reverse('article-detail', kwargs={'pk': 2})
    assert url == '/api/articles/2/', route_message('SC-RET-002', '/api/articles/2/', url)
    response = api_client.get(url)
    assert response.status_code == 404, status_message('SC-RET-002', 404, response, 'Taslak kayıt anonim kullanıcıya görünmez (queryset dışı -> 404).')
