import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_crt_002_post_owner_201(seeded_db, api_client):
    """SC-CRT-002 · POST /api/articles/ · owner (alice; fixture ilişkisi: kimligi_dogrulanmis) · beklenen 201
    
    Beklenen davranış: Kullanıcı kendi adına kayıt oluşturur.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-LIST (article-list), işlem: create; yan etki kuralı: count_plus_one
    Uyarı [OWNERSHIP_UNVERIFIABLE]: owner rolünün sahipliği fixture'dan doğrulanamadı; test kimliği doğrulanmış kullanıcı olarak üretildi
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-list')
    assert url == '/api/articles/', route_message('SC-CRT-002', '/api/articles/', url)
    before_count = model_count('catalog.Article')
    response = api_client.post(url, {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 201, status_message('SC-CRT-002', 201, response, 'Kullanıcı kendi adına kayıt oluşturur.')
    after_count = model_count('catalog.Article')
    assert after_count == before_count + 1, side_effect_message('SC-CRT-002', 'count_plus_one', before_count + 1, after_count)
