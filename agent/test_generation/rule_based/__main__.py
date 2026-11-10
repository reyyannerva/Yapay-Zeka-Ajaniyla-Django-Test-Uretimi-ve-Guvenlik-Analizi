"""Komut satırı: ``python -m agent.test_generation.rule_based {generate,all,examples}`` — H3-04 / Issue #30.

Varsayılan yollar depo içindeki gerçek girdileri gösterir; tüm yollar depo köküne görelidir.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from . import codegen, examples, reporting, runner
from .generator import GenerationResult, generate, relative_pythonpath, sha256, write_output
from .loaders import InputError, load_endpoint_summary, load_fixture_records, load_references

REPO_ROOT = Path(__file__).resolve().parents[3]
EXP = Path("experiments/h3_04_rule_based_baseline")
DEFAULTS = {
    "endpoints": EXP / "endpoint_summary.json",
    "ground_truth": Path("benchmarks/reference_cases/ground_truth.json"),
    "ground_truth_schema": Path("benchmarks/reference_cases/ground_truth.schema.json"),
    "scenarios": Path("benchmarks/drf_fixtures/scenarios/scenarios.json"),
    "scenarios_schema": Path("benchmarks/drf_fixtures/scenarios/scenarios.schema.json"),
    "out": EXP / "generated_tests",
    "reports": EXP / "reports",
    "examples": EXP / "examples" / "unsupported_cases.json",
}


def _abs(p: Path) -> Path:
    return p if p.is_absolute() else REPO_ROOT / p


def _rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return p.name


def build(args) -> tuple[GenerationResult, dict[str, str], dict, Path]:
    summary = load_endpoint_summary(_abs(args.endpoints))
    cases, join_diags = load_references(_abs(args.ground_truth), _abs(args.ground_truth_schema),
                                        _abs(args.scenarios), _abs(args.scenarios_schema))
    users = load_fixture_records(_abs(Path(summary.users_fixture)))
    resources = load_fixture_records(_abs(Path(summary.resources_fixture)))
    input_paths = [args.endpoints, args.ground_truth, args.ground_truth_schema, args.scenarios,
                   args.scenarios_schema, Path(summary.users_fixture), Path(summary.resources_fixture)]
    digests = {_rel(_abs(p)): sha256(_abs(p)) for p in input_paths}
    out_dir = _abs(args.out)
    pythonpath = relative_pythonpath(out_dir, _abs(Path(summary.target_app)))
    result = generate(cases, summary, users, resources, digests, join_diags, pythonpath)
    again = generate(cases, summary, users, resources, digests, join_diags, pythonpath)
    identical = (result.modules == again.modules and result.support_files == again.support_files
                 and [o.to_dict() for o in result.outcomes] == [o.to_dict() for o in again.outcomes])
    meta = {"generator": f"{codegen.GENERATOR_ID} v{codegen.GENERATOR_VERSION}",
            "source": {"kind": summary.source_kind, "ast_integration": summary.ast_integration},
            "identical": identical}
    return result, digests, meta, out_dir


def cmd_generate(args) -> tuple[GenerationResult, dict, Path]:
    result, digests, meta, out_dir = build(args)
    written = write_output(result, out_dir)
    files = {_rel(p): sha256(p) for p in written}
    rep = reporting.generation_report(result, digests, files, meta, meta["identical"])
    reports = _abs(args.reports)
    reporting.write_json(reports / "generation_report.json", rep)
    (reports / "generation_report.md").write_text(reporting.generation_markdown(rep, result.plans), encoding="utf-8",
                                                  newline="\n")
    c = rep["status_counts"]
    print(f"Üretim: {c} · dosya: {len(written)} · yeniden üretim aynı: {meta['identical']}")
    return result, digests, out_dir


def cmd_run(args, result: GenerationResult, digests: dict[str, str], out_dir: Path) -> int:
    env_ok, env_msg = runner.check_environment(out_dir)
    nodes, collect_out = runner.collect(out_dir)
    with tempfile.TemporaryDirectory() as tmp:
        raw, out, code = runner.run(out_dir, Path(tmp) / "suite.xml")
        iso = (runner.isolation_check(out_dir, result.plans, raw, Path(tmp))
               if args.isolation and env_ok else None)
    results = runner.classify_all(result.plans, raw, None if env_ok else env_msg)
    if not env_ok:
        print(f"ORTAM HATASI: hedef uygulama yüklenemedi: {env_msg}", file=sys.stderr)
    unchanged = all(sha256(REPO_ROOT / p) == d for p, d in digests.items())
    rep = reporting.execution_report(results, len(nodes), len(result.plans), iso, unchanged, code)
    reports = _abs(args.reports)
    reporting.write_json(reports / "execution_report.json", rep)
    (reports / "execution_report.md").write_text(reporting.execution_markdown(rep), encoding="utf-8", newline="\n")
    print(f"Toplanan: {len(nodes)}/{len(result.plans)} · pytest: {rep['pytest_outcomes']} · "
          f"sınıflar: {rep['classifications']}" + (f" · yalıtım: {iso['isolated']}" if iso else ""))
    gen_errors = (rep["classifications"]["GENERATION_ERROR"] + rep["classifications"]["APPLICATION_MISMATCH"]
                  + rep["classifications"]["ENVIRONMENT_ERROR"])
    if len(nodes) != len(result.plans):
        print("HATA: toplanan test sayısı planlanan sayıdan farklı.\n" + collect_out[-2000:], file=sys.stderr)
        return 2
    return 1 if gen_errors else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m agent.test_generation.rule_based",
                                 description="LLM kullanmayan kural tabanlı Pytest üretim baseline'ı (H3-04).")
    ap.add_argument("command", choices=["generate", "all", "examples"])
    for k, v in DEFAULTS.items():
        ap.add_argument(f"--{k.replace('_', '-')}", dest=k, type=Path, default=v)
    ap.add_argument("--no-isolation", dest="isolation", action="store_false",
                    help="Tek tek ve ters sıra yalıtım kontrolünü atla")
    args = ap.parse_args(argv)
    try:
        if args.command == "examples":
            rep = examples.run_examples(_abs(args.examples), _abs(args.endpoints), REPO_ROOT)
            reporting.write_json(_abs(args.reports) / "unsupported_examples_report.json", rep)
            (_abs(args.reports) / "unsupported_examples_report.md").write_text(
                examples.markdown(rep), encoding="utf-8", newline="\n")
            print(f"Örnekler: {rep['total']} · beklenenle uyumlu: {rep['matched']}")
            return 0 if rep["matched"] == rep["total"] else 1
        result, digests, out_dir = cmd_generate(args)
        if args.command == "generate":
            return 0
        return cmd_run(args, result, digests, out_dir)
    except InputError as exc:
        for d in exc.diagnostics:
            print(f"{d.code.value}: {d.message} {d.detail}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
