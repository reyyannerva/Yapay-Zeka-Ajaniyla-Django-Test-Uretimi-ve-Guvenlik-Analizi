"""Hibrit nihai test — H5-05 / #43. Kaynak: hybrid<-rule_based:experiments/h5_05_hybrid_experiment/layer_b/generated/rule_based/generated_tests/test_put_generated.py::test_sc_tku_001_put_owner_200. ELLE DÜZENLEMEYİN."""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_tku_001_put_owner_200(seeded_db, api_client):
    """SC-TKU-001 · PUT /api/tasks/1/ · owner (ayse; fixture ilişkisi: kaynak_sahibi) · beklenen 200
    
    Beklenen davranış: Sahip görevini PUT ile tamamen günceller.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-TASK-DETAIL (task-detail), işlem: update; yan etki kuralı: update_applied
    """
    api_client.force_authenticate(user=User.objects.get(username='ayse'))
    url = reverse('task-detail', kwargs={'pk': 1})
    assert url == '/api/tasks/1/', route_message('SC-TKU-001', '/api/tasks/1/', url)
    before = snapshot('tasks.Task', 1, ['title', 'notes', 'is_done'])
    response = api_client.put(url, {'is_done': True, 'notes': 'tam güncelleme', 'title': 'Rapor (güncel)'}, format='json')
    assert response.status_code == 200, status_message('SC-TKU-001', 200, response, 'Sahip görevini PUT ile tamamen günceller.')
    after = snapshot('tasks.Task', 1, ['title', 'notes', 'is_done'])
    observed = {key: after[key] for key in ['is_done', 'notes', 'title']} if after else None
    assert observed == {'is_done': True, 'notes': 'tam güncelleme', 'title': 'Rapor (güncel)'}, side_effect_message('SC-TKU-001', 'update_applied', {'is_done': True, 'notes': 'tam güncelleme', 'title': 'Rapor (güncel)'}, observed)
