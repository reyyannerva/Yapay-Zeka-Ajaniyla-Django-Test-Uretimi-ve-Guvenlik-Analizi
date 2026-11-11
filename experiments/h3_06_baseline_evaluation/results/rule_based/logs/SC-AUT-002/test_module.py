import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_aut_002_put_anonymous_401(seeded_db, api_client):
    """SC-AUT-002 · PUT /api/articles/1/ · anonim · beklenen 401
    
    Beklenen davranış: Anonim kullanıcı güncelleme yapamaz.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHENTICATION
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: update; yan etki kuralı: resource_unchanged
    """
    url = reverse('article-detail', kwargs={'pk': 1})
    assert url == '/api/articles/1/', route_message('SC-AUT-002', '/api/articles/1/', url)
    before = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    response = api_client.put(url, {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 401, status_message('SC-AUT-002', 401, response, 'Anonim kullanıcı güncelleme yapamaz.')
    after = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    assert after == before, side_effect_message('SC-AUT-002', 'resource_unchanged', before, after)
