#!/usr/bin/env bash
# H3-06 demo komutları — depo kök dizininden çalıştırın. Ağ erişimi / API anahtarı gerekmez.
set -euo pipefail
python benchmarks/reference_cases/scripts/check_references.py | tail -1
python -m agent.evaluation verify
python -m agent.evaluation run
sed -n '1,22p' experiments/h3_06_baseline_evaluation/results/comparison.md
tail -5 experiments/h3_06_baseline_evaluation/results/llm/logs/SC-FLW-001/run.log
