"""H5-04 dev deney manifesti testleri — Issue #42."""
import json

import pytest

from agent.evaluation import manifest as mf
from experiments.h5_04_generation_experiment import manifest

REPO = mf.REPO


def test_dev_ids_are_the_20_development_scenarios():
    ids = manifest.DEV_IDS()
    assert len(ids) == 20
    assert len(ids) == len(set(ids))
    split = json.loads((REPO / "benchmarks/reference_cases/split.json").read_text(encoding="utf-8"))
    assert all(split["scenario_split"][i] == "dev" for i in ids)
    test_ids = set(json.loads(
        (REPO / "benchmarks/reference_cases/test_set.json").read_text(encoding="utf-8"))["scenario_ids"])
    assert set(ids).isdisjoint(test_ids)  # sızıntı yok: dev ∩ test = ∅


def test_build_manifest_has_dev_records_and_provenance():
    m = manifest.build()
    assert m["issue"] == "#42"
    assert m["dataset"]["scenario_count"] == 20
    assert m["dataset"]["split"] == "development"
    assert len(m["scenarios"]) == 20
    assert all(r["is_known_flaw"] is False for r in m["scenarios"])  # dev'de bilinen açık yok
    assert m["baselines"]["llm"]["model"] == "groq/openai/gpt-oss-120b"
    assert m["baselines"]["llm"]["first_pass_only"] is True
    assert "llm_reused_from" in m["baselines"]["llm"]
    assert m["baselines"]["rule_based"]["deterministic"] is True


def test_coverage_matches_development_split():
    cov = manifest.build()["coverage"]
    # Dev kümesi gerçeği: GET ve POST yoğun temsil; PUT/DELETE yalnızca 405 (method-not-allowed)
    # senaryolarında (SC-MNA-002/001); PATCH dev'de yok. Gerçek güncelleme/silme (2xx/4xx) ve bilinen
    # güvenlik açıkları mühürlü test kümesinde #32'de değerlendirilir.
    assert cov["by_method"]["GET"] > 0
    assert cov["by_method"]["POST"] > 0
    assert cov["missing_methods"] == ["PATCH"]


def test_cross_reference_points_to_issue_32():
    cr = manifest.build()["cross_reference"]
    assert cr["issue"] == "#32"
    assert "h3_06" in cr["evaluation"]


def test_verify_round_trips_clean():
    m = manifest.build()
    assert manifest.verify(m) == []


def test_build_raises_if_dev_scenario_missing_ground_truth(monkeypatch):
    real_index = mf.ground_truth_index

    def partial_index(*args, **kwargs):
        idx = dict(real_index(*args, **kwargs))
        idx.pop(manifest.DEV_IDS()[0], None)
        return idx

    monkeypatch.setattr(manifest.mf, "ground_truth_index", partial_index)
    with pytest.raises(mf.IntegrityError):
        manifest.build()
