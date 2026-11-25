"""Hibrit nihai test — H5-05 / #43. Kaynak: hybrid<-rule_based:experiments/h5_05_hybrid_experiment/layer_b/generated/rule_based/generated_tests/test_get_generated.py::test_sc_tkx_005_get_owner_200. ELLE DÜZENLEMEYİN."""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_tkx_005_get_owner_200(seeded_db, api_client):
    """SC-TKX-005 · GET /api/legacy/tasks/1/ · owner (ayse; fixture ilişkisi: kaynak_sahibi) · beklenen 200
    
    Beklenen davranış: Sahip kendi görevini görüntüler.
    Referans: ground_truth.json (PROJECT_REQUIREMENT, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-LEGACY-TASK-DETAIL (legacy-task-detail), işlem: retrieve; yan etki kuralı: none
    """
    api_client.force_authenticate(user=User.objects.get(username='ayse'))
    url = reverse('legacy-task-detail', kwargs={'pk': 1})
    assert url == '/api/legacy/tasks/1/', route_message('SC-TKX-005', '/api/legacy/tasks/1/', url)
    response = api_client.get(url)
    assert response.status_code == 200, status_message('SC-TKX-005', 200, response, 'Sahip kendi görevini görüntüler.')
