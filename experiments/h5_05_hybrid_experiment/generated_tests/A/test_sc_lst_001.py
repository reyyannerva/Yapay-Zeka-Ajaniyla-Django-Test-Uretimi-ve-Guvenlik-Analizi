"""Hibrit nihai test — H5-05 / #43. Kaynak: hybrid<-rule_based:experiments/h3_04_rule_based_baseline/generated_tests/test_get_generated.py::test_sc_lst_001_get_anonymous_200+llm:experiments/h3_05_llm_baseline/raw_responses/SC-LST-001.txt. ELLE DÜZENLEMEYİN."""
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


# --- LLM (H3-05) tamamlayıcı testi: ek doğrulama türü ---
def test_sc_lst_001__llm(seeded_db, api_client):
    url = reverse("article-list")
    response = api_client.get(url, format="json")
    assert response.status_code == 200
    for item in response.json():
        assert item.get("is_published") is True
