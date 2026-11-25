"""PATCH senaryoları için kural tabanlı üretilmiş Pytest testleri — H3-04 / Issue #30.

BU DOSYA OTOMATİK ÜRETİLMİŞTİR; ELLE DÜZENLEMEYİN. Yeniden üretmek için:
    python -m agent.test_generation.rule_based generate

Üretici: agent.test_generation.rule_based v1.0.0 (LLM kullanılmaz).
Beklenen durum kodları bağımsız referanstan (ground_truth.json → secure_status) alınmıştır.
Girdi özetleri (SHA-256):
    experiments/h5_05_hybrid_experiment/layer_b/endpoint_summary.json: 9f4bd7729e95c0e17853a1b63800e307f4eca14418fac01412491600215b28ce
    experiments/h5_05_hybrid_experiment/layer_b/generator_inputs/reference_requirements.json: 91ae9d50ca94bb21f9027c0a0fde8602864b4035ad190046472874c240f88ed8
    experiments/h5_05_hybrid_experiment/layer_b/generator_inputs/scenarios.json: de38304803c39cb73a0e3d4a5bac10d8174b362851f0b90a3c8317655a3205ba
    experiments/h5_05_hybrid_experiment/layer_b/ground_truth.schema.json: 69ed5a1ce93f7ab8237149faf306b2d47f3e174e2fe0650bcf63c0c737527245
    experiments/h5_05_hybrid_experiment/layer_b/scenarios.schema.json: 960827549a92e53ffc58ad360440a307de147860a95a19d87b1f2c1aa5d4ceb0
    experiments/h5_05_hybrid_experiment/layer_b/target_app/tasks/fixtures/tasks.json: d0e1247af07bf2b61cfd157587e520aef44c9ad49fa526d97334ca2ed0df9369
    experiments/h5_05_hybrid_experiment/layer_b/target_app/tasks/fixtures/users.json: 7ab33235b998d72b04d436e5b13886fb99a04853b20543dca0bb6e2da8c884e8"""
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

def test_sc_tkp_002_patch_user_403(seeded_db, api_client):
    """SC-TKP-002 · PATCH /api/tasks/1/ · user (mehmet; fixture ilişkisi: sahip_olmayan) · beklenen 403
    
    Beklenen davranış: Sahibi olmayan kullanıcı başkasının görevini PATCH ile değiştiremez.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHORIZATION
    Endpoint: EP-TASK-DETAIL (task-detail), işlem: partial_update; yan etki kuralı: resource_unchanged
    """
    api_client.force_authenticate(user=User.objects.get(username='mehmet'))
    url = reverse('task-detail', kwargs={'pk': 1})
    assert url == '/api/tasks/1/', route_message('SC-TKP-002', '/api/tasks/1/', url)
    before = snapshot('tasks.Task', 1, ['title', 'notes', 'is_done'])
    response = api_client.patch(url, {'is_done': True}, format='json')
    assert response.status_code == 403, status_message('SC-TKP-002', 403, response, 'Sahibi olmayan kullanıcı başkasının görevini PATCH ile değiştiremez.')
    after = snapshot('tasks.Task', 1, ['title', 'notes', 'is_done'])
    assert after == before, side_effect_message('SC-TKP-002', 'resource_unchanged', before, after)

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

def test_sc_tkx_002_patch_user_403(seeded_db, api_client):
    """SC-TKX-002 · PATCH /api/legacy/tasks/1/ · user (mehmet; fixture ilişkisi: sahip_olmayan) · beklenen 403
    
    Beklenen davranış: Sahibi olmayan kullanıcı başkasının görevini PATCH ile değiştiremez.
    Referans: ground_truth.json (PROJECT_REQUIREMENT, verified); kategori: AUTHORIZATION
    Endpoint: EP-LEGACY-TASK-DETAIL (legacy-task-detail), işlem: partial_update; yan etki kuralı: resource_unchanged
    """
    api_client.force_authenticate(user=User.objects.get(username='mehmet'))
    url = reverse('legacy-task-detail', kwargs={'pk': 1})
    assert url == '/api/legacy/tasks/1/', route_message('SC-TKX-002', '/api/legacy/tasks/1/', url)
    before = snapshot('tasks.Task', 1, ['title', 'notes', 'is_done'])
    response = api_client.patch(url, {'is_done': True}, format='json')
    assert response.status_code == 403, status_message('SC-TKX-002', 403, response, 'Sahibi olmayan kullanıcı başkasının görevini PATCH ile değiştiremez.')
    after = snapshot('tasks.Task', 1, ['title', 'notes', 'is_done'])
    assert after == before, side_effect_message('SC-TKX-002', 'resource_unchanged', before, after)

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
