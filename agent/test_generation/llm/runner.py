"""Üretilen testleri yazma, çalıştırma ve sınıflandırma — H3-05 / Issue #31.

Çalıştırma ortamı kontrollü fixture uygulamasıdır (`benchmarks/drf_fixtures/sample_app`).
Sınıflandırma, H3-04 taksonomisiyle uyumludur: PASSED, KNOWN_FLAW_DETECTED,
KNOWN_FLAW_NOT_DETECTED, APPLICATION_MISMATCH, GENERATION_ERROR.
"""
from __future__ import annotations

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from .contracts import Case, ExecutionOutcome, GenerationOutcome
from .prompt import test_name

CONFTEST = '''\
"""Üretilen testlerin ortak fixture'ları — H3-05 / Issue #31."""
import pytest
from django.core.management import call_command
from rest_framework.test import APIClient


@pytest.fixture
def seeded_db(db):
    call_command("loaddata", "users", "articles", verbosity=0)


@pytest.fixture
def api_client():
    return APIClient()
'''

PYTEST_INI = """\
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
pythonpath = ../../../benchmarks/drf_fixtures/sample_app
python_files = test_*.py
"""


def write_support(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "conftest.py").write_text(CONFTEST, encoding="utf-8")
    (out_dir / "pytest.ini").write_text(PYTEST_INI, encoding="utf-8")


def run_pytest(out_dir: Path, junit_path: Path, python: str | None = None) -> int:
    junit_path.parent.mkdir(parents=True, exist_ok=True)
    python = python or sys.executable
    proc = subprocess.run(
        [python, "-m", "pytest", "-q", "--tb=no", f"--junitxml={junit_path}"],
        cwd=str(out_dir), capture_output=True, text=True,
    )
    return proc.returncode


def _parse_junit(junit_path: Path) -> dict[str, str]:
    """testcase fonksiyon adı -> 'passed' | 'failed' | 'error' | 'skipped'."""
    results: dict[str, str] = {}
    if not junit_path.exists():
        return results
    root = ET.parse(junit_path).getroot()
    for tc in root.iter("testcase"):
        name = tc.get("name", "")
        outcome = "passed"
        for child in tc:
            if child.tag == "failure":
                outcome = "failed"
            elif child.tag == "error":
                outcome = "error"
            elif child.tag == "skipped":
                outcome = "skipped"
        results[name] = outcome
    return results


def classify(cases: list[Case], generation: list[GenerationOutcome], junit_path: Path
             ) -> list[ExecutionOutcome]:
    meta = {c.scenario_id: c for c in cases}
    gen = {g.scenario_id: g for g in generation}
    junit = _parse_junit(junit_path)
    outcomes: list[ExecutionOutcome] = []

    for sid, g in gen.items():
        if g.status != "GENERATED":
            outcomes.append(ExecutionOutcome(sid, "NOT_RUN", None, f"üretim durumu: {g.status}"))
            continue
        fname = test_name(sid)
        po = junit.get(fname)
        case = meta[sid]
        if po is None:
            outcomes.append(ExecutionOutcome(sid, "GENERATION_ERROR", None, "pytest testi toplayamadı"))
            continue
        if po == "error":
            outcomes.append(ExecutionOutcome(sid, "GENERATION_ERROR", po, "çalıştırma/toplama hatası"))
        elif po == "passed":
            if case.is_known_flaw:
                outcomes.append(ExecutionOutcome(sid, "KNOWN_FLAW_NOT_DETECTED", po,
                                                 "güvenli durum geçti; kusur (içerik düzeyi) durum koduyla yakalanmaz"))
            else:
                outcomes.append(ExecutionOutcome(sid, "PASSED", po, "uygulama güvenli beklentiyle uyumlu"))
        elif po == "failed":
            if case.is_known_flaw:
                outcomes.append(ExecutionOutcome(sid, "KNOWN_FLAW_DETECTED", po,
                                                 "güvensiz uç güvenli beklentiden sapıyor (kusur yakalandı)"))
            else:
                outcomes.append(ExecutionOutcome(sid, "APPLICATION_MISMATCH", po,
                                                 "hatasız senaryoda güvenli beklenti tutmadı (üretim/ifade hatası)"))
        else:  # skipped
            outcomes.append(ExecutionOutcome(sid, "NOT_RUN", po, "atlandı"))
    return outcomes
