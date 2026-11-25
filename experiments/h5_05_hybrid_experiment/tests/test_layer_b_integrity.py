"""Katman B dondurma, etiket sızıntısı ve kapsam testleri."""
from __future__ import annotations

import json

from agent.evaluation import manifest as mf

from experiments.h5_05_hybrid_experiment import config as C
from experiments.h5_05_hybrid_experiment import layer_b_inputs, reference


def test_frozen_inputs_unchanged():
    assert layer_b_inputs.verify_frozen() == []


def test_all_five_http_methods_and_flaws_present():
    gt = mf.load_json(C.LAYER_B_FILES["ground_truth"])
    methods = {r["http_method"] for r in gt["records"]}
    assert methods == set(C.HTTP_METHODS)
    assert sum(r["is_known_flaw"] for r in gt["records"]) == 3


def test_no_overlap_with_sealed_test_set_ids():
    split = mf.load_json(mf.REF / "split.json")["scenario_split"]
    gt = mf.load_json(C.LAYER_B_FILES["ground_truth"])
    assert not ({r["scenario_id"] for r in gt["records"]} & set(split))


def test_generator_inputs_are_label_free():
    for name in ("reference_requirements.json", "scenarios.json"):
        reference.assert_no_label_leak(json.loads((C.LAYER_B_INPUTS / name).read_text(encoding="utf-8")))
    prompts = sorted((C.LAYER_B_LLM / "prompts_sent").glob("*.txt"))
    assert len(prompts) == 17
    for p in prompts:
        t = p.read_text(encoding="utf-8").lower()
        assert "flaw" not in t and "security_finding" not in t and "is_known_flaw" not in t


def test_endpoint_summary_hides_insecure_flag():
    ep = mf.load_json(C.LAYER_B_FILES["endpoints"])
    assert all(e["intentionally_insecure"] is False for e in ep["endpoints"])
