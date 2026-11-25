import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_tkp_004_patch_admin_200(seeded_db, api_client):
    """SC-TKP-004 · PATCH /api/tasks/2/ · admin (yonetici; fixture ilişkisi: yonetici) · beklenen 200
    
    Beklenen davranış: Yönetici herhangi bir görevi PATCH ile güncelleyebilir.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHORIZATION
    Endpoint: EP-TASK-DETAIL (task-detail), işlem: partial_update; yan etki kuralı: partial_update_applied
    """
    api_client.force_authenticate(user=User.objects.get(username='yonetici'))
    url = reverse('task-detail', kwargs={'pk': 2})
    assert url == '/api/tasks/2/', route_message('SC-TKP-004', '/api/tasks/2/', url)
    before = snapshot('tasks.Task', 2, ['title', 'notes', 'is_done'])
    response = api_client.patch(url, {'notes': 'yönetici notu'}, format='json')
    assert response.status_code == 200, status_message('SC-TKP-004', 200, response, 'Yönetici herhangi bir görevi PATCH ile güncelleyebilir.')
    after = snapshot('tasks.Task', 2, ['title', 'notes', 'is_done'])
    expected_after = {**before, **{'notes': 'yönetici notu'}}
    assert after == expected_after, side_effect_message('SC-TKP-004', 'partial_update_applied', expected_after, after)
