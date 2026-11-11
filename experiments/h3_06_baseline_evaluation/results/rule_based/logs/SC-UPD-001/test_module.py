import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_upd_001_put_owner_200(seeded_db, api_client):
    """SC-UPD-001 · PUT /api/articles/1/ · owner (alice; fixture ilişkisi: kaynak_sahibi) · beklenen 200
    
    Beklenen davranış: Sahip kendi kaydını tam günceller.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: update; yan etki kuralı: update_applied
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-detail', kwargs={'pk': 1})
    assert url == '/api/articles/1/', route_message('SC-UPD-001', '/api/articles/1/', url)
    before = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    response = api_client.put(url, {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 200, status_message('SC-UPD-001', 200, response, 'Sahip kendi kaydını tam günceller.')
    after = snapshot('catalog.Article', 1, ['title', 'body', 'is_published'])
    observed = {key: after[key] for key in ['body', 'title']} if after else None
    assert observed == {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, side_effect_message('SC-UPD-001', 'update_applied', {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, observed)
