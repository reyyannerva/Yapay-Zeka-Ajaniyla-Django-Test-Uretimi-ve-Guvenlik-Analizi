"""Hibrit nihai test — H5-05 / #43. Kaynak: hybrid<-rule_based:experiments/h5_05_hybrid_experiment/layer_b/generated/rule_based/generated_tests/test_post_generated.py::test_sc_tkc_002_post_user_400. ELLE DÜZENLEMEYİN."""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_tkc_002_post_user_400(seeded_db, api_client):
    """SC-TKC-002 · POST /api/tasks/ · user (mehmet; fixture ilişkisi: kimligi_dogrulanmis) · beklenen 400
    
    Beklenen davranış: Zorunlu title alanı eksik görev oluşturulamaz.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: INPUT_VALIDATION
    Endpoint: EP-TASK-LIST (task-list), işlem: create; yan etki kuralı: count_unchanged
    """
    api_client.force_authenticate(user=User.objects.get(username='mehmet'))
    url = reverse('task-list')
    assert url == '/api/tasks/', route_message('SC-TKC-002', '/api/tasks/', url)
    before_count = model_count('tasks.Task')
    response = api_client.post(url, {'notes': 'başlık yok'}, format='json')
    assert response.status_code == 400, status_message('SC-TKC-002', 400, response, 'Zorunlu title alanı eksik görev oluşturulamaz.')
    after_count = model_count('tasks.Task')
    assert after_count == before_count, side_effect_message('SC-TKC-002', 'count_unchanged', before_count, after_count)
