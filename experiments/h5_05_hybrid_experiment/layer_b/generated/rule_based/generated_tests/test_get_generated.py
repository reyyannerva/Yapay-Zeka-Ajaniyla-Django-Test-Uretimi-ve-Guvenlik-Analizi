"""GET senaryoları için kural tabanlı üretilmiş Pytest testleri — H3-04 / Issue #30.

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

def test_sc_tkl_001_get_user_200(seeded_db, api_client):
    """SC-TKL-001 · GET /api/tasks/ · user (mehmet; fixture ilişkisi: kimligi_dogrulanmis) · beklenen 200
    
    Beklenen davranış: Kimliği doğrulanmış kullanıcı görev listesini görür.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-TASK-LIST (task-list), işlem: list; yan etki kuralı: none
    """
    api_client.force_authenticate(user=User.objects.get(username='mehmet'))
    url = reverse('task-list')
    assert url == '/api/tasks/', route_message('SC-TKL-001', '/api/tasks/', url)
    response = api_client.get(url)
    assert response.status_code == 200, status_message('SC-TKL-001', 200, response, 'Kimliği doğrulanmış kullanıcı görev listesini görür.')

def test_sc_tkl_002_get_anonymous_401(seeded_db, api_client):
    """SC-TKL-002 · GET /api/tasks/ · anonim · beklenen 401
    
    Beklenen davranış: Anonim kullanıcı görev listesine erişemez (kimlik doğrulama gerekli).
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHENTICATION
    Endpoint: EP-TASK-LIST (task-list), işlem: list; yan etki kuralı: none
    """
    url = reverse('task-list')
    assert url == '/api/tasks/', route_message('SC-TKL-002', '/api/tasks/', url)
    response = api_client.get(url)
    assert response.status_code == 401, status_message('SC-TKL-002', 401, response, 'Anonim kullanıcı görev listesine erişemez (kimlik doğrulama gerekli).')

def test_sc_tkx_005_get_owner_200(seeded_db, api_client):
    """SC-TKX-005 · GET /api/legacy/tasks/1/ · owner (ayse; fixture ilişkisi: kaynak_sahibi) · beklenen 200
    
    Beklenen davranış: Sahip kendi görevini görüntüler.
    Referans: ground_truth.json (PROJECT_REQUIREMENT, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-LEGACY-TASK-DETAIL (legacy-task-detail), işlem: retrieve; yan etki kuralı: none
    """
    api_client.force_authenticate(user=User.objects.get(username='ayse'))
    url = reverse('legacy-task-detail', kwargs={'pk': 1})
    assert url == '/api/legacy/tasks/1/', route_message('SC-TKX-005', '/api/legacy/tasks/1/', url)
    response = api_client.get(url)
    assert response.status_code == 200, status_message('SC-TKX-005', 200, response, 'Sahip kendi görevini görüntüler.')
