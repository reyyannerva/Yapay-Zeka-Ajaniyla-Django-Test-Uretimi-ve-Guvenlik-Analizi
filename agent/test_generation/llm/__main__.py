"""CLI — H3-05 / Issue #31.

Depo kökünden:
    python -m agent.test_generation.llm all        # üret + çalıştır + raporla
    python -m agent.test_generation.llm generate   # yalnızca üret
    python -m agent.test_generation.llm run         # mevcut üretilmiş testleri çalıştır + sınıflandır

Girdi yolları ve model parametreleri seçeneklerle veya .env ile değiştirilebilir.
Çıkış kodu: 0 = başarı, 2 = beklenmeyen uygulama uyuşmazlığı (APPLICATION_MISMATCH) var,
3 = girdi/anahtar kullanılamaz.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

from .client import GroqClient, load_env
from .contracts import ExecutionOutcome, GenerationOutcome
from .generator import dump_prompts
from .generator import run as generate_run
from .loaders import build_endpoint_index, join_cases, load_json, sha256
from .reporting import write_reports
from .runner import classify, run_pytest, write_support

ROOT = Path(__file__).resolve().parents[3]
EXP = ROOT / "experiments" / "h3_05_llm_baseline"
DEFAULTS = {
    "endpoints": ROOT / "experiments/h3_04_rule_based_baseline/endpoint_summary.json",
    "ground_truth": ROOT / "benchmarks/reference_cases/ground_truth.json",
    "scenarios": ROOT / "benchmarks/drf_fixtures/scenarios/scenarios.json",
    "out": EXP / "generated_tests",
    "raw": EXP / "raw_responses",
    "reports": EXP / "reports",
    "prompts_sent": EXP / "prompts_sent",
    "env": EXP / ".env",
}


def _parse_args(argv):
    p = argparse.ArgumentParser(prog="agent.test_generation.llm")
    p.add_argument("command", choices=["all", "generate", "run", "prompts"])
    for k, v in DEFAULTS.items():
        p.add_argument(f"--{k.replace('_', '-')}", default=str(v))
    p.add_argument("--model", default=None)
    p.add_argument("--temperature", type=float, default=None)
    p.add_argument("--max-tokens", type=int, default=None)
    p.add_argument("--timeout", type=int, default=None)
    p.add_argument("--only", default=None, help="virgülle ayrılmış senaryo ID'leri")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--inter-delay", type=float, default=None, help="istekler arası bekleme (s); TPM sınırı için")
    p.add_argument("--max-retries", type=int, default=None, help="geçici hatada yeniden deneme sayısı")
    return p.parse_args(argv)


def _load_cases(args):
    summary = load_json(args.endpoints)
    gt = load_json(args.ground_truth)
    scen = load_json(args.scenarios)
    cases, warnings = join_cases(scen, gt, build_endpoint_index(summary))
    if args.only:
        wanted = {s.strip() for s in args.only.split(",")}
        cases = [c for c in cases if c.scenario_id in wanted]
    if args.limit:
        cases = cases[: args.limit]
    inputs_sha = {
        "endpoint_summary.json": sha256(args.endpoints),
        "ground_truth.json": sha256(args.ground_truth),
        "scenarios.json": sha256(args.scenarios),
    }
    return cases, warnings, inputs_sha


def main(argv=None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    load_env(args.env)

    model = args.model or os.environ.get("LLM_MODEL", "groq/openai/gpt-oss-120b")
    temperature = args.temperature if args.temperature is not None else float(os.environ.get("LLM_TEMPERATURE", "0.0"))
    max_tokens = args.max_tokens or int(os.environ.get("LLM_MAX_TOKENS", "1200"))
    timeout = args.timeout or int(os.environ.get("LLM_TIMEOUT", "60"))

    try:
        cases, warnings, inputs_sha = _load_cases(args)
    except FileNotFoundError as exc:
        print(f"HATA: girdi bulunamadı: {exc}")
        return 3
    if not cases:
        print("HATA: işlenecek senaryo yok.")
        return 3

    out_dir, raw_dir, reports_dir = Path(args.out), Path(args.raw), Path(args.reports)
    prompts_dir = Path(args.prompts_sent)

    if args.command == "prompts":
        n = dump_prompts(cases, prompts_dir)
        print(f"{n} istem kaydedildi -> {prompts_dir} (LLM çağrısı yapılmadı)")
        return 0

    client = GroqClient(model=model, temperature=temperature, max_tokens=max_tokens, timeout=timeout)

    if args.command in ("all", "generate"):
        if not os.environ.get(client.api_key_env):
            print(f"HATA: {client.api_key_env} yok. '{args.env}' içine ekleyin "
                  f"(bkz. .env.example). Üretim için canlı anahtar gereklidir.")
            return 3
        print(f"Üretim: {len(cases)} senaryo · model={model} · prompt=pytest_v1")
        gen_kwargs = {}
        if args.inter_delay is not None:
            gen_kwargs["inter_delay"] = args.inter_delay
        if args.max_retries is not None:
            gen_kwargs["max_retries"] = args.max_retries
        generation = generate_run(cases, client, out_dir, raw_dir, model, prompts_dir=prompts_dir, **gen_kwargs)
        gen_counts = {}
        for g in generation:
            gen_counts[g.status] = gen_counts.get(g.status, 0) + 1
        print(f"Üretim durumları: {gen_counts}")
    else:  # run
        gen_file = reports_dir / "generation_report.json"
        if not gen_file.exists():
            print(f"HATA: {gen_file} yok. Önce 'generate' veya 'all' çalıştırın.")
            return 3
        generation = [GenerationOutcome(**{k: r.get(k) for k in GenerationOutcome.__dataclass_fields__})
                      for r in json.loads(gen_file.read_text(encoding="utf-8"))["records"]]

    execution = []
    if args.command in ("all", "run"):
        write_support(out_dir)
        junit = reports_dir / "pytest_junit.xml"
        rc = run_pytest(out_dir, junit)
        execution = classify(cases, generation, junit)
        print(f"Pytest çıkış kodu: {rc}")
    else:
        execution = [ExecutionOutcome(g.scenario_id, "NOT_RUN", None, "yalnızca üretim")
                     for g in generation]

    summary = write_reports(cases, generation, execution, inputs_sha, reports_dir, model, warnings)
    print(f"Raporlar: {reports_dir}")
    print(f"Üretim: {summary['generation']}")
    if execution:
        print(f"Çalıştırma: {summary['execution']}")

    if summary["execution"].get("APPLICATION_MISMATCH", 0) > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
