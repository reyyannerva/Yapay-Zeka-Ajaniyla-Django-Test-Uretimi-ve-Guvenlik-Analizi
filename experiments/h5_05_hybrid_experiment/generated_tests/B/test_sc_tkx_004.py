"""Hibrit nihai test — H5-05 / #43. Kaynak: hybrid<-rule_based:experiments/h5_05_hybrid_experiment/layer_b/generated/rule_based/generated_tests/test_patch_generated.py::test_sc_tkx_004_patch_owner_200. ELLE DÜZENLEMEYİN."""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_tkx_004_patch_owner_200(seeded_db, api_client):
    """SC-TKX-004 · PATCH /api/legacy/tasks/1/ · owner (ayse; fixture ilişkisi: kaynak_sahibi) · beklenen 200
    
    Beklenen davranış: Sahip kendi görevini PATCH ile günceller.
    Referans: ground_truth.json (PROJECT_REQUIREMENT, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-LEGACY-TASK-DETAIL (legacy-task-detail), işlem: partial_update; yan etki kuralı: partial_update_applied
    """
    api_client.force_authenticate(user=User.objects.get(username='ayse'))
    url = reverse('legacy-task-detail', kwargs={'pk': 1})
    assert url == '/api/legacy/tasks/1/', route_message('SC-TKX-004', '/api/legacy/tasks/1/', url)
    before = snapshot('tasks.Task', 1, ['title', 'notes', 'is_done'])
    response = api_client.patch(url, {'notes': 'sahip notu'}, format='json')
    assert response.status_code == 200, status_message('SC-TKX-004', 200, response, 'Sahip kendi görevini PATCH ile günceller.')
    after = snapshot('tasks.Task', 1, ['title', 'notes', 'is_done'])
    expected_after = {**before, **{'notes': 'sahip notu'}}
    assert after == expected_after, side_effect_message('SC-TKX-004', 'partial_update_applied', expected_after, after)
