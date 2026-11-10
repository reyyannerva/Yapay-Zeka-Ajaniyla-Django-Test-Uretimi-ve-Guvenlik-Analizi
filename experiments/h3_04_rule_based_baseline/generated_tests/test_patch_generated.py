"""PATCH senaryoları için kural tabanlı üretilmiş Pytest testleri — H3-04 / Issue #30.

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

def test_sc_aut_003_patch_anonymous_401(seeded_db, api_client):
    """SC-AUT-003 · PATCH /api/articles/1/ · anonim · beklenen 401
    
    Beklenen davranış: Anonim kullanıcı kısmi güncelleme yapamaz.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHENTICATION
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: partial_update; yan etki kuralı: resource_unchanged
    """
    url = reverse('article-detail', kwargs={'pk': 1})
    assert url == '/api/articles/1/', route_message('SC-AUT-003', '/api/articles/1/', url)
    before = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    response = api_client.patch(url, {'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 401, status_message('SC-AUT-003', 401, response, 'Anonim kullanıcı kısmi güncelleme yapamaz.')
    after = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    assert after == before, side_effect_message('SC-AUT-003', 'resource_unchanged', before, after)

def test_sc_auz_002_patch_user_403(seeded_db, api_client):
    """SC-AUZ-002 · PATCH /api/articles/1/ · user (carol; fixture ilişkisi: sahip_olmayan) · beklenen 403
    
    Beklenen davranış: Sahip olmayan kullanıcı başkasının kaydını kısmen güncelleyemez.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: AUTHORIZATION
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: partial_update; yan etki kuralı: resource_unchanged
    """
    api_client.force_authenticate(user=User.objects.get(username='carol'))
    url = reverse('article-detail', kwargs={'pk': 1})
    assert url == '/api/articles/1/', route_message('SC-AUZ-002', '/api/articles/1/', url)
    before = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    response = api_client.patch(url, {'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 403, status_message('SC-AUZ-002', 403, response, 'Sahip olmayan kullanıcı başkasının kaydını kısmen güncelleyemez.')
    after = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    assert after == before, side_effect_message('SC-AUZ-002', 'resource_unchanged', before, after)

def test_sc_upd_003_patch_owner_200(seeded_db, api_client):
    """SC-UPD-003 · PATCH /api/articles/1/ · owner (alice; fixture ilişkisi: kaynak_sahibi) · beklenen 200
    
    Beklenen davranış: Sahip kendi kaydını kısmen günceller.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: partial_update; yan etki kuralı: partial_update_applied
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-detail', kwargs={'pk': 1})
    assert url == '/api/articles/1/', route_message('SC-UPD-003', '/api/articles/1/', url)
    before = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    response = api_client.patch(url, {'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 200, status_message('SC-UPD-003', 200, response, 'Sahip kendi kaydını kısmen günceller.')
    after = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    expected_after = {**before, **{'title': 'Örnek Başlık'}}
    assert after == expected_after, side_effect_message('SC-UPD-003', 'partial_update_applied', expected_after, after)

def test_sc_upd_004_patch_admin_200(seeded_db, api_client):
    """SC-UPD-004 · PATCH /api/articles/3/ · admin (admin; fixture ilişkisi: yonetici) · beklenen 200
    
    Beklenen davranış: Yönetici herhangi bir kaydı kısmen günceller.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: partial_update; yan etki kuralı: partial_update_applied
    """
    api_client.force_authenticate(user=User.objects.get(username='admin'))
    url = reverse('article-detail', kwargs={'pk': 3})
    assert url == '/api/articles/3/', route_message('SC-UPD-004', '/api/articles/3/', url)
    before = snapshot('catalog.Article', 3, ['title', 'body', 'is_published'])
    response = api_client.patch(url, {'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 200, status_message('SC-UPD-004', 200, response, 'Yönetici herhangi bir kaydı kısmen günceller.')
    after = snapshot('catalog.Article', 3, ['title', 'body', 'is_published'])
    expected_after = {**before, **{'title': 'Örnek Başlık'}}
    assert after == expected_after, side_effect_message('SC-UPD-004', 'partial_update_applied', expected_after, after)
