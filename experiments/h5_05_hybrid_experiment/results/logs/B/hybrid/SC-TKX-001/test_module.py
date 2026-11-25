import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_tkx_001_put_user_403(seeded_db, api_client):
    """SC-TKX-001 · PUT /api/legacy/tasks/1/ · user (mehmet; fixture ilişkisi: sahip_olmayan) · beklenen 403
    
    Beklenen davranış: Sahibi olmayan kullanıcı başkasının görevini PUT ile değiştiremez.
    Referans: ground_truth.json (PROJECT_REQUIREMENT, verified); kategori: AUTHORIZATION
    Endpoint: EP-LEGACY-TASK-DETAIL (legacy-task-detail), işlem: update; yan etki kuralı: resource_unchanged
    """
    api_client.force_authenticate(user=User.objects.get(username='mehmet'))
    url = reverse('legacy-task-detail', kwargs={'pk': 1})
    assert url == '/api/legacy/tasks/1/', route_message('SC-TKX-001', '/api/legacy/tasks/1/', url)
    before = snapshot('tasks.Task', 1, ['title', 'notes', 'is_done'])
    response = api_client.put(url, {'is_done': True, 'notes': '', 'title': 'Ele geçirme'}, format='json')
    assert response.status_code == 403, status_message('SC-TKX-001', 403, response, 'Sahibi olmayan kullanıcı başkasının görevini PUT ile değiştiremez.')
    after = snapshot('tasks.Task', 1, ['title', 'notes', 'is_done'])
    assert after == before, side_effect_message('SC-TKX-001', 'resource_unchanged', before, after)
