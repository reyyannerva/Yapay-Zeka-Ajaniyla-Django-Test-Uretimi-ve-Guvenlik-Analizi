"""Senaryo ↔ uygulama eşleşme testi — H3-01 / Issue #27.

scenarios.json içindeki HER senaryoyu kontrollü uygulamaya karşı yeniden oynatır ve
beklenen HTTP durum kodunun gerçekten üretildiğini doğrular. Böylece veri kümesi ile
hedef uygulama arasındaki tutarlılık mekanik olarak garanti edilir (ileride kaymayı da
yakalar). Bilerek-hatalı senaryolarda beklenen durum, güvensiz uçta GÖZLEMLENEN davranıştır.
"""
import json
from pathlib import Path

import pytest
from django.contrib.auth.models import User

SCENARIOS_PATH = Path(__file__).resolve().parents[2] / "scenarios" / "scenarios.json"
SCENARIOS = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))["scenarios"]

pytestmark = pytest.mark.django_db

_CALL = {
    "GET": lambda c, url, body: c.get(url),
    "DELETE": lambda c, url, body: c.delete(url),
    "POST": lambda c, url, body: c.post(url, body or {}, format="json"),
    "PUT": lambda c, url, body: c.put(url, body or {}, format="json"),
    "PATCH": lambda c, url, body: c.patch(url, body or {}, format="json"),
}


@pytest.mark.parametrize("sc", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
def test_scenario_matches_app(seeded_db, api, sc):
    username = sc["fixture_ref"]["user"]
    if username:
        api.force_authenticate(user=User.objects.get(username=username))
    resp = _CALL[sc["http_method"]](api, sc["endpoint"], sc["request_input"])
    assert resp.status_code == sc["expected_http_status"], (
        f"{sc['id']}: {sc['http_method']} {sc['endpoint']} "
        f"beklenen {sc['expected_http_status']}, gelen {resp.status_code}"
    )
