import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_upd_004_patch_admin_200(seeded_db, api_client):
    """SC-UPD-004 · PATCH /api/articles/3/ · admin (admin; fixture ilişkisi: yonetici) · beklenen 200
    
    Beklenen davranış: Yönetici herhangi bir kaydı kısmen günceller.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: partial_update; yan etki kuralı: partial_update_applied
    """
    api_client.force_authenticate(user=User.objects.get(username='admin'))
    url = reverse('article-detail', kwargs={'pk': 3})
    assert url == '/api/articles/3/', route_message('SC-UPD-004', '/api/articles/3/', url)
    before = snapshot('catalog.Article', 3, ['title', 'body', 'is_published'])
    response = api_client.patch(url, {'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 200, status_message('SC-UPD-004', 200, response, 'Yönetici herhangi bir kaydı kısmen günceller.')
    after = snapshot('catalog.Article', 3, ['title', 'body', 'is_published'])
    expected_after = {**before, **{'title': 'Örnek Başlık'}}
    assert after == expected_after, side_effect_message('SC-UPD-004', 'partial_update_applied', expected_after, after)
