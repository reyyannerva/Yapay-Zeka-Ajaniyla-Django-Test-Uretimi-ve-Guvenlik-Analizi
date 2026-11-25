"""Sonuç dosyaları ile metrik motorunun bağımsız çapraz kontrolü ve dosyalar arası tutarlılık."""
from __future__ import annotations

import csv
import json

from experiments.h5_05_hybrid_experiment import config as C
from experiments.h5_05_hybrid_experiment import verify_metrics


def test_engine_matches_independent_recomputation():
    assert verify_metrics.check() == []


def test_comparison_csv_matches_metrics_summary():
    summary = json.loads((C.RESULTS / "metrics_summary.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((C.RESULTS / "comparison_table.csv").open(encoding="utf-8")))
    assert len(rows) == 6
    for r in rows:
        s = summary["layers"][r["layer"]]["methods"][r["method"]]
        assert r["f1"] == s["f1"]["display"]
        assert r["first_pass_executable_exact"] == f"{s['first_pass_executable']['count']}/{s['first_pass_executable']['of']}"
        assert int(r["TP"]) == s["confusion"]["TP"]


def test_no_stale_blocked_results_in_current_tables():
    summary = json.loads((C.RESULTS / "metrics_summary.json").read_text(encoding="utf-8"))
    exe = json.loads((C.RESULTS / "execution_results.json").read_text(encoding="utf-8"))
    if summary["layers"]["B"]["llm_status"] == "GENERATED":
        assert all(r["evaluation_eligibility"] == "eligible" for r in exe)
        assert not any("LLM_GENERATION_BLOCKED" in (r.get("not_run_reason") or "") for r in exe)
        decs = [json.loads(x) for x in (C.RESULTS / "hybrid_decisions.jsonl").read_text(encoding="utf-8").splitlines()]
        assert all(d["candidate_status"].get("llm") != "ABSENT" for d in decs if d["layer"] == "B")


def test_each_flaw_counted_once_per_method():
    matches = json.loads((C.RESULTS / "ground_truth_matches.json").read_text(encoding="utf-8"))
    keys = [(m["layer"], m["generation_method"], m["scenario_id"]) for m in matches]
    assert len(keys) == len(set(keys))
