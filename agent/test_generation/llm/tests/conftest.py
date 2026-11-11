"""Birim testleri için ortak fixture'lar — gerçek ortak girdileri yükler (ağ/anahtar gerekmez)."""
from pathlib import Path

import pytest

from agent.test_generation.llm.loaders import build_endpoint_index, join_cases, load_json

ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture(scope="session")
def cases():
    summary = load_json(ROOT / "experiments/h3_04_rule_based_baseline/endpoint_summary.json")
    gt = load_json(ROOT / "benchmarks/reference_cases/ground_truth.json")
    scen = load_json(ROOT / "benchmarks/drf_fixtures/scenarios/scenarios.json")
    cs, warnings = join_cases(scen, gt, build_endpoint_index(summary))
    assert warnings == [], f"beklenmeyen uyarılar: {warnings}"
    return {c.scenario_id: c for c in cs}
