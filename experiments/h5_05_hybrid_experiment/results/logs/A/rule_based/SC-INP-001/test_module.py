import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_inp_001_post_user_400(seeded_db, api_client):
    """SC-INP-001 · POST /api/articles/ · user (carol; fixture ilişkisi: kimligi_dogrulanmis) · beklenen 400
    
    Beklenen davranış: Zorunlu 'title' alanı eksik -> 400.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: INPUT_VALIDATION
    Endpoint: EP-ARTICLE-LIST (article-list), işlem: create; yan etki kuralı: count_unchanged
    """
    api_client.force_authenticate(user=User.objects.get(username='carol'))
    url = reverse('article-list')
    assert url == '/api/articles/', route_message('SC-INP-001', '/api/articles/', url)
    before_count = model_count('catalog.Article')
    response = api_client.post(url, {'body': 'x'}, format='json')
    assert response.status_code == 400, status_message('SC-INP-001', 400, response, "Zorunlu 'title' alanı eksik -> 400.")
    after_count = model_count('catalog.Article')
    assert after_count == before_count, side_effect_message('SC-INP-001', 'count_unchanged', before_count, after_count)
