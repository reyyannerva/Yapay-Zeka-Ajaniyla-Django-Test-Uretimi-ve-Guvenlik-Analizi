import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_upd_002_put_admin_200(seeded_db, api_client):
    """SC-UPD-002 · PUT /api/articles/3/ · admin (admin; fixture ilişkisi: yonetici) · beklenen 200
    
    Beklenen davranış: Yönetici herhangi bir kaydı tam günceller.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: update; yan etki kuralı: update_applied
    """
    api_client.force_authenticate(user=User.objects.get(username='admin'))
    url = reverse('article-detail', kwargs={'pk': 3})
    assert url == '/api/articles/3/', route_message('SC-UPD-002', '/api/articles/3/', url)
    before = snapshot('catalog.Article', 3, ['title', 'body', 'is_published'])
    response = api_client.put(url, {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 200, status_message('SC-UPD-002', 200, response, 'Yönetici herhangi bir kaydı tam günceller.')
    after = snapshot('catalog.Article', 3, ['title', 'body', 'is_published'])
    observed = {key: after[key] for key in ['body', 'title']} if after else None
    assert observed == {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, side_effect_message('SC-UPD-002', 'update_applied', {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, observed)
