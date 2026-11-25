import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_ret_004_get_admin_200(seeded_db, api_client):
    """SC-RET-004 · GET /api/articles/2/ · admin (admin; fixture ilişkisi: yonetici) · beklenen 200
    
    Beklenen davranış: Yönetici herhangi bir taslağı görüntüleyebilir.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: retrieve; yan etki kuralı: none
    """
    api_client.force_authenticate(user=User.objects.get(username='admin'))
    url = reverse('article-detail', kwargs={'pk': 2})
    assert url == '/api/articles/2/', route_message('SC-RET-004', '/api/articles/2/', url)
    response = api_client.get(url)
    assert response.status_code == 200, status_message('SC-RET-004', 200, response, 'Yönetici herhangi bir taslağı görüntüleyebilir.')
