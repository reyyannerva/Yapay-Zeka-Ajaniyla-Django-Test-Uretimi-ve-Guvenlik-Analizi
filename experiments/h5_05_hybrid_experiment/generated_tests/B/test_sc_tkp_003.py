"""Hibrit nihai test — H5-05 / #43. Kaynak: hybrid<-rule_based:experiments/h5_05_hybrid_experiment/layer_b/generated/rule_based/generated_tests/test_patch_generated.py::test_sc_tkp_003_patch_anonymous_401. ELLE DÜZENLEMEYİN."""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_tkp_003_patch_anonymous_401(seeded_db, api_client):
    """SC-TKP-003 · PATCH /api/tasks/1/ · anonim · beklenen 401
    
    Beklenen davranış: Anonim kullanıcı görevi PATCH ile değiştiremez (kimlik doğrulama gerekli).
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHENTICATION
    Endpoint: EP-TASK-DETAIL (task-detail), işlem: partial_update; yan etki kuralı: resource_unchanged
    """
    url = reverse('task-detail', kwargs={'pk': 1})
    assert url == '/api/tasks/1/', route_message('SC-TKP-003', '/api/tasks/1/', url)
    before = snapshot('tasks.Task', 1, ['title', 'notes', 'is_done'])
    response = api_client.patch(url, {'is_done': True}, format='json')
    assert response.status_code == 401, status_message('SC-TKP-003', 401, response, 'Anonim kullanıcı görevi PATCH ile değiştiremez (kimlik doğrulama gerekli).')
    after = snapshot('tasks.Task', 1, ['title', 'notes', 'is_done'])
    assert after == before, side_effect_message('SC-TKP-003', 'resource_unchanged', before, after)
