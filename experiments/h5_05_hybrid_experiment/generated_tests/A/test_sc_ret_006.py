"""Hibrit nihai test — H5-05 / #43. Kaynak: hybrid<-rule_based:experiments/h3_04_rule_based_baseline/generated_tests/test_get_generated.py::test_sc_ret_006_get_anonymous_404. ELLE DÜZENLEMEYİN."""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


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
