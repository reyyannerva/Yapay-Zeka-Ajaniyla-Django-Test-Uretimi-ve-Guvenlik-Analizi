"""DELETE senaryoları için kural tabanlı üretilmiş Pytest testleri — H3-04 / Issue #30.

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

def test_sc_aut_004_delete_anonymous_401(seeded_db, api_client):
    """SC-AUT-004 · DELETE /api/articles/1/ · anonim · beklenen 401
    
    Beklenen davranış: Anonim kullanıcı silme yapamaz.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHENTICATION
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: destroy; yan etki kuralı: resource_unchanged
    """
    url = reverse('article-detail', kwargs={'pk': 1})
    assert url == '/api/articles/1/', route_message('SC-AUT-004', '/api/articles/1/', url)
    before = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    response = api_client.delete(url)
    assert response.status_code == 401, status_message('SC-AUT-004', 401, response, 'Anonim kullanıcı silme yapamaz.')
    after = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    assert after == before, side_effect_message('SC-AUT-004', 'resource_unchanged', before, after)

def test_sc_auz_003_delete_user_403(seeded_db, api_client):
    """SC-AUZ-003 · DELETE /api/articles/1/ · user (carol; fixture ilişkisi: sahip_olmayan) · beklenen 403
    
    Beklenen davranış: Sahip olmayan kullanıcı başkasının kaydını silemez.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHORIZATION
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: destroy; yan etki kuralı: resource_unchanged
    """
    api_client.force_authenticate(user=User.objects.get(username='carol'))
    url = reverse('article-detail', kwargs={'pk': 1})
    assert url == '/api/articles/1/', route_message('SC-AUZ-003', '/api/articles/1/', url)
    before = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    response = api_client.delete(url)
    assert response.status_code == 403, status_message('SC-AUZ-003', 403, response, 'Sahip olmayan kullanıcı başkasının kaydını silemez.')
    after = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    assert after == before, side_effect_message('SC-AUZ-003', 'resource_unchanged', before, after)

def test_sc_del_001_delete_owner_204(seeded_db, api_client):
    """SC-DEL-001 · DELETE /api/articles/1/ · owner (alice; fixture ilişkisi: kaynak_sahibi) · beklenen 204
    
    Beklenen davranış: Sahip kendi kaydını siler (204).
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: destroy; yan etki kuralı: resource_deleted
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-detail', kwargs={'pk': 1})
    assert url == '/api/articles/1/', route_message('SC-DEL-001', '/api/articles/1/', url)
    before = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    response = api_client.delete(url)
    assert response.status_code == 204, status_message('SC-DEL-001', 204, response, 'Sahip kendi kaydını siler (204).')
    after = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    assert after is None, side_effect_message('SC-DEL-001', 'resource_deleted', None, after)

def test_sc_del_002_delete_admin_204(seeded_db, api_client):
    """SC-DEL-002 · DELETE /api/articles/3/ · admin (admin; fixture ilişkisi: yonetici) · beklenen 204
    
    Beklenen davranış: Yönetici herhangi bir kaydı siler (204).
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: destroy; yan etki kuralı: resource_deleted
    """
    api_client.force_authenticate(user=User.objects.get(username='admin'))
    url = reverse('article-detail', kwargs={'pk': 3})
    assert url == '/api/articles/3/', route_message('SC-DEL-002', '/api/articles/3/', url)
    before = snapshot('catalog.Article', 3, ['title', 'body', 'is_published'])
    response = api_client.delete(url)
    assert response.status_code == 204, status_message('SC-DEL-002', 204, response, 'Yönetici herhangi bir kaydı siler (204).')
    after = snapshot('catalog.Article', 3, ['title', 'body', 'is_published'])
    assert after is None, side_effect_message('SC-DEL-002', 'resource_deleted', None, after)

def test_sc_flw_002_delete_user_403(seeded_db, api_client):
    """SC-FLW-002 · DELETE /api/insecure/articles/3/ · user (carol; fixture ilişkisi: sahip_olmayan) · beklenen 403
    
    Beklenen davranış: Sahip olmayan kullanıcı başkasının kaydını silememeli (403).
    Referans: ground_truth.json (PROJECT_REQUIREMENT, verified); kategori: AUTHORIZATION
    Endpoint: EP-INSECURE-ARTICLE-DETAIL (insecure-article-detail), işlem: destroy; yan etki kuralı: resource_unchanged
    Bilinen güvenlik kusuru: Broken Object Level Authorization (BOLA/IDOR, OWASP API1:2023) — güvensiz uçta gözlenen 204 (status sapması).
    """
    api_client.force_authenticate(user=User.objects.get(username='carol'))
    url = reverse('insecure-article-detail', kwargs={'pk': 3})
    assert url == '/api/insecure/articles/3/', route_message('SC-FLW-002', '/api/insecure/articles/3/', url)
    before = snapshot('catalog.Article', 3, ['title', 'body', 'is_published'])
    response = api_client.delete(url)
    assert response.status_code == 403, status_message('SC-FLW-002', 403, response, 'Sahip olmayan kullanıcı başkasının kaydını silememeli (403).')
    after = snapshot('catalog.Article', 3, ['title', 'body', 'is_published'])
    assert after == before, side_effect_message('SC-FLW-002', 'resource_unchanged', before, after)

def test_sc_mna_001_delete_owner_405(seeded_db, api_client):
    """SC-MNA-001 · DELETE /api/articles/ · owner (alice; fixture ilişkisi: kimligi_dogrulanmis) · beklenen 405
    
    Beklenen davranış: Koleksiyon ucunda DELETE desteklenmez -> 405.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-LIST (article-list), işlem: method_not_allowed; yan etki kuralı: count_unchanged
    Uyarı [OWNERSHIP_UNVERIFIABLE]: owner rolünün sahipliği fixture'dan doğrulanamadı; test kimliği doğrulanmış kullanıcı olarak üretildi
    Uyarı [METHOD_NOT_IN_OPERATIONS]: DELETE bu endpoint'in işlemleri arasında yok; beklenen sonuç referanstan alınır
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-list')
    assert url == '/api/articles/', route_message('SC-MNA-001', '/api/articles/', url)
    before_count = model_count('catalog.Article')
    response = api_client.delete(url)
    assert response.status_code == 405, status_message('SC-MNA-001', 405, response, 'Koleksiyon ucunda DELETE desteklenmez -> 405.')
    after_count = model_count('catalog.Article')
    assert after_count == before_count, side_effect_message('SC-MNA-001', 'count_unchanged', before_count, after_count)

def test_sc_nf_002_delete_owner_404(seeded_db, api_client):
    """SC-NF-002 · DELETE /api/articles/999/ · owner (alice; fixture ilişkisi: belirlenemez) · beklenen 404
    
    Beklenen davranış: Kimliği doğrulanmış kullanıcı mevcut olmayan kaydı silemez -> 404.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: destroy; yan etki kuralı: resource_still_absent
    Uyarı [OWNERSHIP_UNVERIFIABLE]: owner rolünün sahipliği fixture'dan doğrulanamadı; test kimliği doğrulanmış kullanıcı olarak üretildi
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-detail', kwargs={'pk': 999})
    assert url == '/api/articles/999/', route_message('SC-NF-002', '/api/articles/999/', url)
    response = api_client.delete(url)
    assert response.status_code == 404, status_message('SC-NF-002', 404, response, 'Kimliği doğrulanmış kullanıcı mevcut olmayan kaydı silemez -> 404.')
    after = snapshot('catalog.Article', 999, ['title', 'body', 'is_published'])
    assert after is None, side_effect_message('SC-NF-002', 'resource_still_absent', None, after)
