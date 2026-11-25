"""Hibrit nihai test — H5-05 / #43. Kaynak: hybrid<-rule_based:experiments/h3_04_rule_based_baseline/generated_tests/test_post_generated.py::test_sc_aut_001_post_anonymous_401. ELLE DÜZENLEMEYİN."""
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
