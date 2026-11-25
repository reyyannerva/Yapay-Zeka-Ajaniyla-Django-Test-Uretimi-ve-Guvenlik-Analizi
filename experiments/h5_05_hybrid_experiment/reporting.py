"""Sonuç dosyalarını yazar (JSON/CSV/MD/JSONL) — H5-05 / Issue #43.

Ölçülemeyen değerler "Ölçülemedi" olarak yazılır; asla 0 veya 1 ile doldurulmaz.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from . import config as C
from . import metrics as M

EXEC_FIELDS = ("layer", "generation_method", "scenario_id", "http_method", "user_role", "secure_status",
               "is_known_flaw", "outcome", "status", "syntax_valid", "collected", "collected_count", "test_count",
               "executable_tests", "failing_tests", "observed_status", "exc_type", "not_run_reason", "evidence",
               "artifact_origin", "artifact_sha256", "input_hash", "evaluation_eligibility", "confusion_cell")
MATCH_FIELDS = ("layer", "generation_method", "scenario_id", "http_method", "gt_is_known_flaw", "gt_finding_type",
                "gt_secure_status", "gt_observed_flawed_status", "outcome", "status", "predicted_finding",
                "observed_status", "failing_tests_in_scenario", "confusion_cell")


def _w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _wj(path: Path, obj) -> None:
    _w(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def build_summary(runs: dict, env: dict) -> dict:
    from .runner import sealed_ids
    sealed = sealed_ids()
    layers = {}
    matches = []
    for name, run in runs.items():
        gt = run["layer"]["ground_truth"]
        methods = {}
        for method, rows in run["results"].items():
            attempted = not (method == "llm" and run["layer"]["llm"]["status"] == "BLOCKED")
            methods[method] = M.method_metrics(rows, gt, sealed, attempted)
            eligible, _ = M.validate_rows(rows, gt, sealed)
            matches.extend(M.ground_truth_matches(eligible, gt))
        comp = M.comparability({m: (r if methods[m]["attempted"] else []) for m, r in run["results"].items()})
        methods_by_http = Counter(gt[s]["http_method"] for s in run["layer"]["ids"])
        layers[name] = {
            "scenarios": len(run["layer"]["ids"]), "split_name": run["layer"]["split_name"],
            "dataset_version": run["layer"]["dataset_version"],
            "positives": sum(1 for s in run["layer"]["ids"] if gt[s]["is_known_flaw"]),
            "http_methods": {m: methods_by_http.get(m, 0) for m in C.HTTP_METHODS},
            "llm_status": run["layer"]["llm"]["status"], "llm_note": run["layer"]["llm"]["note"],
            "comparability": comp, "hybrid": run["hybrid_summary"], "methods": methods,
            "environment_check": run["environment"],
        }
    return {"experiment_id": C.EXPERIMENT_ID, "version": C.EXPERIMENT_VERSION, "issue": "#43",
            "targets": {"f1": ">= 0.80 (4/5)", "first_pass_executable": ">= 0.70 (7/10)"},
            "definitions": {
                "first_pass_executable": "pay = PASS+FAIL sonuçlanan senaryo sayısı (ilk üretim, otomatik düzeltme yok); "
                                         "payda = katmandaki tüm değerlendirilebilir senaryolar (test üretilmeyenler dahil)",
                "test_level_executable": "pay = PASS/FAIL sonuçlanan test fonksiyonu; payda = toplanan test fonksiyonu",
                "confusion": "senaryo düzeyi; FAIL+kusur=TP, FAIL+kusursuz=FP, PASS+kusur=FN, PASS+kusursuz=TN, "
                             "teknik/çalışmayan+kusur=FN, teknik/çalışmayan+kusursuz=EXCLUDED",
                "not_measurable": "payda sıfır → Ölçülemedi"},
            "environment": env, "layers": layers}, matches


def _md_table(rows: list[dict], cols: list[tuple[str, str]]) -> str:
    out = ["| " + " | ".join(h for _, h in cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(k, "")) for k, _ in cols) + " |")
    return "\n".join(out)


COMP_COLS = [("method", "Yöntem"), ("attempted", "Denendi"), ("scenarios", "Senaryo"), ("TP", "TP"), ("FP", "FP"),
             ("TN", "TN"), ("FN", "FN"), ("EXCLUDED", "Hariç"), ("precision", "Precision"), ("recall", "Recall"),
             ("f1", "F1"), ("syntax", "Sözdizimi geçerli"), ("collected", "Toplanan"),
             ("first_pass_executable_exact", "İlk geçiş çalıştırılabilir (pay/payda)"),
             ("first_pass_executable", "Oran"), ("test_level_executable", "Test düzeyi"),
             ("status5", "PASS/FAIL/ERROR/TIMEOUT/NOT_RUN"), ("f1_target", "F1 ≥ 0.80"),
             ("executability_target", "Çalıştırılabilirlik ≥ %70")]


def comparison_markdown(summary: dict) -> str:
    parts = ["# H5-05 karşılaştırma tablosu (geliştirme kümesi — nihai performans DEĞİLDİR)\n"]
    rows = M.comparison_rows(summary)
    for layer, info in summary["layers"].items():
        title = ("Katman A — H5-04'ün 20 geliştirme senaryosu" if layer == "A"
                 else "Katman B — kontrollü ek geliştirme kümesi (17 senaryo, 5 HTTP metodu)")
        parts.append(f"## {title}\n")
        parts.append(f"HTTP metotları: {info['http_methods']} · bilinen kusur: {info['positives']} · "
                     f"karşılaştırılabilirlik: {'evet' if info['comparability']['comparable'] else 'HAYIR'} "
                     f"({info['comparability']['reason']})\n")
        lr = []
        for r in rows:
            if r["layer"] != layer:
                continue
            mm = info["methods"][r["method"]]
            s5 = mm["status5"]
            lr.append({**r, "syntax": f"{mm['syntax_valid']['count']}/{mm['syntax_valid']['of']}",
                       "collected": f"{mm['collected']['count']}/{mm['collected']['of']}",
                       "status5": "/".join(str(s5.get(k, 0)) for k in M.STATUS5) if mm["attempted"] else "denenmedi"})
        parts.append(_md_table(lr, COMP_COLS) + "\n")
        if info["llm_status"] == "BLOCKED":
            parts.append(f"> LLM: {info['llm_note']}\n")
    return "\n".join(parts)


def write_all(runs: dict, out: Path, env: dict, config: dict) -> dict:
    summary, matches = build_summary(runs, env)
    exec_rows, manifests, decisions, cands, raw = [], [], [], [], {}
    for name, run in runs.items():
        for method in C.METHODS:
            manifests.extend(run["manifests"][method])
            exec_rows.extend({k: v for k, v in r.items() if k != "artifacts_hash"} for r in run["results"][method])
        decisions.extend({"layer": name, **asdict(d)} for d in run["decisions"])
        cands.extend(run["candidates"])
        lay = run["layer"]
        raw[name] = {
            "rule_based": {"source": lay["rule_based_source"], "status": "ARCHIVED_FIRST_PASS" if name == "A" else
                           "GENERATED_IN_H5_05 (etiket maskeli girdi)",
                           "artifacts": {s: [a.origin for a in v] for s, v in lay["candidates"]["rule_based"].items()}},
            "llm": {**lay["llm"], "artifacts": {s: [a.origin for a in v] for s, v in lay["candidates"]["llm"].items()}},
        }
    _wj(out / "scenario_manifest.json", {"experiment_id": C.EXPERIMENT_ID, "rows": manifests})
    _wj(out / "experiment_config.json", config)
    _w(out / "hybrid_candidates.jsonl", "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cands))
    _w(out / "hybrid_decisions.jsonl", "".join(json.dumps(d, ensure_ascii=False) + "\n" for d in decisions))
    _wj(out / "raw_generation_results.json", raw)
    _wj(out / "execution_results.json", exec_rows)
    _w(out / "execution_results.csv", M.to_csv(exec_rows, EXEC_FIELDS))
    _wj(out / "ground_truth_matches.json", matches)
    _w(out / "ground_truth_matches.csv", M.to_csv(matches, MATCH_FIELDS))
    _wj(out / "metrics_summary.json", summary)
    comp = M.comparison_rows(summary)
    comp_csv = M.to_csv(comp, M.CSV_FIELDS)
    if not M.csv_matches_json(comp_csv, comp, M.CSV_FIELDS):
        raise AssertionError("karşılaştırma CSV'si JSON ile tutarsız")
    _w(out / "comparison_table.csv", comp_csv)
    _w(out / "comparison_table.md", comparison_markdown(summary))
    coverage = {name: {"http_methods": info["http_methods"],
                       "methods_executed": {m: info["methods"][m]["attempted"] for m in C.METHODS},
                       "by_http_method": {m: info["methods"][m]["by_method"] for m in C.METHODS}}
                for name, info in summary["layers"].items()}
    coverage["union_http_methods_per_generation_method"] = {
        m: sorted({h for n, info in summary["layers"].items() if info["methods"][m]["attempted"]
                   for h, c in info["http_methods"].items() if c}) for m in C.METHODS}
    _wj(out / "coverage_report.json", coverage)
    failures = [{k: r.get(k) for k in ("layer", "generation_method", "scenario_id", "http_method", "outcome", "status",
                                       "exc_type", "observed_status", "not_run_reason", "evidence", "is_known_flaw")}
                for r in exec_rows if r["outcome"] != "PASS"]
    _wj(out / "failure_analysis.json", {
        "note": "PASS dışı tüm satırlar. FAIL + bilinen kusur = beklenen tespit (TP); diğerleri hata analizi.",
        "counts": dict(Counter(f"{f['layer']}/{f['generation_method']}/{f['outcome']}" for f in failures)),
        "rows": failures})
    return summary
