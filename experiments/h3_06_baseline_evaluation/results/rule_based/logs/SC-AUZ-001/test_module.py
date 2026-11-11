import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_auz_001_put_user_403(seeded_db, api_client):
    """SC-AUZ-001 · PUT /api/articles/1/ · user (carol; fixture ilişkisi: sahip_olmayan) · beklenen 403
    
    Beklenen davranış: Sahip olmayan kullanıcı başkasının kaydını güncelleyemez.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHORIZATION
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: update; yan etki kuralı: resource_unchanged
    """
    api_client.force_authenticate(user=User.objects.get(username='carol'))
    url = reverse('article-detail', kwargs={'pk': 1})
    assert url == '/api/articles/1/', route_message('SC-AUZ-001', '/api/articles/1/', url)
    before = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    response = api_client.put(url, {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 403, status_message('SC-AUZ-001', 403, response, 'Sahip olmayan kullanıcı başkasının kaydını güncelleyemez.')
    after = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    assert after == before, side_effect_message('SC-AUZ-001', 'resource_unchanged', before, after)
