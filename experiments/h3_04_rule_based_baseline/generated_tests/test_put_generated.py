"""PUT senaryoları için kural tabanlı üretilmiş Pytest testleri — H3-04 / Issue #30.

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

def test_sc_aut_002_put_anonymous_401(seeded_db, api_client):
    """SC-AUT-002 · PUT /api/articles/1/ · anonim · beklenen 401
    
    Beklenen davranış: Anonim kullanıcı güncelleme yapamaz.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHENTICATION
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: update; yan etki kuralı: resource_unchanged
    """
    url = reverse('article-detail', kwargs={'pk': 1})
    assert url == '/api/articles/1/', route_message('SC-AUT-002', '/api/articles/1/', url)
    before = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    response = api_client.put(url, {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 401, status_message('SC-AUT-002', 401, response, 'Anonim kullanıcı güncelleme yapamaz.')
    after = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    assert after == before, side_effect_message('SC-AUT-002', 'resource_unchanged', before, after)

def test_sc_auz_001_put_user_403(seeded_db, api_client):
    """SC-AUZ-001 · PUT /api/articles/1/ · user (carol; fixture ilişkisi: sahip_olmayan) · beklenen 403
    
    Beklenen davranış: Sahip olmayan kullanıcı başkasının kaydını güncelleyemez.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHORIZATION
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: update; yan etki kuralı: resource_unchanged
    """
    api_client.force_authenticate(user=User.objects.get(username='carol'))
    url = reverse('article-detail', kwargs={'pk': 1})
    assert url == '/api/articles/1/', route_message('SC-AUZ-001', '/api/articles/1/', url)
    before = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    response = api_client.put(url, {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 403, status_message('SC-AUZ-001', 403, response, 'Sahip olmayan kullanıcı başkasının kaydını güncelleyemez.')
    after = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    assert after == before, side_effect_message('SC-AUZ-001', 'resource_unchanged', before, after)

def test_sc_flw_001_put_user_403(seeded_db, api_client):
    """SC-FLW-001 · PUT /api/insecure/articles/1/ · user (carol; fixture ilişkisi: sahip_olmayan) · beklenen 403
    
    Beklenen davranış: Sahip olmayan kullanıcı başkasının kaydını güncelleyememeli (403).
    Referans: ground_truth.json (PROJECT_REQUIREMENT, verified); kategori: AUTHORIZATION
    Endpoint: EP-INSECURE-ARTICLE-DETAIL (insecure-article-detail), işlem: update; yan etki kuralı: resource_unchanged
    Bilinen güvenlik kusuru: Broken Object Level Authorization (BOLA/IDOR, OWASP API1:2023) — güvensiz uçta gözlenen 200 (status sapması).
    """
    api_client.force_authenticate(user=User.objects.get(username='carol'))
    url = reverse('insecure-article-detail', kwargs={'pk': 1})
    assert url == '/api/insecure/articles/1/', route_message('SC-FLW-001', '/api/insecure/articles/1/', url)
    before = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    response = api_client.put(url, {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 403, status_message('SC-FLW-001', 403, response, 'Sahip olmayan kullanıcı başkasının kaydını güncelleyememeli (403).')
    after = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    assert after == before, side_effect_message('SC-FLW-001', 'resource_unchanged', before, after)

def test_sc_inp_003_put_owner_400(seeded_db, api_client):
    """SC-INP-003 · PUT /api/articles/1/ · owner (alice; fixture ilişkisi: kaynak_sahibi) · beklenen 400
    
    Beklenen davranış: PUT'ta zorunlu 'title' eksik -> 400.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: INPUT_VALIDATION
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: update; yan etki kuralı: resource_unchanged
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-detail', kwargs={'pk': 1})
    assert url == '/api/articles/1/', route_message('SC-INP-003', '/api/articles/1/', url)
    before = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    response = api_client.put(url, {'body': 'x'}, format='json')
    assert response.status_code == 400, status_message('SC-INP-003', 400, response, "PUT'ta zorunlu 'title' eksik -> 400.")
    after = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    assert after == before, side_effect_message('SC-INP-003', 'resource_unchanged', before, after)

