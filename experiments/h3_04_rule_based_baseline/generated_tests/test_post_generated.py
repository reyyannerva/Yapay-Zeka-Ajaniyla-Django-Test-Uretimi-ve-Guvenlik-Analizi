"""POST senaryoları için kural tabanlı üretilmiş Pytest testleri — H3-04 / Issue #30.

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

def test_sc_aut_001_post_anonymous_401(seeded_db, api_client):
    """SC-AUT-001 · POST /api/articles/ · anonim · beklenen 401
    
    Beklenen davranış: Anonim kullanıcı kayıt oluşturamaz (kimlik doğrulama gerekli).
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHENTICATION
    Endpoint: EP-ARTICLE-LIST (article-list), işlem: create; yan etki kuralı: count_unchanged
    """
    url = reverse('article-list')
    assert url == '/api/articles/', route_message('SC-AUT-001', '/api/articles/', url)
    before_count = model_count('catalog.Article')
    response = api_client.post(url, {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 401, status_message('SC-AUT-001', 401, response, 'Anonim kullanıcı kayıt oluşturamaz (kimlik doğrulama gerekli).')
    after_count = model_count('catalog.Article')
    assert after_count == before_count, side_effect_message('SC-AUT-001', 'count_unchanged', before_count, after_count)

def test_sc_aut_005_post_anonymous_401(seeded_db, api_client):
    """SC-AUT-005 · POST /api/articles/2/publish/ · anonim · beklenen 401
    
    Beklenen davranış: Anonim kullanıcı yayınlama yapamaz.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHENTICATION
    Endpoint: EP-ARTICLE-PUBLISH (article-publish), işlem: custom_action; yan etki kuralı: none
    """
    url = reverse('article-publish', kwargs={'pk': 2})
    assert url == '/api/articles/2/publish/', route_message('SC-AUT-005', '/api/articles/2/publish/', url)
    response = api_client.post(url, format='json')
    assert response.status_code == 401, status_message('SC-AUT-005', 401, response, 'Anonim kullanıcı yayınlama yapamaz.')

def test_sc_auz_004_post_user_403(seeded_db, api_client):
    """SC-AUZ-004 · POST /api/articles/2/publish/ · user (carol; fixture ilişkisi: sahip_olmayan) · beklenen 403
    
    Beklenen davranış: Sahip olmayan kullanıcı başkasının kaydını yayınlayamaz.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHORIZATION
    Endpoint: EP-ARTICLE-PUBLISH (article-publish), işlem: custom_action; yan etki kuralı: none
    """
    api_client.force_authenticate(user=User.objects.get(username='carol'))
    url = reverse('article-publish', kwargs={'pk': 2})
    assert url == '/api/articles/2/publish/', route_message('SC-AUZ-004', '/api/articles/2/publish/', url)
    response = api_client.post(url, format='json')
    assert response.status_code == 403, status_message('SC-AUZ-004', 403, response, 'Sahip olmayan kullanıcı başkasının kaydını yayınlayamaz.')

def test_sc_crt_001_post_user_201(seeded_db, api_client):
    """SC-CRT-001 · POST /api/articles/ · user (carol; fixture ilişkisi: kimligi_dogrulanmis) · beklenen 201
    
    Beklenen davranış: Kimliği doğrulanmış kullanıcı geçerli girdiyle kayıt oluşturur; owner isteği yapan olur.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-LIST (article-list), işlem: create; yan etki kuralı: count_plus_one
    """
    api_client.force_authenticate(user=User.objects.get(username='carol'))
    url = reverse('article-list')
    assert url == '/api/articles/', route_message('SC-CRT-001', '/api/articles/', url)
    before_count = model_count('catalog.Article')
    response = api_client.post(url, {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 201, status_message('SC-CRT-001', 201, response, 'Kimliği doğrulanmış kullanıcı geçerli girdiyle kayıt oluşturur; owner isteği yapan olur.')
    after_count = model_count('catalog.Article')
    assert after_count == before_count + 1, side_effect_message('SC-CRT-001', 'count_plus_one', before_count + 1, after_count)

def test_sc_crt_002_post_owner_201(seeded_db, api_client):
    """SC-CRT-002 · POST /api/articles/ · owner (alice; fixture ilişkisi: kimligi_dogrulanmis) · beklenen 201
    
    Beklenen davranış: Kullanıcı kendi adına kayıt oluşturur.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-LIST (article-list), işlem: create; yan etki kuralı: count_plus_one
    Uyarı [OWNERSHIP_UNVERIFIABLE]: owner rolünün sahipliği fixture'dan doğrulanamadı; test kimliği doğrulanmış kullanıcı olarak üretildi
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-list')
    assert url == '/api/articles/', route_message('SC-CRT-002', '/api/articles/', url)
    before_count = model_count('catalog.Article')
    response = api_client.post(url, {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 201, status_message('SC-CRT-002', 201, response, 'Kullanıcı kendi adına kayıt oluşturur.')
    after_count = model_count('catalog.Article')
    assert after_count == before_count + 1, side_effect_message('SC-CRT-002', 'count_plus_one', before_count + 1, after_count)

def test_sc_inp_001_post_user_400(seeded_db, api_client):
    """SC-INP-001 · POST /api/articles/ · user (carol; fixture ilişkisi: kimligi_dogrulanmis) · beklenen 400
    
    Beklenen davranış: Zorunlu 'title' alanı eksik -> 400.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: INPUT_VALIDATION
    Endpoint: EP-ARTICLE-LIST (article-list), işlem: create; yan etki kuralı: count_unchanged
    """
    api_client.force_authenticate(user=User.objects.get(username='carol'))
    url = reverse('article-list')
    assert url == '/api/articles/', route_message('SC-INP-001', '/api/articles/', url)
    before_count = model_count('catalog.Article')
    response = api_client.post(url, {'body': 'x'}, format='json')
    assert response.status_code == 400, status_message('SC-INP-001', 400, response, "Zorunlu 'title' alanı eksik -> 400.")
    after_count = model_count('catalog.Article')
    assert after_count == before_count, side_effect_message('SC-INP-001', 'count_unchanged', before_count, after_count)

def test_sc_inp_002_post_user_400(seeded_db, api_client):
    """SC-INP-002 · POST /api/articles/ · user (carol; fixture ilişkisi: kimligi_dogrulanmis) · beklenen 400
    
    Beklenen davranış: Yalnızca boşluktan oluşan başlık -> 400.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: INPUT_VALIDATION
    Endpoint: EP-ARTICLE-LIST (article-list), işlem: create; yan etki kuralı: count_unchanged
    """
    api_client.force_authenticate(user=User.objects.get(username='carol'))
    url = reverse('article-list')
    assert url == '/api/articles/', route_message('SC-INP-002', '/api/articles/', url)
    before_count = model_count('catalog.Article')
    response = api_client.post(url, {'body': 'x', 'title': '   '}, format='json')
    assert response.status_code == 400, status_message('SC-INP-002', 400, response, 'Yalnızca boşluktan oluşan başlık -> 400.')
    after_count = model_count('catalog.Article')
    assert after_count == before_count, side_effect_message('SC-INP-002', 'count_unchanged', before_count, after_count)

def test_sc_inp_004_post_user_400(seeded_db, api_client):
    """SC-INP-004 · POST /api/articles/ · user (carol; fixture ilişkisi: kimligi_dogrulanmis) · beklenen 400
    
    Beklenen davranış: Başlık max_length=200 sınırını aşıyor (201 karakter) -> 400.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: INPUT_VALIDATION
    Endpoint: EP-ARTICLE-LIST (article-list), işlem: create; yan etki kuralı: count_unchanged
    """
    api_client.force_authenticate(user=User.objects.get(username='carol'))
    url = reverse('article-list')
    assert url == '/api/articles/', route_message('SC-INP-004', '/api/articles/', url)
    before_count = model_count('catalog.Article')
    response = api_client.post(url, {'body': 'x', 'title': 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'}, format='json')
    assert response.status_code == 400, status_message('SC-INP-004', 400, response, 'Başlık max_length=200 sınırını aşıyor (201 karakter) -> 400.')
    after_count = model_count('catalog.Article')
    assert after_count == before_count, side_effect_message('SC-INP-004', 'count_unchanged', before_count, after_count)

def test_sc_pub_001_post_owner_200(seeded_db, api_client):
    """SC-PUB-001 · POST /api/articles/2/publish/ · owner (alice; fixture ilişkisi: kaynak_sahibi) · beklenen 200
    
    Beklenen davranış: Sahip kendi taslağını yayınlar (is_published=true).
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHORIZATION
    Endpoint: EP-ARTICLE-PUBLISH (article-publish), işlem: custom_action; yan etki kuralı: none
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-publish', kwargs={'pk': 2})
    assert url == '/api/articles/2/publish/', route_message('SC-PUB-001', '/api/articles/2/publish/', url)
    response = api_client.post(url, format='json')
    assert response.status_code == 200, status_message('SC-PUB-001', 200, response, 'Sahip kendi taslağını yayınlar (is_published=true).')
