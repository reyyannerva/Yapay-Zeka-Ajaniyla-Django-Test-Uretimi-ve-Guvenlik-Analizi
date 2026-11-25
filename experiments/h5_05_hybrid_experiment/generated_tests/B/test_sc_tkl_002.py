"""Hibrit nihai test — H5-05 / #43. Kaynak: hybrid<-rule_based:experiments/h5_05_hybrid_experiment/layer_b/generated/rule_based/generated_tests/test_get_generated.py::test_sc_tkl_002_get_anonymous_401. ELLE DÜZENLEMEYİN."""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_tkl_002_get_anonymous_401(seeded_db, api_client):
    """SC-TKL-002 · GET /api/tasks/ · anonim · beklenen 401
    
    Beklenen davranış: Anonim kullanıcı görev listesine erişemez (kimlik doğrulama gerekli).
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHENTICATION
    Endpoint: EP-TASK-LIST (task-list), işlem: list; yan etki kuralı: none
    """
    url = reverse('task-list')
    assert url == '/api/tasks/', route_message('SC-TKL-002', '/api/tasks/', url)
    response = api_client.get(url)
    assert response.status_code == 401, status_message('SC-TKL-002', 401, response, 'Anonim kullanıcı görev listesine erişemez (kimlik doğrulama gerekli).')
