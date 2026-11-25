"""Hibrit birleştirme politikası, normalizasyon ve etiket sızıntısı testleri."""
from __future__ import annotations

from agent.evaluation.artifacts import Artifact

from experiments.h5_05_hybrid_experiment import hybrid, reference
from experiments.h5_05_hybrid_experiment.normalize import signature

ROUTES = {"task-detail": "/api/tasks/{pk}/"}
HDR = "import pytest\nfrom django.contrib.auth.models import User\nfrom django.urls import reverse\n"


def src(method="patch", status=403, user="mehmet", extra=""):
    auth = f"    api_client.force_authenticate(user=User.objects.get(username='{user}'))\n" if user else ""
    return (HDR + "def test_x(seeded_db, api_client):\n" + auth +
            "    url = reverse('task-detail', kwargs={'pk': 1})\n"
            f"    response = api_client.{method}(url, {{'title': 'a'}}, format='json')\n"
            f"    assert response.status_code == {status}\n" + extra)


REF = hybrid.Reference("SC-1", "PATCH", "/api/tasks/1/", "user", "mehmet", 403, "SC-1:expected_result")


def art(method, source):
    return Artifact("SC-1", method, f"{method}.py", source, "test_x", {})


def test_signature_extraction():
    s = signature(src(), ROUTES)
    assert s.key() == ("PATCH", "/api/tasks/1/", "authenticated", "mehmet", 403)
    assert s.payload == {"title": "a"} and "seeded_db" in s.preconditions
    assert signature("def x(:", ROUTES).parse_ok is False


def test_duplicate_keeps_rule_based():
    a, d, c = hybrid.merge("T", REF, [art("rule_based", src())], [art("llm", src())], ROUTES)
    assert d.provenance == "common" and d.duplicates == 1 and a.source == src() and d.final_source == "rule_based"
    assert {x["status"] for x in c} == {"SELECTED", "DROPPED_DUPLICATE"}


def test_llm_conflicting_with_reference_rejected():
    a, d, _ = hybrid.merge("T", REF, [art("rule_based", src())], [art("llm", src(status=200))], ROUTES)
    assert d.final_source == "rule_based" and d.candidate_status["llm"] == "REJECTED_REFERENCE_CONFLICT"
    assert d.conflicts_resolved == 1


def test_wrong_method_rejected_and_llm_only_kept():
    a, d, _ = hybrid.merge("T", REF, [art("rule_based", src(method="put"))], [art("llm", src())], ROUTES)
    assert d.provenance == "llm_only" and d.final_source == "llm"


def test_unresolved_when_no_candidate_consistent():
    a, d, _ = hybrid.merge("T", REF, [art("rule_based", src(status=200))], [art("llm", src(user=None))], ROUTES)
    assert a is None and d.conflicts_unresolved == 1 and d.provenance == "unresolved"


def test_resolved_conflict_prefers_richer_assertions():
    ref = hybrid.Reference("SC-1", "PATCH", "/api/tasks/1/", "user", None, 403, "r")
    rich = src(user="zeynep", extra="    assert response.data['detail']\n")
    a, d, _ = hybrid.merge("T", ref, [art("rule_based", src())], [art("llm", rich)], ROUTES)
    assert d.provenance == "resolved_conflict" and d.final_source == "llm"


def test_absent_llm_gives_rule_only():
    a, d, _ = hybrid.merge("T", REF, [art("rule_based", src())], [], ROUTES)
    assert d.provenance == "rule_only" and d.candidate_status["llm"] == "ABSENT"


def test_merge_is_deterministic():
    r1 = hybrid.merge("T", REF, [art("rule_based", src())], [art("llm", src())], ROUTES)
    r2 = hybrid.merge("T", REF, [art("rule_based", src())], [art("llm", src())], ROUTES)
    assert r1[1] == r2[1] and r1[2] == r2[2]


def test_reference_view_masks_labels():
    gt = {"records": [{"scenario_id": "S", "is_known_flaw": True, "security_finding": {"type": "BOLA"},
                       "expected_result": {"secure_status": 403}}]}
    v = reference.reference_view(gt)
    reference.assert_no_label_leak(v)
    assert v["records"][0]["is_known_flaw"] is False and "security_finding" not in v["records"][0]
    assert gt["records"][0]["is_known_flaw"] is True  # orijinal değişmez
    import pytest
    with pytest.raises(ValueError):
        reference.assert_no_label_leak(gt)
