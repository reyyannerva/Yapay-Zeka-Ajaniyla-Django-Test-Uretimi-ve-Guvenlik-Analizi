"""Komut satırı — H5-04 / Issue #42.

Depo kökünden:
    python -m experiments.h5_04_generation_experiment freeze   # dev manifestini (yeniden) dondur
    python -m experiments.h5_04_generation_experiment verify   # manifest ↔ veri/artefakt özetleri
    python -m experiments.h5_04_generation_experiment run      # doğrula + iki baseline'ı dev kümesinde
                                                               # değerlendir + results/ yaz

Çıkış kodu: 0 = koşu tamamlandı (ortam yoksa bile sonuçlar dürüstçe yazılır);
2 = manifest yok/geçersiz.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import experiment, manifest, reporting


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m experiments.h5_04_generation_experiment",
                                description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("freeze")
    sub.add_parser("verify")
    r = sub.add_parser("run")
    r.add_argument("--timeout", type=int, default=120)
    r.add_argument("--baselines", nargs="+", default=["rule_based", "llm"],
                   choices=["rule_based", "llm"])
    r.add_argument("--out", type=Path, default=manifest.OUT)
    r.add_argument("--no-logs", action="store_true")
    a = p.parse_args(argv)

    if a.cmd == "freeze":
        manifest.write()
        print(f"Manifest yazıldı: {manifest.MANIFEST}")
        return 0

    if a.cmd == "verify":
        if not manifest.MANIFEST.exists():
            print("HATA: manifest yok; önce 'freeze' çalıştırın.", file=sys.stderr)
            return 2
        problems = manifest.verify(manifest.mf.load_json(manifest.MANIFEST))
        for x in problems:
            print(f"  - {x}")
        print("Manifest geçerli." if not problems else "Manifest GEÇERSİZ.")
        return 0 if not problems else 2

    # run
    out = a.out.resolve()
    try:
        summary = experiment.run_experiment(out=out, timeout=a.timeout, baselines=a.baselines,
                                            keep_logs=not a.no_logs, manifest_path=manifest.MANIFEST)
    except (FileNotFoundError, manifest.mf.IntegrityError) as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 2
    reporting.write_all(out, summary)
    if not summary["environment_check"]["ok"]:
        print("UYARI: hedef uygulama yüklenemedi; sonuçlar ENVIRONMENT_ERROR olarak raporlandı "
              f"({summary['environment_check']['message']}).", file=sys.stderr)
    for b in sorted(summary["metrics"]):
        mt = summary["metrics"][b]
        print(f"{b}: {mt['pytest_summary']} | sözdizimi={mt['syntax_valid']['display']} "
              f"| çalıştırılabilir={mt['first_pass_executable']['display']} | F1={mt['f1']['display']}")
    print(f"Çıktılar: {out / 'results'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
