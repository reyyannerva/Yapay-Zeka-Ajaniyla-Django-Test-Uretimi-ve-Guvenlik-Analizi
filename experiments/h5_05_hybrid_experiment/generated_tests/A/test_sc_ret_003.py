"""Hibrit nihai test — H5-05 / #43. Kaynak: hybrid<-rule_based:experiments/h3_04_rule_based_baseline/generated_tests/test_get_generated.py::test_sc_ret_003_get_owner_200. ELLE DÜZENLEMEYİN."""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


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
