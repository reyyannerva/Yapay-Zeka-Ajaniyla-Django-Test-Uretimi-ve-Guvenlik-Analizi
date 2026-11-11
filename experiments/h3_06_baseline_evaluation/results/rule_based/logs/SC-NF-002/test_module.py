import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from h304_support import model_count, route_message, side_effect_message, snapshot, status_message
pytestmark = pytest.mark.django_db


def test_sc_nf_002_delete_owner_404(seeded_db, api_client):
    """SC-NF-002 · DELETE /api/articles/999/ · owner (alice; fixture ilişkisi: belirlenemez) · beklenen 404
    
    Beklenen davranış: Kimliği doğrulanmış kullanıcı mevcut olmayan kaydı silemez -> 404.
    Referans: ground_truth.json (DRF_SEMANTICS, verified); kategori: HTTP_BEHAVIOR
    Endpoint: EP-ARTICLE-DETAIL (article-detail), işlem: destroy; yan etki kuralı: resource_still_absent
    Uyarı [OWNERSHIP_UNVERIFIABLE]: owner rolünün sahipliği fixture'dan doğrulanamadı; test kimliği doğrulanmış kullanıcı olarak üretildi
    """
    api_client.force_authenticate(user=User.objects.get(username='alice'))
    url = reverse('article-detail', kwargs={'pk': 999})
    assert url == '/api/articles/999/', route_message('SC-NF-002', '/api/articles/999/', url)
    response = api_client.delete(url)
    assert response.status_code == 404, status_message('SC-NF-002', 404, response, 'Kimliği doğrulanmış kullanıcı mevcut olmayan kaydı silemez -> 404.')
    after = snapshot('catalog.Article', 999, ['title', 'body', 'is_published'])
    assert after is None, side_effect_message('SC-NF-002', 'resource_still_absent', None, after)
