import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_tkd_001_delete_owner_204(seeded_db, api_client):
    """SC-TKD-001 · DELETE /api/tasks/1/ · owner (ayse; fixture ilişkisi: kaynak_sahibi) · beklenen 204
    
    Beklenen davranış: Sahip kendi görevini siler.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-TASK-DETAIL (task-detail), işlem: destroy; yan etki kuralı: resource_deleted
    """
    api_client.force_authenticate(user=User.objects.get(username='ayse'))
    url = reverse('task-detail', kwargs={'pk': 1})
    assert url == '/api/tasks/1/', route_message('SC-TKD-001', '/api/tasks/1/', url)
    before = snapshot('tasks.Task', 1, ['title', 'notes', 'is_done'])
    response = api_client.delete(url)
    assert response.status_code == 204, status_message('SC-TKD-001', 204, response, 'Sahip kendi görevini siler.')
    after = snapshot('tasks.Task', 1, ['title', 'notes', 'is_done'])
    assert after is None, side_effect_message('SC-TKD-001', 'resource_deleted', None, after)
