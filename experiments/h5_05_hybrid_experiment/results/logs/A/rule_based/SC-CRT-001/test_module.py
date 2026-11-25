import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_crt_001_post_user_201(seeded_db, api_client):
    """SC-CRT-001 · POST /api/articles/ · user (carol; fixture ilişkisi: kimligi_dogrulanmis) · beklenen 201
    
    Beklenen davranış: Kimliği doğrulanmış kullanıcı geçerli girdiyle kayıt oluşturur; owner isteği yapan olur.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-LIST (article-list), işlem: create; yan etki kuralı: count_plus_one
    """
    api_client.force_authenticate(user=User.objects.get(username='carol'))
    url = reverse('article-list')
    assert url == '/api/articles/', route_message('SC-CRT-001', '/api/articles/', url)
    before_count = model_count('catalog.Article')
    response = api_client.post(url, {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 201, status_message('SC-CRT-001', 201, response, 'Kimliği doğrulanmış kullanıcı geçerli girdiyle kayıt oluşturur; owner isteği yapan olur.')
    after_count = model_count('catalog.Article')
    assert after_count == before_count + 1, side_effect_message('SC-CRT-001', 'count_plus_one', before_count + 1, after_count)
