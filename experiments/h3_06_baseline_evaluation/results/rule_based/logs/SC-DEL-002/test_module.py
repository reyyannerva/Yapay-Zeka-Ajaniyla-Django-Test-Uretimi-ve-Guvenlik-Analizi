import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_del_002_delete_admin_204(seeded_db, api_client):
    """SC-DEL-002 · DELETE /api/articles/3/ · admin (admin; fixture ilişkisi: yonetici) · beklenen 204
    
    Beklenen davranış: Yönetici herhangi bir kaydı siler (204).
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: destroy; yan etki kuralı: resource_deleted
    """
    api_client.force_authenticate(user=User.objects.get(username='admin'))
    url = reverse('article-detail', kwargs={'pk': 3})
    assert url == '/api/articles/3/', route_message('SC-DEL-002', '/api/articles/3/', url)
    before = snapshot('catalog.Article', 3, ['title', 'body', 'is_published'])
    response = api_client.delete(url)
    assert response.status_code == 204, status_message('SC-DEL-002', 204, response, 'Yönetici herhangi bir kaydı siler (204).')
    after = snapshot('catalog.Article', 3, ['title', 'body', 'is_published'])
    assert after is None, side_effect_message('SC-DEL-002', 'resource_deleted', None, after)
