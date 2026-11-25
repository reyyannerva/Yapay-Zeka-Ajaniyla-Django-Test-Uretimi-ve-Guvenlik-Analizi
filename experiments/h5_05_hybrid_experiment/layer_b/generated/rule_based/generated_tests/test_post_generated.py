"""POST senaryoları için kural tabanlı üretilmiş Pytest testleri — H3-04 / Issue #30.

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

def test_sc_tkc_002_post_user_400(seeded_db, api_client):
    """SC-TKC-002 · POST /api/tasks/ · user (mehmet; fixture ilişkisi: kimligi_dogrulanmis) · beklenen 400
    
    Beklenen davranış: Zorunlu title alanı eksik görev oluşturulamaz.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: INPUT_VALIDATION
    Endpoint: EP-TASK-LIST (task-list), işlem: create; yan etki kuralı: count_unchanged
    """
    api_client.force_authenticate(user=User.objects.get(username='mehmet'))
    url = reverse('task-list')
    assert url == '/api/tasks/', route_message('SC-TKC-002', '/api/tasks/', url)
    before_count = model_count('tasks.Task')
    response = api_client.post(url, {'notes': 'başlık yok'}, format='json')
    assert response.status_code == 400, status_message('SC-TKC-002', 400, response, 'Zorunlu title alanı eksik görev oluşturulamaz.')
    after_count = model_count('tasks.Task')
    assert after_count == before_count, side_effect_message('SC-TKC-002', 'count_unchanged', before_count, after_count)
