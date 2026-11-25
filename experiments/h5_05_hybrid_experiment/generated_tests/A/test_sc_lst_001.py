"""Hibrit nihai test — H5-05 / #43. Kaynak: hybrid<-rule_based:experiments/h3_04_rule_based_baseline/generated_tests/test_get_generated.py::test_sc_lst_001_get_anonymous_200. ELLE DÜZENLEMEYİN."""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


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
