import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_tkp_001_patch_owner_200(seeded_db, api_client):
    """SC-TKP-001 · PATCH /api/tasks/1/ · owner (ayse; fixture ilişkisi: kaynak_sahibi) · beklenen 200
    
    Beklenen davranış: Sahip görevini PATCH ile kısmen günceller; gövdede olmayan alanlar korunur.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-TASK-DETAIL (task-detail), işlem: partial_update; yan etki kuralı: partial_update_applied
    """
    api_client.force_authenticate(user=User.objects.get(username='ayse'))
    url = reverse('task-detail', kwargs={'pk': 1})
    assert url == '/api/tasks/1/', route_message('SC-TKP-001', '/api/tasks/1/', url)
    before = snapshot('tasks.Task', 1, ['title', 'notes', 'is_done'])
    response = api_client.patch(url, {'is_done': True}, format='json')
    assert response.status_code == 200, status_message('SC-TKP-001', 200, response, 'Sahip görevini PATCH ile kısmen günceller; gövdede olmayan alanlar korunur.')
    after = snapshot('tasks.Task', 1, ['title', 'notes', 'is_done'])
    expected_after = {**before, **{'is_done': True}}
    assert after == expected_after, side_effect_message('SC-TKP-001', 'partial_update_applied', expected_after, after)
