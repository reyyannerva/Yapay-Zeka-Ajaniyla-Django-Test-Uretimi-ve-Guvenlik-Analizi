import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_tkl_001_get_user_200(seeded_db, api_client):
    """SC-TKL-001 · GET /api/tasks/ · user (mehmet; fixture ilişkisi: kimligi_dogrulanmis) · beklenen 200
    
    Beklenen davranış: Kimliği doğrulanmış kullanıcı görev listesini görür.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-TASK-LIST (task-list), işlem: list; yan etki kuralı: none
    """
    api_client.force_authenticate(user=User.objects.get(username='mehmet'))
    url = reverse('task-list')
    assert url == '/api/tasks/', route_message('SC-TKL-001', '/api/tasks/', url)
    response = api_client.get(url)
    assert response.status_code == 200, status_message('SC-TKL-001', 200, response, 'Kimliği doğrulanmış kullanıcı görev listesini görür.')
