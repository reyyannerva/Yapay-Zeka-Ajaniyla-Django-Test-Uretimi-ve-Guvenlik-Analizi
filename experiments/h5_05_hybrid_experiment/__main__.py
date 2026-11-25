"""CLI: ``python -m experiments.h5_05_hybrid_experiment {prepare|run|verify}`` — H5-05 / Issue #43."""
from __future__ import annotations

import argparse
import sys

from agent.evaluation import manifest as mf

from . import config as C
from . import layer_b_inputs, reporting, runner


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m experiments.h5_05_hybrid_experiment")
    ap.add_argument("command", choices=["prepare", "run", "verify"])
    ap.add_argument("--layer", choices=["A", "B", "all"], default="all")
    ap.add_argument("--resume", action="store_true", help="artefakt özeti aynı kontrol noktalarını yeniden kullan")
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args(argv)
    if args.command == "verify":
        problems = layer_b_inputs.verify_frozen()
        print("Katman B dondurma: " + ("OK" if not problems else "; ".join(problems)))
        return 1 if problems else 0
    if args.command == "prepare":
        print(layer_b_inputs.prepare())
        return 0
    layers = C.LAYERS if args.layer == "all" else (args.layer,)
    runs = {name: runner.run_layer(name, C.RESULTS, args.timeout, args.resume) for name in layers}
    config = {"experiment_id": C.EXPERIMENT_ID, "version": C.EXPERIMENT_VERSION, "layers": list(layers),
              "methods": list(C.METHODS), "timeout_s": args.timeout, "planned_model": C.PLANNED_MODEL,
              "llm_provider": C.LLM_PROVIDER, "llm_temperature": mf.LLM_TEMPERATURE,
              "hybrid_generator": f"{C.HYBRID_GENERATOR_ID} v{C.HYBRID_VERSION}",
              "llm_status_by_layer": {n: r["layer"]["llm"]["status"] for n, r in runs.items()},
              "actual_model_by_layer": {n: r["layer"]["llm"]["model_id"] for n, r in runs.items()},
              "layer_b_generator_inputs_sha256": layer_b_inputs.prepare() if "B" in layers else None}
    summary = reporting.write_all(runs, C.RESULTS, runner.environment_info(), config)
    for name, info in summary["layers"].items():
        for m, mm in info["methods"].items():
            print(f"[{name}] {m:10s} F1={mm['f1']['display']:10s} ilk-geçiş={mm['first_pass_executable']['count']}/"
                  f"{mm['first_pass_executable']['of']} hedef={mm['target_status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
