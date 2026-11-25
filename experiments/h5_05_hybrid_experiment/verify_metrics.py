"""Bağımsız metrik çapraz kontrolü — H5-05 / Issue #43.

``metrics.py``'yi KULLANMADAN, yalnızca ``results/execution_results.csv`` ve donmuş ground truth
dosyalarından TP/FP/TN/FN, P/R/F1 ve ilk geçiş çalıştırılabilirliğini yeniden hesaplar ve
``results/metrics_summary.json`` ile karşılaştırır. Kullanım:
``python experiments/h5_05_hybrid_experiment/verify_metrics.py`` (fark varsa çıkış kodu 1).
"""
from __future__ import annotations

import csv
import json
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
GT_FILES = {"A": REPO / "benchmarks" / "reference_cases" / "ground_truth.json",
            "B": HERE / "layer_b" / "ground_truth.json"}


def recompute() -> dict:
    rows = list(csv.DictReader((HERE / "results" / "execution_results.csv").open(encoding="utf-8")))
    gts = {k: {r["scenario_id"]: r for r in json.loads(p.read_text(encoding="utf-8"))["records"]}
           for k, p in GT_FILES.items()}
    out: dict = {}
    for r in rows:
        if r["evaluation_eligibility"] != "eligible":
            continue
        gt = gts[r["layer"]][r["scenario_id"]]
        assert gt["http_method"] == r["http_method"], r
        flaw, o = bool(gt["is_known_flaw"]), r["outcome"]
        cell = ("TP" if flaw else "FP") if o == "FAIL" else ("FN" if flaw else "TN") if o == "PASS" else \
            ("FN" if flaw else "EXCLUDED")
        m = out.setdefault((r["layer"], r["generation_method"]), {"TP": 0, "FP": 0, "TN": 0, "FN": 0, "EXCLUDED": 0,
                                                                    "n": 0, "exe": 0})
        m[cell] += 1
        m["n"] += 1
        m["exe"] += o in ("PASS", "FAIL")
    return out


def _frac(num, den):
    return None if den == 0 else Fraction(num, den)


def check() -> list[str]:
    summary = json.loads((HERE / "results" / "metrics_summary.json").read_text(encoding="utf-8"))
    problems = []
    for (layer, method), m in sorted(recompute().items()):
        s = summary["layers"][layer]["methods"][method]
        p, r = _frac(m["TP"], m["TP"] + m["FP"]), _frac(m["TP"], m["TP"] + m["FN"])
        f1 = None if p is None or r is None or p + r == 0 else 2 * p * r / (p + r)
        exe = _frac(m["exe"], m["n"])
        expect = {"confusion": {k: m[k] for k in ("TP", "FP", "TN", "FN", "EXCLUDED")},
                  "precision": None if p is None else f"{p.numerator}/{p.denominator}",
                  "recall": None if r is None else f"{r.numerator}/{r.denominator}",
                  "f1": None if f1 is None else f"{f1.numerator}/{f1.denominator}",
                  "exec": (m["exe"], m["n"], None if exe is None else f"{exe.numerator}/{exe.denominator}")}
        got = {"confusion": s["confusion"], "precision": s["precision"]["exact"], "recall": s["recall"]["exact"],
               "f1": s["f1"]["exact"], "exec": (s["first_pass_executable"]["count"], s["first_pass_executable"]["of"],
                                                s["first_pass_executable"]["exact"])}
        if expect != got:
            problems.append(f"{layer}/{method}: bağımsız={expect} motor={got}")
    return problems


if __name__ == "__main__":
    probs = check()
    print("Bağımsız metrik çapraz kontrolü: " + ("UYUŞUYOR" if not probs else "FARK VAR"))
    for x in probs:
        print("  " + x)
    sys.exit(1 if probs else 0)
