"""Ground truth ↔ uygulama çapraz-kontrolü — H3-03 / Issue #29.

Ground truth'un BAĞIMSIZLIĞINI ve bilinen hataların GERÇEKLİĞİNİ kanıtlar:
  - Hatasız senaryolarda: uygulamanın gözlemlenen davranışı = altın güvenli durum.
  - Bilinen hatalarda: uygulama altın (güvenli) durumdan SAPAR
      * deviation_kind=status  -> gözlemlenen durum kodu, güvenli durumdan farklı (ve
        security_finding.observed_flawed_status'a eşit).
      * deviation_kind=content -> durum kodu aynı (200) ama içerik güvenlik dışı
        (güvensiz liste taslakları ifşa eder).

Böylece ground truth, uygulamanın hatalı davranışını tekrar etmez; beklenen güvenli
davranış bağımsız olarak tanımlanmıştır.
"""
import json
from pathlib import Path

import pytest
from django.contrib.auth.models import User

BASE = Path(__file__).resolve().parents[1]
BENCH = BASE.parent
SCEN = {s["id"]: s for s in json.loads(
    (BENCH / "drf_fixtures" / "scenarios" / "scenarios.json").read_text(encoding="utf-8"))["scenarios"]}
RECORDS = json.loads((BASE / "ground_truth.json").read_text(encoding="utf-8"))["records"]

pytestmark = pytest.mark.django_db

_CALL = {
    "GET": lambda c, url, body: c.get(url),
    "DELETE": lambda c, url, body: c.delete(url),
    "POST": lambda c, url, body: c.post(url, body or {}, format="json"),
    "PUT": lambda c, url, body: c.put(url, body or {}, format="json"),
    "PATCH": lambda c, url, body: c.patch(url, body or {}, format="json"),
}


def _invoke(api, sc):
    username = sc["fixture_ref"]["user"]
    if username:
        api.force_authenticate(user=User.objects.get(username=username))
    return _CALL[sc["http_method"]](api, sc["endpoint"], sc["request_input"])


@pytest.mark.parametrize("rec", RECORDS, ids=[r["scenario_id"] for r in RECORDS])
def test_ground_truth_vs_app(seeded_db, api, rec):
    sc = SCEN[rec["scenario_id"]]
    resp = _invoke(api, sc)
    gold = rec["expected_result"]["secure_status"]

    if not rec["is_known_flaw"]:
        # Uygulama doğru; altın güvenli durum gerçeğe eşit olmalı.
        assert resp.status_code == gold, f"{rec['scenario_id']}: beklenen {gold}, gelen {resp.status_code}"
        return

    sf = rec["security_finding"]
    if sf["deviation_kind"] == "status":
        assert resp.status_code == sf["observed_flawed_status"], (
            f"{rec['scenario_id']}: gözlemlenen hatalı durum {sf['observed_flawed_status']} bekleniyordu, "
            f"gelen {resp.status_code}")
        assert resp.status_code != gold, (
            f"{rec['scenario_id']}: güvensiz uç altın güvenli durumdan ({gold}) sapmalıydı")
    else:  # content
        assert resp.status_code == gold  # durum kodu aynı (200)
        titles = {a["title"] for a in resp.json()}
        assert any("Draft" in t for t in titles), (
            f"{rec['scenario_id']}: güvensiz liste taslak ifşa etmeliydi (içerik sapması)")
