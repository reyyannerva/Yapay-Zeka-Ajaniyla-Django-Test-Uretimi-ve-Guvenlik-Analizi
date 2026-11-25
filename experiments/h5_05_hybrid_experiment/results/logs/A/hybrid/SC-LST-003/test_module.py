import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_lst_003_get_admin_200(seeded_db, api_client):
    """SC-LST-003 · GET /api/articles/ · admin (admin; fixture ilişkisi: yonetici) · beklenen 200
    
    Beklenen davranış: Yönetici tüm kayıtları listeler.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-LIST (article-list), işlem: list; yan etki kuralı: none
    """
    api_client.force_authenticate(user=User.objects.get(username='admin'))
    url = reverse('article-list')
    assert url == '/api/articles/', route_message('SC-LST-003', '/api/articles/', url)
    response = api_client.get(url)
    assert response.status_code == 200, status_message('SC-LST-003', 200, response, 'Yönetici tüm kayıtları listeler.')
