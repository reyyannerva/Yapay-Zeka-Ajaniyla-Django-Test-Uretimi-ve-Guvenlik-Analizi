import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_del_001_delete_owner_204(seeded_db, api_client):
    """SC-DEL-001 · DELETE /api/articles/1/ · owner (alice; fixture ilişkisi: kaynak_sahibi) · beklenen 204
    
    Beklenen davranış: Sahip kendi kaydını siler (204).
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: destroy; yan etki kuralı: resource_deleted
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-detail', kwargs={'pk': 1})
    assert url == '/api/articles/1/', route_message('SC-DEL-001', '/api/articles/1/', url)
    before = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    response = api_client.delete(url)
    assert response.status_code == 204, status_message('SC-DEL-001', 204, response, 'Sahip kendi kaydını siler (204).')
    after = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    assert after is None, side_effect_message('SC-DEL-001', 'resource_deleted', None, after)
