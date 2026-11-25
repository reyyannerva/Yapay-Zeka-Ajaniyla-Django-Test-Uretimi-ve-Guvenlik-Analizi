import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_tkc_001_post_user_201(seeded_db, api_client):
    """SC-TKC-001 · POST /api/tasks/ · user (mehmet; fixture ilişkisi: kimligi_dogrulanmis) · beklenen 201
    
    Beklenen davranış: Kimliği doğrulanmış kullanıcı geçerli girdiyle görev oluşturur; sahip isteği yapan olur.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-TASK-LIST (task-list), işlem: create; yan etki kuralı: count_plus_one
    """
    api_client.force_authenticate(user=User.objects.get(username='mehmet'))
    url = reverse('task-list')
    assert url == '/api/tasks/', route_message('SC-TKC-001', '/api/tasks/', url)
    before_count = model_count('tasks.Task')
    response = api_client.post(url, {'notes': 'örnek', 'title': 'Yeni görev'}, format='json')
    assert response.status_code == 201, status_message('SC-TKC-001', 201, response, 'Kimliği doğrulanmış kullanıcı geçerli girdiyle görev oluşturur; sahip isteği yapan olur.')
    after_count = model_count('tasks.Task')
    assert after_count == before_count + 1, side_effect_message('SC-TKC-001', 'count_plus_one', before_count + 1, after_count)
