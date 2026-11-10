"""Üretim ve çalıştırma raporları (JSON + Markdown) — H3-04 / Issue #30.

Raporlar deterministiktir: zaman damgası, süre veya mutlak yol içermez.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .contracts import SUPPORTED_METHODS, SUPPORTED_STATUSES, Severity, Status
from .generator import GenerationResult
from .runner import CLASS_LABELS, TestResult

STATUS_LABELS = {
    "GENERATED": "Üretildi",
    "UNSUPPORTED": "Desteklenmiyor",
    "INVALID_INPUT": "Geçersiz girdi",
    "MISSING_REFERENCE": "Referans eksik",
    "GENERATION_ERROR": "Üretim hatası",
}


def _cell(v) -> str:
    return "—" if v is None or v == "" else str(v).replace("|", "\\|").replace("\n", " ")


def table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(_cell(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8",
                    newline="\n")


def generation_report(result: GenerationResult, inputs: dict[str, str], files: dict[str, str],
                      summary_meta: dict, regeneration_identical: bool) -> dict:
    plans = result.plans
    return {
        "report": "H3-04 kural tabanlı Pytest üretim raporu",
        "generator": summary_meta["generator"],
        "llm_used": False,
        "endpoint_summary_source": summary_meta["source"],
        "inputs_sha256": inputs,
        "status_counts": result.counts(),
        "generated_by_method": {m: sum(1 for p in plans if p.http_method == m) for m in SUPPORTED_METHODS},
        "generated_by_expected_status": {str(s): sum(1 for p in plans if p.expected_status == s)
                                         for s in sorted(SUPPORTED_STATUSES)},
        "generated_by_role": dict(sorted(Counter(p.user_role for p in plans).items())),
        "generated_by_side_effect_rule": dict(sorted(Counter(p.side_effect_check for p in plans).items())),
        "regeneration_identical": regeneration_identical,
        "generated_files_sha256": files,
        "global_diagnostics": [d.to_dict() for d in result.global_diagnostics],
        "scenarios": [o.to_dict() for o in result.outcomes],
    }


def generation_markdown(rep: dict, plans) -> str:
    w: list[str] = []
    a = w.append
    a("# H3-04 | Kural Tabanlı Pytest Üretim Raporu")
    a("")
    a("> Otomatik üretilmiştir (`python -m agent.test_generation.rule_based all`). LLM kullanılmamıştır. "
      "Beklenen durum kodları `ground_truth.json` → `secure_status` alanından alınmıştır.")
    a("")
    src = rep["endpoint_summary_source"]
    a(f"- Endpoint özeti kaynağı: `{src['kind']}` (AST entegrasyonu: {'var' if src['ast_integration'] else 'yok'}).")
    a(f"- Yeniden üretim sonucu birebir aynı: **{'evet' if rep['regeneration_identical'] else 'HAYIR'}**.")
    a("")
    a("## Senaryo durumları")
    a("")
    a(table(["Durum", "Açıklama", "Senaryo"], [[k, STATUS_LABELS[k], v] for k, v in rep["status_counts"].items()]))
    a("")
    a("## Üretilen testlerin dağılımı")
    a("")
    a(table(["HTTP metodu", "Test"], [[k, v] for k, v in rep["generated_by_method"].items()]))
    a("")
    a(table(["Beklenen durum kodu (referans)", "Test"], [[k, v] for k, v in rep["generated_by_expected_status"].items()]))
    a("")
    a(table(["Rol", "Test"], [[k, v] for k, v in rep["generated_by_role"].items()]))
    a("")
    a(table(["Yan etki kuralı", "Test"], [[k, v] for k, v in rep["generated_by_side_effect_rule"].items()]))
    a("")
    a("## Senaryo → test izlenebilirliği")
    a("")
    by_sid = {p.scenario_id: p for p in plans}
    rows = []
    for s in rep["scenarios"]:
        p = by_sid.get(s["scenario_id"])
        rows.append([s["scenario_id"], s["status"], s["http_method"], p.path if p else None,
                     f"{p.user_role} ({p.username or 'anonim'})" if p else None, s["expected_status"],
                     p.side_effect_check if p else None, f"{s['module']}::{s['test_name']}" if s["test_name"] else None])
    a(table(["Senaryo", "Durum", "Metot", "Endpoint", "Rol (fixture)", "Beklenen", "Yan etki", "Test"], rows))
    a("")
    diags = [(s["scenario_id"], d) for s in rep["scenarios"] for d in s["diagnostics"]]
    diags += [(None, d) for d in rep["global_diagnostics"]]
    a("## Tanılar (uyarılar ve hatalar)")
    a("")
    if diags:
        a(table(["Senaryo", "Kod", "Önem", "İleti", "Ayrıntı"],
                [[sid, d["code"], d["severity"], d["message"], d["detail"]] for sid, d in diags]))
    else:
        a("Tanı yok.")
    a("")
    a("## Üretilen dosyalar (SHA-256)")
    a("")
    a(table(["Dosya", "SHA-256"], [[k, v] for k, v in rep["generated_files_sha256"].items()]))
    a("")
    a("## Girdiler (SHA-256)")
    a("")
    a(table(["Girdi", "SHA-256"], [[k, v] for k, v in rep["inputs_sha256"].items()]))
    a("")
    return "\n".join(w)


def execution_report(results: list[TestResult], collected: int, planned: int, isolation: dict | None,
                     inputs_unchanged: bool, pytest_returncode: int) -> dict:
    cls = Counter(r.classification for r in results)
    out = Counter(r.pytest_outcome for r in results)
    by_method = {}
    for m in SUPPORTED_METHODS:
        rs = [r for r in results if r.http_method == m]
        by_method[m] = {"tests": len(rs), "passed": sum(r.pytest_outcome == "passed" for r in rs),
                        "failed": sum(r.pytest_outcome == "failed" for r in rs),
                        "generation_errors": sum(r.classification == "GENERATION_ERROR" for r in rs)}
    by_status = {}
    for s in sorted(SUPPORTED_STATUSES):
        rs = [r for r in results if r.expected_status == s]
        by_status[str(s)] = {"tests": len(rs), "passed": sum(r.pytest_outcome == "passed" for r in rs)}
    return {
        "report": "H3-04 üretilen testlerin kontrollü fixture üzerinde çalıştırma raporu",
        "planned_tests": planned,
        "collected_tests": collected,
        "pytest_returncode": pytest_returncode,
        "pytest_outcomes": dict(sorted(out.items())),
        "classifications": {k: cls.get(k, 0) for k in CLASS_LABELS},
        "by_method": by_method,
        "by_expected_status": by_status,
        "isolation": isolation,
        "inputs_unchanged_after_run": inputs_unchanged,
        "results": [r.to_dict() for r in results],
    }


def execution_markdown(rep: dict) -> str:
    w: list[str] = []
    a = w.append
    a("# H3-04 | Üretilen Testlerin Çalıştırma Raporu")
    a("")
    a("> Otomatik üretilmiştir. Pytest sonucu (passed/failed) olduğu gibi korunur; sınıflandırma ayrı bir "
      "alandır. Bilinen güvenlik kusurunu tespit eden test **başarısız** olarak kalır.")
    a("")
    a(f"- Planlanan test: **{rep['planned_tests']}**, pytest'in topladığı: **{rep['collected_tests']}**, "
      f"pytest çıkış kodu: `{rep['pytest_returncode']}` (kusur tespit eden başarısız testler nedeniyle 0 olmayabilir).")
    a(f"- Pytest sonuçları: " + ", ".join(f"{k}={v}" for k, v in rep["pytest_outcomes"].items()) + ".")
    iso = rep["isolation"]
    if iso:
        a(f"- Yalıtım: {iso['tests']} testin her biri tek başına ve paket ters sırayla çalıştırıldı; fark: "
          f"tek başına {len(iso['single_run_differences'])}, ters sıra {len(iso['reversed_order_differences'])} "
          f"→ **{'yalıtılmış' if iso['isolated'] else 'BAĞIMLILIK VAR'}**.")
    a(f"- Girdi dosyaları çalıştırma sonrası değişmedi: **{'evet' if rep['inputs_unchanged_after_run'] else 'HAYIR'}**.")
    a("")
    a("## Sınıflandırma")
    a("")
    a(table(["Sınıf", "Anlam", "Test"], [[k, CLASS_LABELS[k], v] for k, v in rep["classifications"].items()]))
    a("")
    a("## Metot bazında")
    a("")
    a(table(["Metot", "Test", "Geçti", "Başarısız", "Üretim hatası"],
            [[m, d["tests"], d["passed"], d["failed"], d["generation_errors"]] for m, d in rep["by_method"].items()]))
    a("")
    a("## Beklenen durum kodu bazında (destek ≠ kanıt: 0 test = kanıt yok)")
    a("")
    a(table(["Beklenen kod", "Test", "Geçti"], [[s, d["tests"], d["passed"]] for s, d in rep["by_expected_status"].items()]))
    a("")
    a("## Test sonuçları")
    a("")
    a(table(["Senaryo", "Test", "Metot", "Beklenen", "Gözlenen", "Pytest", "Sınıf", "Kanıt"],
            [[r["scenario_id"], r["test_name"], r["http_method"], r["expected_status"], r["observed_status"],
              r["pytest_outcome"], r["classification"], r["evidence"]] for r in rep["results"]]))
    a("")
    return "\n".join(w)


def severity_errors(result: GenerationResult) -> int:
    return sum(1 for o in result.outcomes for d in o.diagnostics if d.severity is Severity.ERROR) + \
        sum(1 for d in result.global_diagnostics if d.severity is Severity.ERROR)


def status_of(result: GenerationResult, sid: str) -> Status | None:
    return next((o.status for o in result.outcomes if o.scenario_id == sid), None)
