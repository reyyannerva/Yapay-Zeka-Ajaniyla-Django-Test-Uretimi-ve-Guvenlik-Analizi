"""H5-05 deney sonuçlarından frontend anlık görüntüsü üretir — H5-06 / Issue #44.

Kaynak: ``experiments/h5_05_hybrid_experiment/results/metrics_summary.json`` (H5-05, #43, merge 391a58d).
Hedef: ``frontend/src/data/h5-05-experiment.json``. Değerler kopyalanır, yeniden hesaplanmaz veya
yuvarlanmaz; ölçülemeyen değerler ``null`` + "Ölçülemedi" olarak kalır. Kaynak dosyanın SHA-256 özeti
anlık görüntüye yazılır; ``--check`` kipinde güncel olup olmadığı doğrulanır.

    python -m demo.h5_06.export_experiment_snapshot          # yaz
    python -m demo.h5_06.export_experiment_snapshot --check  # güncel mi? (değilse çıkış 1)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "experiments" / "h5_05_hybrid_experiment" / "results" / "metrics_summary.json"
CONFIG = SOURCE.with_name("experiment_config.json")
TARGET = REPO / "frontend" / "src" / "data" / "h5-05-experiment.json"
METHOD_LABELS = {"rule_based": "Kural tabanlı (H3-04)", "llm": "Groq LLM (H3-05)", "hybrid": "Hibrit (H5-05)"}


def _metric(m: dict) -> dict:
    return {"value": m["value"], "exact": m["exact"], "display": m["display"]}


def build() -> dict:
    raw = SOURCE.read_bytes()
    s = json.loads(raw)
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    models = {m for m in cfg["actual_model_by_layer"].values() if m}
    if len(models) != 1:
        raise ValueError(f"katmanlar arasında tek model beklenir: {models}")
    layers = []
    for name, info in s["layers"].items():
        methods = []
        for key, mm in info["methods"].items():
            methods.append({
                "key": key, "label": METHOD_LABELS[key], "attempted": mm["attempted"], "scenarios": mm["scenarios"],
                "confusion": mm["confusion"], "precision": _metric(mm["precision"]), "recall": _metric(mm["recall"]),
                "f1": _metric(mm["f1"]),
                "syntaxValid": {"count": mm["syntax_valid"]["count"], "of": mm["syntax_valid"]["of"]},
                "collected": {"count": mm["collected"]["count"], "of": mm["collected"]["of"]},
                "firstPassExecutable": {"count": mm["first_pass_executable"]["count"],
                                        "of": mm["first_pass_executable"]["of"],
                                        **_metric(mm["first_pass_executable"])},
                "testLevel": {"executable": mm["test_level"]["executable"], "tests": mm["test_level"]["tests"]},
                "status5": {k: mm["status5"].get(k, 0) for k in ("PASS", "FAIL", "ERROR", "TIMEOUT", "NOT_RUN")},
                "targets": {"f1": mm["target_status"]["f1_gte_0_80"],
                            "executability": mm["target_status"]["first_pass_executable_gte_0_70"]},
            })
        h = info["hybrid"]
        layers.append({
            "key": name, "scenarios": info["scenarios"], "splitName": info["split_name"],
            "positives": info["positives"], "httpMethods": info["http_methods"],
            "llmStatus": info["llm_status"], "llmNote": info["llm_note"],
            "llmModel": cfg["actual_model_by_layer"][name],
            "comparable": info["comparability"]["comparable"], "comparabilityReason": info["comparability"]["reason"],
            "hybrid": {k: h[k] for k in ("rule_based_candidates", "llm_candidates", "duplicates", "merged",
                                         "conflicts_resolved", "conflicts_unresolved", "final_tests",
                                         "code_identical_pairs", "semantic_key_equal_pairs")},
            "methods": methods,
        })
    return {
        "kind": "OFFLINE_EXPERIMENT",
        "issue": "#43",
        "experimentId": s["experiment_id"],
        "source": str(SOURCE.relative_to(REPO)).replace("\\", "/"),
        "sourceSha256": hashlib.sha256(raw).hexdigest(),
        "runTimestampUtc": s["environment"]["timestamp_utc"],
        "model": models.pop(),
        "plannedModel": cfg["planned_model"],
        "promptVersion": "pytest_v1",
        "targets": {"f1": 0.8, "executability": 0.7},
        "definitions": s["definitions"],
        "layers": layers,
    }


def render() -> str:
    return json.dumps(build(), ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    text = render()
    if args.check:
        ok = TARGET.exists() and TARGET.read_text(encoding="utf-8") == text
        print("anlık görüntü " + ("güncel" if ok else "GÜNCEL DEĞİL"))
        return 0 if ok else 1
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(text, encoding="utf-8", newline="\n")
    print(f"yazıldı: {TARGET.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
