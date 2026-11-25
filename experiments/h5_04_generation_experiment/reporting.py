"""Deterministik JSON / CSV / Markdown raporlama — H5-04 / Issue #42.

Çıktılar ``<out>/results/`` altına yazılır: ham sonuçlar (results.json), senaryo düzeyi CSV
(per_scenario.csv), baseline özet CSV'si (metrics.csv) ve okunur karşılaştırma (comparison.md).
Zaman damgası yazılmaz; aynı girdi aynı baytları üretir (tekrarlanabilirlik). 5 metot ve güvenlik
açıkları için mühürlü test kümesi değerlendirmesine (#32) açıkça atıf yapılır.
"""
from __future__ import annotations

import csv
import json
import platform
import sys
from pathlib import Path

PER_SCENARIO_FIELDS = [
    "scenario_id", "baseline", "http_method", "user_role", "secure_status", "outcome",
    "pytest_summary", "syntax_valid", "collected", "collected_count", "exc_type",
    "observed_status", "evidence",
]
METRICS_FIELDS = [
    "baseline", "generator", "scenarios", "syntax_valid", "collected", "first_pass_executable",
    "PASS", "FAIL", "ERROR", "NOT_RUN",
]


def environment() -> dict:
    return {"python": sys.version.split()[0], "implementation": platform.python_implementation(),
            "platform": platform.platform()}


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _results_json(summary: dict) -> dict:
    m = summary["manifest"]
    baselines = {}
    for b, rows in sorted(summary["results"].items()):
        baselines[b] = {
            "generator": m["baselines"].get(b, {}).get("generator"),
            "metrics": summary["metrics"][b],
            "results": sorted(rows, key=lambda r: r["scenario_id"]),
        }
    return {
        "report": "H5-04 dev üretim deneyi sonuçları",
        "issue": "#42",
        "manifest_version": m.get("manifest_version"),
        "dataset": {k: m["dataset"].get(k) for k in ("split", "scenario_count", "scenario_ids")},
        "coverage": m.get("coverage"),
        "environment": environment(),
        "environment_check": summary["environment_check"],
        "cross_reference": m.get("cross_reference"),
        "focus_note": m.get("focus_note"),
        "baselines": baselines,
    }


def _write_per_scenario_csv(path: Path, summary: dict) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=PER_SCENARIO_FIELDS, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for b in sorted(summary["results"]):
            for r in sorted(summary["results"][b], key=lambda r: r["scenario_id"]):
                w.writerow({**r, "baseline": b})


def _write_metrics_csv(path: Path, summary: dict) -> None:
    m = summary["manifest"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=METRICS_FIELDS, lineterminator="\n")
        w.writeheader()
        for b in sorted(summary["metrics"]):
            mt = summary["metrics"][b]
            ps = mt["pytest_summary"]
            w.writerow({
                "baseline": b,
                "generator": m["baselines"].get(b, {}).get("generator"),
                "scenarios": mt["scenarios"],
                "syntax_valid": mt["syntax_valid"]["display"],
                "collected": mt["collected"]["display"],
                "first_pass_executable": mt["first_pass_executable"]["display"],
                "PASS": ps.get("PASS", 0), "FAIL": ps.get("FAIL", 0),
                "ERROR": ps.get("ERROR", 0), "NOT_RUN": ps.get("NOT_RUN", 0),
            })


def _comparison_md(summary: dict) -> str:
    m = summary["manifest"]
    bl = sorted(summary["metrics"])
    hdr = " | ".join(bl)
    lines = [
        "# H5-04 — Dev kümesi üretim deneyi karşılaştırması (otomatik üretilmiştir)",
        "",
        f"Issue #42 · manifest sürüm {m.get('manifest_version')} · dev kümesi "
        f"{m['dataset'].get('scenario_count')} senaryo · ortam yüklendi: "
        f"{summary['environment_check'].get('ok')}.",
        "",
        m.get("focus_note", ""),
        "",
        f"| Metrik | {hdr} |",
        "|---|" + "---|" * len(bl),
    ]

    def line(label, fn):
        return f"| {label} | " + " | ".join(str(fn(summary['metrics'][b])) for b in bl) + " |"

    lines += [
        line("Senaryo", lambda mt: mt["scenarios"]),
        line("Sözdizimi geçerli", lambda mt: f"{mt['syntax_valid']['count']}/{mt['syntax_valid']['of']}"),
        line("Toplanabilir", lambda mt: f"{mt['collected']['count']}/{mt['collected']['of']}"),
        line("İlk geçişte çalıştırılabilir", lambda mt: mt["first_pass_executable"]["display"]),
        line("PASS", lambda mt: mt["pytest_summary"].get("PASS", 0)),
        line("FAIL", lambda mt: mt["pytest_summary"].get("FAIL", 0)),
        line("ERROR (teknik)", lambda mt: mt["pytest_summary"].get("ERROR", 0)),
        line("NOT_RUN", lambda mt: mt["pytest_summary"].get("NOT_RUN", 0)),
        line("Güvenlik F1", lambda mt: mt["f1"]["display"]),
        "",
        "## Senaryo düzeyi sonuçlar",
        "",
        f"| Senaryo | Yöntem | {hdr} |",
        "|---|---|" + "---|" * len(bl),
    ]
    by_sid: dict[str, dict] = {}
    method: dict[str, str] = {}
    for b in bl:
        for r in summary["results"][b]:
            by_sid.setdefault(r["scenario_id"], {})[b] = r["outcome"]
            method[r["scenario_id"]] = r["http_method"]
    for sid in sorted(by_sid):
        cells = " | ".join(by_sid[sid].get(b, "-") for b in bl)
        lines.append(f"| {sid} | {method[sid]} | {cells} |")

    cov = m.get("coverage", {})
    bm = cov.get("by_method", {})
    lines += [
        "",
        "## HTTP yöntemi kapsamı (dev kümesi)",
        "",
        "| Yöntem | Dev senaryo sayısı |",
        "|---|---|",
    ]
    for meth in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        lines.append(f"| {meth} | {bm.get(meth, 0)} |")
    cr = m.get("cross_reference", {})
    lines += [
        "",
        "## 5 metot ve güvenlik açıkları için: mühürlü test kümesi (#32)",
        "",
        f"Dev kümesinde eksik metot(lar): {', '.join(cov.get('missing_methods', [])) or 'yok'}. "
        f"{cr.get('note', '')} Bkz. `{cr.get('evaluation', '')}` (#32 / H3-06).",
        "",
    ]
    return "\n".join(lines).rstrip("\n") + "\n"


def write_all(out: Path, summary: dict) -> None:
    results_dir = out / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    _write_json(results_dir / "results.json", _results_json(summary))
    _write_per_scenario_csv(results_dir / "per_scenario.csv", summary)
    _write_metrics_csv(results_dir / "metrics.csv", summary)
    (results_dir / "comparison.md").write_text(_comparison_md(summary), encoding="utf-8", newline="\n")
