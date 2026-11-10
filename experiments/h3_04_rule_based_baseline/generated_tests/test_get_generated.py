"""GET senaryoları için kural tabanlı üretilmiş Pytest testleri — H3-04 / Issue #30.

BU DOSYA OTOMATİK ÜRETİLMİŞTİR; ELLE DÜZENLEMEYİN. Yeniden üretmek için:
    python -m agent.test_generation.rule_based generate

Üretici: agent.test_generation.rule_based v1.0.0 (LLM kullanılmaz).
Beklenen durum kodları bağımsız referanstan (ground_truth.json → secure_status) alınmıştır.
Girdi özetleri (SHA-256):
    benchmarks/drf_fixtures/sample_app/catalog/fixtures/articles.json: 7d3017e8c4324818b615bc076ab0bd76400f0c3b1472ec95a4fc7d674915989d
    benchmarks/drf_fixtures/sample_app/catalog/fixtures/users.json: 4a976c917b4e5d7ad511bc93a239b6ea6dc0bc4122d58b603bed5ab67a1e4e62
    benchmarks/drf_fixtures/scenarios/scenarios.json: 6970d02ed14f5c66268b367a5cae2d02e753f60de5b8044b98ab53519237158e
    benchmarks/drf_fixtures/scenarios/scenarios.schema.json: 8ddca198ee2356648f6859111e87e1d73353188248a8c2122af47540b0f247a1
    benchmarks/reference_cases/ground_truth.json: b5114e74c63d9a60f335bd4984d9896da98d423c41ea87d618f2cca268fd737c
    benchmarks/reference_cases/ground_truth.schema.json: 3642e429bfbee234d7a43caf27f1a8a0d9afb623dc5dd02fad1232a0e4e997ef
    experiments/h3_04_rule_based_baseline/endpoint_summary.json: 47fa2ed25bd95a89fe93a72f3705c74c05780c2e614c50b7bf380b77d8c4344f"""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db

def test_sc_flw_003_get_anonymous_200(seeded_db, api_client):
    """SC-FLW-003 · GET /api/insecure/articles/ · anonim · beklenen 200
    
    Beklenen davranış: Liste 200 döner ancak yalnızca yayınlananları; taslaklar gizlenmeli.
    Referans: ground_truth.json (PROJECT_REQUIREMENT, verified); kategori: SECURITY_CONFIGURATION
    Endpoint: EP-INSECURE-ARTICLE-LIST (insecure-article-list), işlem: list; yan etki kuralı: none
    Bilinen güvenlik kusuru: Hassas veri ifşası / bozuk fonksiyon düzeyi yetkilendirme — güvensiz uçta gözlenen 200 (content sapması).
    Uyarı [CONTENT_ASSERTION_UNSUPPORTED]: Referanstaki güvenlik beklentisi içerik düzeyinde ve makine-okunur değil; yalnızca durum kodu doğrulanır, bilinen kusur bu testle tespit EDİLEMEZ
    """
    url = reverse('insecure-article-list')
    assert url == '/api/insecure/articles/', route_message('SC-FLW-003', '/api/insecure/articles/', url)
    response = api_client.get(url)
    assert response.status_code == 200, status_message('SC-FLW-003', 200, response, 'Liste 200 döner ancak yalnızca yayınlananları; taslaklar gizlenmeli.')

def test_sc_lst_001_get_anonymous_200(seeded_db, api_client):
    """SC-LST-001 · GET /api/articles/ · anonim · beklenen 200
    
    Beklenen davranış: Anonim kullanıcı listeyi görür; yalnızca yayınlanan kayıtlar döner.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-LIST (article-list), işlem: list; yan etki kuralı: none
    """
    url = reverse('article-list')
    assert url == '/api/articles/', route_message('SC-LST-001', '/api/articles/', url)
    response = api_client.get(url)
    assert response.status_code == 200, status_message('SC-LST-001', 200, response, 'Anonim kullanıcı listeyi görür; yalnızca yayınlanan kayıtlar döner.')

def test_sc_lst_002_get_user_200(seeded_db, api_client):
    """SC-LST-002 · GET /api/articles/ · user (carol; fixture ilişkisi: kimligi_dogrulanmis) · beklenen 200
    
    Beklenen davranış: Kimliği doğrulanmış kullanıcı listeyi görür (yayınlananlar + kendi kayıtları).
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-LIST (article-list), işlem: list; yan etki kuralı: none
    """
    api_client.force_authenticate(user=User.objects.get(username='carol'))
    url = reverse('article-list')
    assert url == '/api/articles/', route_message('SC-LST-002', '/api/articles/', url)
    response = api_client.get(url)
    assert response.status_code == 200, status_message('SC-LST-002', 200, response, 'Kimliği doğrulanmış kullanıcı listeyi görür (yayınlananlar + kendi kayıtları).')

