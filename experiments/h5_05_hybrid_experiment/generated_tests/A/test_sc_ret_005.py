"""Hibrit nihai test — H5-05 / #43. Kaynak: hybrid<-rule_based:experiments/h3_04_rule_based_baseline/generated_tests/test_get_generated.py::test_sc_ret_005_get_user_404. ELLE DÜZENLEMEYİN."""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


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
