"""Değerlendirme çıktıları (JSON, CSV, Markdown) — H3-06 / Issue #32.

Sonuç dosyaları deterministiktir: zaman damgası, süre veya geçici yol içermez; aynı girdilerle yeniden
çalıştırma bayt düzeyinde aynı ``results.json`` / ``metrics.json`` / CSV dosyalarını üretir.
"""
from __future__ import annotations

import csv
import io
import json
import platform
from importlib import metadata
from pathlib import Path

from .metrics import NOT_MEASURABLE

BASELINE_NAMES = {"rule_based": "Baseline A — kural tabanlı (H3-04)", "llm": "Baseline B — LLM (H3-05)"}
CSV_FIELDS = ("baseline", "scenario_id", "http_method", "user_role", "secure_status", "is_known_flaw",
              "deviation_kind", "syntax_valid", "collected", "outcome", "pytest_summary", "confusion_cell",
              "observed_status", "exc_type", "artifact_origin", "artifact_sha256", "evidence")
METRIC_FIELDS = ("baseline", "scenarios", "positives", "negatives", "TP", "FP", "TN", "FN", "EXCLUDED",
                 "syntax_valid", "collected", "first_pass_executable", "precision", "recall", "f1",
                 "f1_gte_0_80", "first_pass_executable_gte_0_70")


def environment() -> dict:
    def ver(pkg: str) -> str:
        try:
            return metadata.version(pkg)
        except metadata.PackageNotFoundError:
            return "yüklü değil"
    return {"python": platform.python_version(), "implementation": platform.python_implementation(),
            "os": platform.system(),
            **{p: ver(p) for p in ("Django", "djangorestframework", "pytest", "pytest-django")}}


def _dump(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _csv(rows: list[dict], fields: tuple[str, ...]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})
    return buf.getvalue()


def _target(v: bool | None) -> str:
    return NOT_MEASURABLE if v is None else ("Karşılandı" if v else "Karşılanmadı")


def metric_row(name: str, m: dict) -> dict:
    c = m["confusion"]
    return {"baseline": name, "scenarios": m["scenarios"], "positives": m["positives"], "negatives": m["negatives"],
            **{k: c[k] for k in ("TP", "FP", "TN", "FN", "EXCLUDED")},
            "syntax_valid": f"{m['syntax_valid']['count']}/{m['syntax_valid']['of']}",
            "collected": f"{m['collected']['count']}/{m['collected']['of']}",
            "first_pass_executable": m["first_pass_executable"]["display"],
            "precision": m["precision"]["display"], "recall": m["recall"]["display"], "f1": m["f1"]["display"],
            "f1_gte_0_80": _target(m["targets"]["f1_gte_0_80"]),
            "first_pass_executable_gte_0_70": _target(m["targets"]["first_pass_executable_gte_0_70"])}


def markdown(summary: dict, results: dict[str, list[dict]]) -> str:
    L = ["# H3-06 — Baseline karşılaştırma sonuçları (otomatik üretilmiştir)", "",
         f"Manifest: `{summary['manifest']['path']}` (sürüm {summary['manifest']['version']}, SHA-256 "
         f"`{summary['manifest']['sha256'][:16]}…`); test kümesi {summary['dataset']['scenario_count']} senaryo, "
         f"{summary['dataset']['positives']} bilinen kusur.", "",
         "| Metrik | " + " | ".join(BASELINE_NAMES[b] for b in summary["baselines"]) + " |",
         "|---|" + "---|" * len(summary["baselines"])]
    rows = [metric_row(b, summary["baselines"][b]["metrics"]) for b in summary["baselines"]]
    labels = [("Sözdizimi geçerli", "syntax_valid"), ("Pytest toplama", "collected"),
              ("İlk geçişte çalıştırılabilir", "first_pass_executable"), ("TP", "TP"), ("FP", "FP"),
              ("TN", "TN"), ("FN", "FN"), ("Matris dışı (teknik hata, kusursuz)", "EXCLUDED"),
              ("Precision", "precision"), ("Recall", "recall"), ("F1", "f1"),
              ("Hedef F1 ≥ 0.80", "f1_gte_0_80"), ("Hedef çalıştırılabilirlik ≥ %70", "first_pass_executable_gte_0_70")]
    for label, key in labels:
        L.append(f"| {label} | " + " | ".join(str(r[key]) for r in rows) + " |")
    L += ["", "## Senaryo düzeyi sonuçlar", "",
          "| Senaryo | Yöntem | Güvenli beklenti | Kusur | " + " | ".join(BASELINE_NAMES[b] for b in results) + " |",
          "|---|---|---|---|" + "---|" * len(results)]
    by = {b: {r["scenario_id"]: r for r in rs} for b, rs in results.items()}
    for sid in summary["dataset"]["scenario_ids"]:
        first = next(iter(by.values()))[sid]
        cells = []
        for b in results:
            r = by[b][sid]
            obs = f", gözlenen {r['observed_status']}" if r.get("observed_status") is not None else ""
            cells.append(f"{r['outcome']} → {r['confusion_cell']}{obs}")
        flaw = f"evet ({first['deviation_kind']})" if first["is_known_flaw"] else "hayır"
        L.append(f"| {sid} | {first['http_method']} | {first['secure_status']} | {flaw} | " + " | ".join(cells) + " |")
    L += ["", "## HTTP yöntemi kapsamı", "", "| Yöntem | Test kümesinde | " +
          " | ".join(f"{BASELINE_NAMES[b]} çalıştırılabilir" for b in results) + " |",
          "|---|---|" + "---|" * len(results)]
    for method, n in summary["dataset"]["coverage"]["by_method"].items():
        cells = []
        for b in results:
            if n == 0:
                cells.append("Kapsam dışı (test kümesinde yok)")
            else:
                bm = summary["baselines"][b]["metrics"]["by_method"].get(method, {})
                cells.append(f"{bm.get('PASS', 0) + bm.get('FAIL', 0)}/{n}")
        L.append(f"| {method} | {n} | " + " | ".join(cells) + " |")
    L += ["", f"Mutasyon skoru: **{summary['mutation_score']}**.", ""]
    return "\n".join(L)


def write_all(out: Path, summary: dict, results: dict[str, list[dict]]) -> None:
    for b, rows in results.items():
        _dump(out / "results" / b / "results.json", {"baseline": b, "name": BASELINE_NAMES[b], "results": rows})
    all_rows = [{"baseline": b, **r} for b, rs in results.items() for r in rs]
    (out / "results" / "per_scenario.csv").write_text(_csv(all_rows, CSV_FIELDS), encoding="utf-8", newline="")
    _dump(out / "results" / "metrics.json", summary)
    rows = [metric_row(b, summary["baselines"][b]["metrics"]) for b in summary["baselines"]]
    (out / "results" / "metrics.csv").write_text(_csv(rows, METRIC_FIELDS), encoding="utf-8", newline="")
    (out / "results" / "comparison.md").write_text(markdown(summary, results), encoding="utf-8", newline="\n")
