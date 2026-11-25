import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_tku_002_put_user_403(seeded_db, api_client):
    """SC-TKU-002 · PUT /api/tasks/1/ · user (mehmet; fixture ilişkisi: sahip_olmayan) · beklenen 403
    
    Beklenen davranış: Sahibi olmayan kullanıcı başkasının görevini PUT ile değiştiremez.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHORIZATION
    Endpoint: EP-TASK-DETAIL (task-detail), işlem: update; yan etki kuralı: resource_unchanged
    """
    api_client.force_authenticate(user=User.objects.get(username='mehmet'))
    url = reverse('task-detail', kwargs={'pk': 1})
    assert url == '/api/tasks/1/', route_message('SC-TKU-002', '/api/tasks/1/', url)
    before = snapshot('tasks.Task', 1, ['title', 'notes', 'is_done'])
    response = api_client.put(url, {'is_done': True, 'notes': '', 'title': 'Ele geçirme'}, format='json')
    assert response.status_code == 403, status_message('SC-TKU-002', 403, response, 'Sahibi olmayan kullanıcı başkasının görevini PUT ile değiştiremez.')
    after = snapshot('tasks.Task', 1, ['title', 'notes', 'is_done'])
    assert after == before, side_effect_message('SC-TKU-002', 'resource_unchanged', before, after)
