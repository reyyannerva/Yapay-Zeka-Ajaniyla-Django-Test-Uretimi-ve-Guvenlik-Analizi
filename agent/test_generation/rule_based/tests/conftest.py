"""Üretici testlerinin ortak fixture'ları — H3-04 / Issue #30.

Gerçek girdiler (endpoint özeti, ground truth, senaryolar, fixture'lar) salt okunur kullanılır.
Sentetik kayıtlar yalnızca bu testlerin içinde, kopyalar üzerinde oluşturulur.
"""
from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

from agent.test_generation.rule_based.loaders import (
    load_endpoint_summary,
    load_fixture_records,
    load_references,
    parse_endpoint_summary,
)

REPO = Path(__file__).resolve().parents[4]
EXP = REPO / "experiments" / "h3_04_rule_based_baseline"
ENDPOINTS = EXP / "endpoint_summary.json"
GT = REPO / "benchmarks" / "reference_cases" / "ground_truth.json"
GT_SCHEMA = REPO / "benchmarks" / "reference_cases" / "ground_truth.schema.json"
SCEN = REPO / "benchmarks" / "drf_fixtures" / "scenarios" / "scenarios.json"
SCEN_SCHEMA = REPO / "benchmarks" / "drf_fixtures" / "scenarios" / "scenarios.schema.json"
TARGET_APP = REPO / "benchmarks" / "drf_fixtures" / "sample_app"


@pytest.fixture(scope="session")
def target_app(tmp_path_factory) -> Path:
    """Hedef uygulamanın (sample_app) geçici dizindeki salt kopyası.

    Üretilen paketler aynı geçici kök altında oluşturulur; böylece pytest.ini'ye yazılan göreli yol her zaman
    kısa ve güvenlidir (``../target_app`` gibi). Depo, boşluk içeren bir yolda veya geçici dizinden farklı bir
    Windows sürücüsünde olsa bile testler çalışır. Kaynak ağaca hiçbir şey yazılmaz.
    """
    app = tmp_path_factory.mktemp("target_app", numbered=False)
    shutil.copytree(TARGET_APP, app, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.sqlite3"))
    return app


@pytest.fixture(scope="session")
def summary_dict():
    return json.loads(ENDPOINTS.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def summary():
    return load_endpoint_summary(ENDPOINTS)


@pytest.fixture(scope="session")
def references():
    return load_references(GT, GT_SCHEMA, SCEN, SCEN_SCHEMA)


@pytest.fixture(scope="session")
def cases(references):
    return {c.scenario_id: c for c in references[0]}


@pytest.fixture(scope="session")
def users(summary):
    return load_fixture_records(REPO / summary.users_fixture)


@pytest.fixture(scope="session")
def resources(summary):
    return load_fixture_records(REPO / summary.resources_fixture)


@pytest.fixture(scope="session")
def raw_gt():
    return json.loads(GT.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def raw_scen():
    return json.loads(SCEN.read_text(encoding="utf-8"))


@pytest.fixture
def summary_copy(summary_dict):
    return copy.deepcopy(summary_dict)


def reparse(d):
    return parse_endpoint_summary(d)
