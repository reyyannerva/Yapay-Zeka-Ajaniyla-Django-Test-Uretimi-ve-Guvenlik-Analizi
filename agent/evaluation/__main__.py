"""H3-06 değerlendirme komut satırı.

    python -m agent.evaluation freeze   # manifesti (yeniden) dondurur — yalnızca bilinçli sürüm değişikliğinde
    python -m agent.evaluation verify   # manifest ↔ veri/artefakt özetleri
    python -m agent.evaluation run      # doğrula + iki baseline'ı aynı hatla değerlendir + raporları yaz
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from . import manifest as mf
from .artifacts import ADAPTERS
from .execution import DEFAULT_TIMEOUT, check_environment, evaluate_baseline
from .metrics import Outcome, compute
from .reporting import environment, write_all


def run(out: Path, timeout: int, baselines: list[str], keep_logs: bool = True) -> int:
    if not mf.MANIFEST.exists():
        print("HATA: manifest yok; önce 'freeze' çalıştırın.", file=sys.stderr)
        return 2
    manifest = mf.load_json(mf.MANIFEST)
    problems = mf.verify(manifest)
    if problems:
        print("HATA: dondurulmuş manifest doğrulanamadı; değerlendirme yapılmadı:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 2
    records = manifest["scenarios"]
    ids = [r["scenario_id"] for r in records]
    env_ok, env_msg = check_environment()
    print(f"Ortam ön kontrolü: {'geçti' if env_ok else 'BAŞARISIZ — ' + env_msg}")
    results: dict[str, list[dict]] = {}
    summary_baselines: dict[str, dict] = {}
    for b in baselines:
        arts = ADAPTERS[b](ids)
        log_dir = out / "results" / b / "logs" if keep_logs else None
        rows = evaluate_baseline(records, arts, log_dir=log_dir, timeout=timeout, env_ok=env_ok)
        results[b] = rows
        m = compute(Outcome(r["scenario_id"], r["http_method"], r["is_known_flaw"], r["outcome"]) for r in rows)
        summary_baselines[b] = {"generator": manifest["baselines"][b]["generator"], "metrics": m}
        print(f"{b}: {m['outcomes']} | TP={m['confusion']['TP']} FP={m['confusion']['FP']} "
              f"TN={m['confusion']['TN']} FN={m['confusion']['FN']} | P={m['precision']['display']} "
              f"R={m['recall']['display']} F1={m['f1']['display']} | çalıştırılabilir="
              f"{m['first_pass_executable']['display']}")
    summary = {
        "report": "H3-06 baseline değerlendirme metrikleri",
        "issue": "#32",
        "evaluator_version": mf.EVALUATOR_VERSION,
        "manifest": {"path": mf.rel(mf.MANIFEST), "version": manifest["manifest_version"],
                     "sha256": hashlib.sha256(mf.canonical_bytes(mf.MANIFEST)).hexdigest()},
        "dataset": {"scenario_count": len(records), "positives": sum(r["is_known_flaw"] for r in records),
                    "scenario_ids": ids, "coverage": manifest["coverage"]},
        "metric_definitions": "benchmarks/reference_cases/split.md §4.3; docs/evaluation/h3-06/methodology.md",
        "environment": environment(),
        "environment_check": {"ok": env_ok, "message": env_msg if not env_ok else "ok"},
        "baselines": summary_baselines,
        "mutation_score": manifest["mutation_score"],
    }
    write_all(out, summary, results)
    print(f"Çıktılar: {mf.rel(out / 'results')}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m agent.evaluation", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("freeze")
    sub.add_parser("verify")
    r = sub.add_parser("run")
    r.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    r.add_argument("--baselines", nargs="+", default=["rule_based", "llm"], choices=sorted(ADAPTERS))
    r.add_argument("--out", type=Path, default=mf.OUT)
    r.add_argument("--no-logs", action="store_true")
    a = p.parse_args(argv)
    if a.cmd == "freeze":
        mf.write()
        print(f"Manifest yazıldı: {mf.rel(mf.MANIFEST)}")
        return 0
    if a.cmd == "verify":
        problems = mf.verify(mf.load_json(mf.MANIFEST))
        for x in problems:
            print(f"  - {x}")
        print("Manifest geçerli." if not problems else "Manifest GEÇERSİZ.")
        return 0 if not problems else 2
    return run(a.out.resolve(), a.timeout, a.baselines, keep_logs=not a.no_logs)


if __name__ == "__main__":
    sys.exit(main())