def test_sc_mna_002_put_owner_405(seeded_db, api_client):
    """SC-MNA-002 · PUT /api/articles/ · owner (alice; fixture ilişkisi: kimligi_dogrulanmis) · beklenen 405
    
    Beklenen davranış: Koleksiyon ucunda PUT desteklenmez -> 405.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-LIST (article-list), işlem: method_not_allowed; yan etki kuralı: count_unchanged
    Uyarı [OWNERSHIP_UNVERIFIABLE]: owner rolünün sahipliği fixture'dan doğrulanamadı; test kimliği doğrulanmış kullanıcı olarak üretildi
    Uyarı [METHOD_NOT_IN_OPERATIONS]: PUT bu endpoint'in işlemleri arasında yok; beklenen sonuç referanstan alınır
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-list')
    assert url == '/api/articles/', route_message('SC-MNA-002', '/api/articles/', url)
    before_count = model_count('catalog.Article')
    response = api_client.put(url, {'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 405, status_message('SC-MNA-002', 405, response, 'Koleksiyon ucunda PUT desteklenmez -> 405.')
    after_count = model_count('catalog.Article')
    assert after_count == before_count, side_effect_message('SC-MNA-002', 'count_unchanged', before_count, after_count)

def test_sc_nf_001_put_owner_404(seeded_db, api_client):
    """SC-NF-001 · PUT /api/articles/999/ · owner (alice; fixture ilişkisi: belirlenemez) · beklenen 404
    
    Beklenen davranış: Kimliği doğrulanmış kullanıcı mevcut olmayan kaydı güncelleyemez -> 404.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: update; yan etki kuralı: resource_still_absent
    Uyarı [OWNERSHIP_UNVERIFIABLE]: owner rolünün sahipliği fixture'dan doğrulanamadı; test kimliği doğrulanmış kullanıcı olarak üretildi
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-detail', kwargs={'pk': 999})
    assert url == '/api/articles/999/', route_message('SC-NF-001', '/api/articles/999/', url)
    response = api_client.put(url, {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 404, status_message('SC-NF-001', 404, response, 'Kimliği doğrulanmış kullanıcı mevcut olmayan kaydı güncelleyemez -> 404.')
    after = snapshot('catalog.Article', 999, ['title', 'body', 'is_published'])
    assert after is None, side_effect_message('SC-NF-001', 'resource_still_absent', None, after)

def test_sc_upd_001_put_owner_200(seeded_db, api_client):
    """SC-UPD-001 · PUT /api/articles/1/ · owner (alice; fixture ilişkisi: kaynak_sahibi) · beklenen 200
    
    Beklenen davranış: Sahip kendi kaydını tam günceller.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: update; yan etki kuralı: update_applied
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-detail', kwargs={'pk': 1})
    assert url == '/api/articles/1/', route_message('SC-UPD-001', '/api/articles/1/', url)
    before = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    response = api_client.put(url, {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 200, status_message('SC-UPD-001', 200, response, 'Sahip kendi kaydını tam günceller.')
    after = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    observed = {key: after[key] for key in ['body', 'title']} if after else None
    assert observed == {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, side_effect_message('SC-UPD-001', 'update_applied', {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, observed)

def test_sc_upd_002_put_admin_200(seeded_db, api_client):
    """SC-UPD-002 · PUT /api/articles/3/ · admin (admin; fixture ilişkisi: yonetici) · beklenen 200
    
    Beklenen davranış: Yönetici herhangi bir kaydı tam günceller.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: update; yan etki kuralı: update_applied
    """
    api_client.force_authenticate(user=User.objects.get(username='admin'))
    url = reverse('article-detail', kwargs={'pk': 3})
    assert url == '/api/articles/3/', route_message('SC-UPD-002', '/api/articles/3/', url)
    before = snapshot('catalog.Article', 3, ['title', 'body', 'is_published'])
    response = api_client.put(url, {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 200, status_message('SC-UPD-002', 200, response, 'Yönetici herhangi bir kaydı tam günceller.')
    after = snapshot('catalog.Article', 3, ['title', 'body', 'is_published'])
    observed = {key: after[key] for key in ['body', 'title']} if after else None
    assert observed == {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, side_effect_message('SC-UPD-002', 'update_applied', {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, observed)
