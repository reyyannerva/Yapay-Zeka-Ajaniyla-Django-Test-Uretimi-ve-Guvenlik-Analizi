"""H5-04 raporlama testleri — Issue #42."""
import csv

from agent.evaluation.metrics import Outcome, compute, pytest_summary

from experiments.h5_04_generation_experiment import reporting


def _row(sid, method, outcome):
    return {
        "scenario_id": sid, "http_method": method, "user_role": "user", "secure_status": 200,
        "is_known_flaw": False, "deviation_kind": None, "artifact_origin": f"src/{sid}",
        "artifact_sha256": "0" * 64, "test_function": f"test_{sid.lower()}", "syntax_valid": True,
        "collected": outcome in ("PASS", "FAIL"), "collected_count": 1 if outcome in ("PASS", "FAIL") else 0,
        "exc_type": None, "observed_status": None, "evidence": "", "outcome": outcome,
        "pytest_summary": pytest_summary(outcome), "confusion_cell": "TN" if outcome == "PASS" else "EXCLUDED",
    }


def _summary():
    rows = {
        "rule_based": [_row("SC-RET-002", "GET", "PASS"), _row("SC-AUT-001", "POST", "ENVIRONMENT_ERROR")],
        "llm": [_row("SC-RET-002", "GET", "PASS"), _row("SC-AUT-001", "POST", "NO_ARTIFACT")],
    }
    metrics = {b: compute(Outcome(r["scenario_id"], r["http_method"], r["is_known_flaw"], r["outcome"])
                          for r in rs) for b, rs in rows.items()}
    manifest = {
        "manifest_version": "1.0.0", "issue": "#42",
        "dataset": {"scenario_count": 20, "scenario_ids": ["SC-AUT-001", "SC-RET-002"],
                    "split": "development", "ground_truth_sha256_lf": "abc"},
        "coverage": {"by_method": {"GET": 9, "POST": 9, "PUT": 1, "PATCH": 0, "DELETE": 1},
                     "missing_methods": ["PATCH"]},
        "baselines": {"rule_based": {"generator": "rb v1"}, "llm": {"generator": "llm v1",
                      "model": "groq/openai/gpt-oss-120b"}},
        "cross_reference": {"issue": "#32", "evaluation": "experiments/h3_06_baseline_evaluation",
                            "note": "gerçek PUT/PATCH/DELETE ve açıklar mühürlü test kümesinde #32'de"},
        "focus_note": "Güvenlik F1 üretilmez; odak çalıştırılabilirlik.",
    }
    return {"results": rows, "metrics": metrics, "manifest": manifest,
            "environment_check": {"ok": True, "message": "ok"}}


def test_write_all_is_deterministic(tmp_path):
    reporting.write_all(tmp_path, _summary())
    first = (tmp_path / "results" / "results.json").read_bytes()
    reporting.write_all(tmp_path, _summary())
    assert (tmp_path / "results" / "results.json").read_bytes() == first


def test_comparison_md_cites_issue_32(tmp_path):
    reporting.write_all(tmp_path, _summary())
    md = (tmp_path / "results" / "comparison.md").read_text(encoding="utf-8")
    assert "#32" in md and "mühürlü" in md.lower()


def test_per_scenario_csv_sorted_and_complete(tmp_path):
    reporting.write_all(tmp_path, _summary())
    rows = list(csv.DictReader((tmp_path / "results" / "per_scenario.csv").open(encoding="utf-8")))
    llm = [r["scenario_id"] for r in rows if r["baseline"] == "llm"]
    assert llm == sorted(llm) and len(llm) == 2
    assert {"scenario_id", "baseline", "outcome", "pytest_summary", "syntax_valid"} <= set(rows[0].keys())


def test_metrics_csv_has_row_per_baseline(tmp_path):
    reporting.write_all(tmp_path, _summary())
    rows = list(csv.DictReader((tmp_path / "results" / "metrics.csv").open(encoding="utf-8")))
    assert {r["baseline"] for r in rows} == {"rule_based", "llm"}
