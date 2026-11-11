import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_upd_003_patch_owner_200(seeded_db, api_client):
    """SC-UPD-003 · PATCH /api/articles/1/ · owner (alice; fixture ilişkisi: kaynak_sahibi) · beklenen 200
    
    Beklenen davranış: Sahip kendi kaydını kısmen günceller.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: partial_update; yan etki kuralı: partial_update_applied
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-detail', kwargs={'pk': 1})
    assert url == '/api/articles/1/', route_message('SC-UPD-003', '/api/articles/1/', url)
    before = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    response = api_client.patch(url, {'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 200, status_message('SC-UPD-003', 200, response, 'Sahip kendi kaydını kısmen günceller.')
    after = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    expected_after = {**before, **{'title': 'Örnek Başlık'}}
    assert after == expected_after, side_effect_message('SC-UPD-003', 'partial_update_applied', expected_after, after)
