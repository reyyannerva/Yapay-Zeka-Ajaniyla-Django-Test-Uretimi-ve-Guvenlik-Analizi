import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_nf_001_put_owner_404(seeded_db, api_client):
    """SC-NF-001 · PUT /api/articles/999/ · owner (alice; fixture ilişkisi: belirlenemez) · beklenen 404
    
    Beklenen davranış: Kimliği doğrulanmış kullanıcı mevcut olmayan kaydı güncelleyemez -> 404.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: update; yan etki kuralı: resource_still_absent
    Uyarı [OWNERSHIP_UNVERIFIABLE]: owner rolünün sahipliği fixture'dan doğrulanamadı; test kimliği doğrulanmış kullanıcı olarak üretildi
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-detail', kwargs={'pk': 999})
    assert url == '/api/articles/999/', route_message('SC-NF-001', '/api/articles/999/', url)
    response = api_client.put(url, {'body': 'örnek içerik', 'title': 'Örnek Başlık'}, format='json')
    assert response.status_code == 404, status_message('SC-NF-001', 404, response, 'Kimliği doğrulanmış kullanıcı mevcut olmayan kaydı güncelleyemez -> 404.')
    after = snapshot('catalog.Article', 999, ['title', 'body', 'is_published'])
    assert after is None, side_effect_message('SC-NF-001', 'resource_still_absent', None, after)
