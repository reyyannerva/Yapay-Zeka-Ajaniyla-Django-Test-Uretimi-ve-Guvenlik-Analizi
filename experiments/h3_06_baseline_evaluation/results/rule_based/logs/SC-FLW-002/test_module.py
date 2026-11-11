import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_flw_002_delete_user_403(seeded_db, api_client):
    """SC-FLW-002 · DELETE /api/insecure/articles/3/ · user (carol; fixture ilişkisi: sahip_olmayan) · beklenen 403
    
    Beklenen davranış: Sahip olmayan kullanıcı başkasının kaydını silememeli (403).
    Referans: ground_truth.json (PROJECT_REQUIREMENT, verified); kategori: AUTHORIZATION
    Endpoint: EP-INSECURE-ARTICLE-DETAIL (insecure-article-detail), işlem: destroy; yan etki kuralı: resource_unchanged
    Bilinen güvenlik kusuru: Broken Object Level Authorization (BOLA/IDOR, OWASP API1:2023) — güvensiz uçta gözlenen 204 (status sapması).
    """
    api_client.force_authenticate(user=User.objects.get(username='carol'))
    url = reverse('insecure-article-detail', kwargs={'pk': 3})
    assert url == '/api/insecure/articles/3/', route_message('SC-FLW-002', '/api/insecure/articles/3/', url)
    before = snapshot('catalog.Article', 3, ['title', 'body', 'is_published'])
    response = api_client.delete(url)
    assert response.status_code == 403, status_message('SC-FLW-002', 403, response, 'Sahip olmayan kullanıcı başkasının kaydını silememeli (403).')
    after = snapshot('catalog.Article', 3, ['title', 'body', 'is_published'])
    assert after == before, side_effect_message('SC-FLW-002', 'resource_unchanged', before, after)
