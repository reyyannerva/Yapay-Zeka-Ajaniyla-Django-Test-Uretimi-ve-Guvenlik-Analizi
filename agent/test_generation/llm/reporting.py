"""Üretim ve çalıştırma raporları — H3-05 / Issue #31. H3-04 ile karşılaştırılabilir yapı."""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from . import PROMPT_VERSION, VERSION
from .contracts import Case, ExecutionOutcome, GenerationOutcome

GEN_STATUSES = ["GENERATED", "INVALID_SYNTAX", "EMPTY_OUTPUT", "LLM_ERROR"]
EXEC_CLASSES = ["PASSED", "KNOWN_FLAW_DETECTED", "KNOWN_FLAW_NOT_DETECTED",
                "APPLICATION_MISMATCH", "GENERATION_ERROR", "NOT_RUN"]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def _table(title: str, rows: list[tuple[str, object]]) -> str:
    out = [f"| {title} | Adet |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in rows]
    return "\n".join(out)


def write_reports(cases: list[Case], generation: list[GenerationOutcome],
                  execution: list[ExecutionOutcome], inputs_sha: dict[str, str],
                  reports_dir: Path, model: str, warnings: list[str]) -> dict:
    gen_counts = Counter(g.status for g in generation)
    method_counts = Counter(g.http_method for g in generation if g.status == "GENERATED")
    exec_counts = Counter(e.classification for e in execution)
    pt = sum(g.prompt_tokens or 0 for g in generation)
    ct = sum(g.completion_tokens or 0 for g in generation)
    lat = [g.latency_ms for g in generation if g.latency_ms is not None]

    summary = {
        "generator": "agent.test_generation.llm",
        "version": VERSION,
        "prompt_version": PROMPT_VERSION,
        "model": model,
        "scenario_count": len(generation),
        "generation": {s: gen_counts.get(s, 0) for s in GEN_STATUSES},
        "execution": {c: exec_counts.get(c, 0) for c in EXEC_CLASSES},
        "tokens": {"prompt": pt, "completion": ct, "total": pt + ct},
        "latency_ms": {"total": sum(lat), "avg": (sum(lat) // len(lat)) if lat else 0,
                        "max": max(lat) if lat else 0},
        "input_sha256": inputs_sha,
        "warnings": warnings,
    }

    # --- JSON ---
    _write(reports_dir / "generation_report.json", json.dumps(
        {"summary": summary, "records": [asdict(g) for g in generation]},
        ensure_ascii=False, indent=2))
    _write(reports_dir / "execution_report.json", json.dumps(
        {"summary": {"model": model, "execution": summary["execution"]},
         "records": [asdict(e) for e in execution]}, ensure_ascii=False, indent=2))

    # --- generation_report.md ---
    g_md = [
        "# H3-05 | LLM Tabanlı Pytest Üretim Raporu",
        "",
        f"> Üretici: `agent.test_generation.llm` v{VERSION} · Prompt: `{PROMPT_VERSION}` · Model: `{model}`.",
        "> Beklenen durum kodları bağımsız referanstan (`ground_truth.json` → `secure_status`) alınmıştır.",
        "> Cevap anahtarı meta (is_known_flaw, gözlenen kod, dev/test ayrımı) prompt'a konulmamıştır.",
        "",
        "## Üretim durumları",
        _table("Durum", [(s, gen_counts.get(s, 0)) for s in GEN_STATUSES]),
        "",
        "## Üretilen testlerin metot dağılımı (GENERATED)",
        _table("HTTP metodu", [(m, method_counts.get(m, 0)) for m in ["GET", "POST", "PUT", "PATCH", "DELETE"]]),
        "",
        "## Kaynak tüketimi (İST-12)",
        _table("Ölçüt", [("Prompt token", pt), ("Completion token", ct), ("Toplam token", pt + ct),
                          ("Toplam süre (ms)", summary["latency_ms"]["total"]),
                          ("Ortalama süre (ms)", summary["latency_ms"]["avg"])]),
        "",
        "## Senaryo → üretim izlenebilirliği",
        "| Senaryo | Durum | Metot | Token (p/c) | Süre (ms) | Not |",
        "|---|---|---|---|---|---|",
    ]
    for g in generation:
        note = g.error or g.syntax_error or ""
        g_md.append(f"| {g.scenario_id} | {g.status} | {g.http_method} | "
                    f"{g.prompt_tokens or '-'}/{g.completion_tokens or '-'} | {g.latency_ms or '-'} | {note} |")
    if warnings:
        g_md += ["", "## Uyarılar"] + [f"- {w}" for w in warnings]
    _write(reports_dir / "generation_report.md", "\n".join(g_md))

    # --- execution_report.md ---
    e_md = [
        "# H3-05 | LLM Üretilmiş Testlerin Çalıştırma Raporu",
        "",
        f"> Kontrollü fixture ortamında (`benchmarks/drf_fixtures/sample_app`) çalıştırıldı. Model: `{model}`.",
        "> Sınıflandırma H3-04 ile uyumludur. Bilinen kusuru tespit eden başarısız testler beklenen sonuçtur.",
        "",
        "## Sınıflandırma",
        _table("Sınıf", [(c, exec_counts.get(c, 0)) for c in EXEC_CLASSES]),
        "",
        "## Senaryo → sonuç",
        "| Senaryo | Sınıf | Pytest | Açıklama |",
        "|---|---|---|---|",
    ]
    for e in execution:
        e_md.append(f"| {e.scenario_id} | {e.classification} | {e.pytest_outcome or '-'} | {e.detail} |")
    _write(reports_dir / "execution_report.md", "\n".join(e_md))

    return summary
