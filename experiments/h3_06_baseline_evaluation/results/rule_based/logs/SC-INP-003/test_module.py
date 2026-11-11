import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_inp_003_put_owner_400(seeded_db, api_client):
    """SC-INP-003 · PUT /api/articles/1/ · owner (alice; fixture ilişkisi: kaynak_sahibi) · beklenen 400
    
    Beklenen davranış: PUT'ta zorunlu 'title' eksik -> 400.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: INPUT_VALIDATION
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: update; yan etki kuralı: resource_unchanged
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-detail', kwargs={'pk': 1})
    assert url == '/api/articles/1/', route_message('SC-INP-003', '/api/articles/1/', url)
    before = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    response = api_client.put(url, {'body': 'x'}, format='json')
    assert response.status_code == 400, status_message('SC-INP-003', 400, response, "PUT'ta zorunlu 'title' eksik -> 400.")
    after = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    assert after == before, side_effect_message('SC-INP-003', 'resource_unchanged', before, after)
