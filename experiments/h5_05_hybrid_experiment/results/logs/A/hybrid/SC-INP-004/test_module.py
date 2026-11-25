import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_inp_004_post_user_400(seeded_db, api_client):
    """SC-INP-004 · POST /api/articles/ · user (carol; fixture ilişkisi: kimligi_dogrulanmis) · beklenen 400
    
    Beklenen davranış: Başlık max_length=200 sınırını aşıyor (201 karakter) -> 400.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: INPUT_VALIDATION
    Endpoint: EP-ARTICLE-LIST (article-list), işlem: create; yan etki kuralı: count_unchanged
    """
    api_client.force_authenticate(user=User.objects.get(username='carol'))
    url = reverse('article-list')
    assert url == '/api/articles/', route_message('SC-INP-004', '/api/articles/', url)
    before_count = model_count('catalog.Article')
    response = api_client.post(url, {'body': 'x', 'title': 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'}, format='json')
    assert response.status_code == 400, status_message('SC-INP-004', 400, response, 'Başlık max_length=200 sınırını aşıyor (201 karakter) -> 400.')
    after_count = model_count('catalog.Article')
    assert after_count == before_count, side_effect_message('SC-INP-004', 'count_unchanged', before_count, after_count)
