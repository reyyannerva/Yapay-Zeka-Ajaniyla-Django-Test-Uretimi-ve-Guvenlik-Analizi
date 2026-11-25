"""Hibrit nihai test — H5-05 / #43. Kaynak: hybrid<-rule_based:experiments/h3_04_rule_based_baseline/generated_tests/test_delete_generated.py::test_sc_mna_001_delete_owner_405. ELLE DÜZENLEMEYİN."""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_mna_001_delete_owner_405(seeded_db, api_client):
    """SC-MNA-001 · DELETE /api/articles/ · owner (alice; fixture ilişkisi: kimligi_dogrulanmis) · beklenen 405
    
    Beklenen davranış: Koleksiyon ucunda DELETE desteklenmez -> 405.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-LIST (article-list), işlem: method_not_allowed; yan etki kuralı: count_unchanged
    Uyarı [OWNERSHIP_UNVERIFIABLE]: owner rolünün sahipliği fixture'dan doğrulanamadı; test kimliği doğrulanmış kullanıcı olarak üretildi
    Uyarı [METHOD_NOT_IN_OPERATIONS]: DELETE bu endpoint'in işlemleri arasında yok; beklenen sonuç referanstan alınır
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-list')
    assert url == '/api/articles/', route_message('SC-MNA-001', '/api/articles/', url)
    before_count = model_count('catalog.Article')
    response = api_client.delete(url)
    assert response.status_code == 405, status_message('SC-MNA-001', 405, response, 'Koleksiyon ucunda DELETE desteklenmez -> 405.')
    after_count = model_count('catalog.Article')
    assert after_count == before_count, side_effect_message('SC-MNA-001', 'count_unchanged', before_count, after_count)
