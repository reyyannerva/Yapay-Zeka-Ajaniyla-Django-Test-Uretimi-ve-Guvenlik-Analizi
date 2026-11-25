import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_auz_004_post_user_403(seeded_db, api_client):
    """SC-AUZ-004 · POST /api/articles/2/publish/ · user (carol; fixture ilişkisi: sahip_olmayan) · beklenen 403
    
    Beklenen davranış: Sahip olmayan kullanıcı başkasının kaydını yayınlayamaz.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHORIZATION
    Endpoint: EP-ARTICLE-PUBLISH (article-publish), işlem: custom_action; yan etki kuralı: none
    """
    api_client.force_authenticate(user=User.objects.get(username='carol'))
    url = reverse('article-publish', kwargs={'pk': 2})
    assert url == '/api/articles/2/publish/', route_message('SC-AUZ-004', '/api/articles/2/publish/', url)
    response = api_client.post(url, format='json')
    assert response.status_code == 403, status_message('SC-AUZ-004', 403, response, 'Sahip olmayan kullanıcı başkasının kaydını yayınlayamaz.')
