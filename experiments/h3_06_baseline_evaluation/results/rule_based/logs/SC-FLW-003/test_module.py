import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_flw_003_get_anonymous_200(seeded_db, api_client):
    """SC-FLW-003 · GET /api/insecure/articles/ · anonim · beklenen 200
    
    Beklenen davranış: Liste 200 döner ancak yalnızca yayınlananları; taslaklar gizlenmeli.
    Referans: ground_truth.json (PROJECT_REQUIREMENT, verified); kategori: SECURITY_CONFIGURATION
    Endpoint: EP-INSECURE-ARTICLE-LIST (insecure-article-list), işlem: list; yan etki kuralı: none
    Bilinen güvenlik kusuru: Hassas veri ifşası / bozuk fonksiyon düzeyi yetkilendirme — güvensiz uçta gözlenen 200 (content sapması).
    Uyarı [CONTENT_ASSERTION_UNSUPPORTED]: Referanstaki güvenlik beklentisi içerik düzeyinde ve makine-okunur değil; yalnızca durum kodu doğrulanır, bilinen kusur bu testle tespit EDİLEMEZ
    """
    url = reverse('insecure-article-list')
    assert url == '/api/insecure/articles/', route_message('SC-FLW-003', '/api/insecure/articles/', url)
    response = api_client.get(url)
    assert response.status_code == 200, status_message('SC-FLW-003', 200, response, 'Liste 200 döner ancak yalnızca yayınlananları; taslaklar gizlenmeli.')
