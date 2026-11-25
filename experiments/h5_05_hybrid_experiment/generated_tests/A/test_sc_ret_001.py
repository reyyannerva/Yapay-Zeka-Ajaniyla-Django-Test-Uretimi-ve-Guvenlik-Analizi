"""Hibrit nihai test — H5-05 / #43. Kaynak: hybrid<-rule_based:experiments/h3_04_rule_based_baseline/generated_tests/test_get_generated.py::test_sc_ret_001_get_anonymous_200. ELLE DÜZENLEMEYİN."""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


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
