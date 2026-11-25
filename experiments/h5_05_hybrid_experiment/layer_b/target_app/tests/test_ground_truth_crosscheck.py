"""Katman B fixture ↔ ground truth çapraz kontrolü — H5-05 / Issue #43.

Ground truth'un fixture davranışıyla tutarlı olduğunu ÜRETİCİDEN BAĞIMSIZ kanıtlar (H3-03
`test_ground_truth_crosscheck.py` ile aynı yaklaşım):
* Kusursuz senaryolarda uygulamanın durum kodu = güvenli beklenti (`secure_status`).
* Bilinen kusurlu senaryolarda uygulama güvenli beklentiden SAPAR ve kayıtlı `observed_flawed_status`'u üretir.
"""
import json
from pathlib import Path

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

LAYER_B = Path(__file__).resolve().parents[2]
SCENARIOS = {s["id"]: s for s in json.loads((LAYER_B / "scenarios.json").read_text(encoding="utf-8"))["scenarios"]}
TRUTH = json.loads((LAYER_B / "ground_truth.json").read_text(encoding="utf-8"))["records"]


def _call(record):
    sc = SCENARIOS[record["scenario_id"]]
    client = APIClient()
    if sc["fixture_ref"]["user"]:
        client.force_authenticate(user=User.objects.get(username=sc["fixture_ref"]["user"]))
    send = getattr(client, sc["http_method"].lower())
    return send(sc["endpoint"], sc["request_input"], format="json") if sc["request_input"] is not None \
        else send(sc["endpoint"])


@pytest.mark.parametrize("record", TRUTH, ids=[r["scenario_id"] for r in TRUTH])
def test_fixture_behaviour_matches_ground_truth(seeded_db, record):
    status = _call(record).status_code
    if record["is_known_flaw"]:
        assert status != record["expected_result"]["secure_status"]
        assert status == record["security_finding"]["observed_flawed_status"]
    else:
        assert status == record["expected_result"]["secure_status"]


def test_ground_truth_and_scenarios_are_consistent():
    assert set(SCENARIOS) == {r["scenario_id"] for r in TRUTH}
    for r in TRUTH:
        sc = SCENARIOS[r["scenario_id"]]
        assert (sc["http_method"], sc["user_role"]) == (r["http_method"], r["user_role"])
        assert sc["is_intentional_flaw"] == r["is_known_flaw"]


def test_all_five_http_methods_and_flaws_are_present():
    methods = {r["http_method"] for r in TRUTH}
    assert methods == {"GET", "POST", "PUT", "PATCH", "DELETE"}
    assert sum(r["is_known_flaw"] for r in TRUTH) == 3