def test_sc_lst_003_get_admin_200(seeded_db, api_client):
    """SC-LST-003 · GET /api/articles/ · admin (admin; fixture ilişkisi: yonetici) · beklenen 200
    
    Beklenen davranış: Yönetici tüm kayıtları listeler.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-LIST (article-list), işlem: list; yan etki kuralı: none
    """
    api_client.force_authenticate(user=User.objects.get(username='admin'))
    url = reverse('article-list')
    assert url == '/api/articles/', route_message('SC-LST-003', '/api/articles/', url)
    response = api_client.get(url)
    assert response.status_code == 200, status_message('SC-LST-003', 200, response, 'Yönetici tüm kayıtları listeler.')

def test_sc_ret_001_get_anonymous_200(seeded_db, api_client):
    """SC-RET-001 · GET /api/articles/1/ · anonim · beklenen 200
    
    Beklenen davranış: Yayınlanmış kayıt anonim kullanıcıya görünür.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: retrieve; yan etki kuralı: none
    """
    url = reverse('article-detail', kwargs={'pk': 1})
    assert url == '/api/articles/1/', route_message('SC-RET-001', '/api/articles/1/', url)
    response = api_client.get(url)
    assert response.status_code == 200, status_message('SC-RET-001', 200, response, 'Yayınlanmış kayıt anonim kullanıcıya görünür.')

def test_sc_ret_002_get_anonymous_404(seeded_db, api_client):
    """SC-RET-002 · GET /api/articles/2/ · anonim · beklenen 404
    
    Beklenen davranış: Taslak kayıt anonim kullanıcıya görünmez (queryset dışı -> 404).
    Referans: ground_truth.json (FIXTURE_DESIGN, verified); kategori: AUTHORIZATION
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: retrieve; yan etki kuralı: none
    """
    url = reverse('article-detail', kwargs={'pk': 2})
    assert url == '/api/articles/2/', route_message('SC-RET-002', '/api/articles/2/', url)
    response = api_client.get(url)
    assert response.status_code == 404, status_message('SC-RET-002', 404, response, 'Taslak kayıt anonim kullanıcıya görünmez (queryset dışı -> 404).')

def test_sc_ret_003_get_owner_200(seeded_db, api_client):
    """SC-RET-003 · GET /api/articles/2/ · owner (alice; fixture ilişkisi: kaynak_sahibi) · beklenen 200
    
    Beklenen davranış: Sahip kendi taslağını görüntüleyebilir.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: retrieve; yan etki kuralı: none
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-detail', kwargs={'pk': 2})
    assert url == '/api/articles/2/', route_message('SC-RET-003', '/api/articles/2/', url)
    response = api_client.get(url)
    assert response.status_code == 200, status_message('SC-RET-003', 200, response, 'Sahip kendi taslağını görüntüleyebilir.')

def test_sc_ret_004_get_admin_200(seeded_db, api_client):
    """SC-RET-004 · GET /api/articles/2/ · admin (admin; fixture ilişkisi: yonetici) · beklenen 200
    
    Beklenen davranış: Yönetici herhangi bir taslağı görüntüleyebilir.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: retrieve; yan etki kuralı: none
    """
    api_client.force_authenticate(user=User.objects.get(username='admin'))
    url = reverse('article-detail', kwargs={'pk': 2})
    assert url == '/api/articles/2/', route_message('SC-RET-004', '/api/articles/2/', url)
    response = api_client.get(url)
    assert response.status_code == 200, status_message('SC-RET-004', 200, response, 'Yönetici herhangi bir taslağı görüntüleyebilir.')

def test_sc_ret_005_get_user_404(seeded_db, api_client):
    """SC-RET-005 · GET /api/articles/2/ · user (carol; fixture ilişkisi: sahip_olmayan) · beklenen 404
    
    Beklenen davranış: Başkasının taslağı kullanıcıya görünmez (queryset dışı -> 404).
    Referans: ground_truth.json (FIXTURE_DESIGN, verified); kategori: AUTHORIZATION
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: retrieve; yan etki kuralı: none
    """
    api_client.force_authenticate(user=User.objects.get(username='carol'))
    url = reverse('article-detail', kwargs={'pk': 2})
    assert url == '/api/articles/2/', route_message('SC-RET-005', '/api/articles/2/', url)
    response = api_client.get(url)
    assert response.status_code == 404, status_message('SC-RET-005', 404, response, 'Başkasının taslağı kullanıcıya görünmez (queryset dışı -> 404).')

def test_sc_ret_006_get_anonymous_404(seeded_db, api_client):
    """SC-RET-006 · GET /api/articles/999/ · anonim · beklenen 404
    
    Beklenen davranış: Mevcut olmayan kaynak 404 döner.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: retrieve; yan etki kuralı: none
    """
    url = reverse('article-detail', kwargs={'pk': 999})
    assert url == '/api/articles/999/', route_message('SC-RET-006', '/api/articles/999/', url)
    response = api_client.get(url)
    assert response.status_code == 404, status_message('SC-RET-006', 404, response, 'Mevcut olmayan kaynak 404 döner.')
