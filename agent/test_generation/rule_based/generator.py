"""Üretim akışı: yükle → planla → kod üret → doğrula → yaz — H3-04 / Issue #30."""
from __future__ import annotations

import hashlib
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from . import codegen
from .contracts import (
    CODE_STATUS,
    SUPPORTED_METHODS,
    Diagnostic,
    EndpointSummary,
    ReferenceCase,
    ScenarioOutcome,
    Severity,
    Status,
    TestPlan,
)
from .planner import plan_case
from .validation import validate_suite

SUPPORT_SOURCE = Path(__file__).resolve().parent / "runtime_support.py"
GENERATED_FILE_RX = re.compile(r"^test_[a-z]+_generated\.py$")


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@dataclass
class GenerationResult:
    outcomes: list[ScenarioOutcome]
    global_diagnostics: list[Diagnostic]
    modules: dict[str, str] = field(default_factory=dict)
    support_files: dict[str, str] = field(default_factory=dict)

    @property
    def plans(self) -> list[TestPlan]:
        return [o.plan for o in self.outcomes if o.status is Status.GENERATED and o.plan]

    def counts(self) -> dict[str, int]:
        return {s.value: sum(1 for o in self.outcomes if o.status is s) for s in Status}


def generate(cases: list[ReferenceCase], summary: EndpointSummary, users: list[dict], resources: list[dict],
             input_digests: dict[str, str], join_diagnostics: list[Diagnostic] | None = None,
             pytest_ini_pythonpath: str = ".") -> GenerationResult:
    """Tüm senaryoları planlar ve test modüllerini bellekte üretir (dosyaya yazmaz)."""
    outcomes: list[ScenarioOutcome] = []
    global_diags: list[Diagnostic] = []
    for d in join_diagnostics or []:
        if d.scenario_id and d.severity is Severity.ERROR:
            outcomes.append(ScenarioOutcome(d.scenario_id, CODE_STATUS[d.code], None, [d]))
        else:
            global_diags.append(d)
    for case in sorted(cases, key=lambda c: str(c.scenario_id)):
        outcomes.append(plan_case(case, summary, users, resources))
    outcomes.sort(key=lambda o: str(o.scenario_id))

    result = GenerationResult(outcomes, global_diags)
    plans = result.plans
    for method in SUPPORTED_METHODS:
        group = [p for p in plans if p.http_method == method]
        if group:
            result.modules[group[0].module] = codegen.build_module(method, group, input_digests)
    problems = validate_suite(result.modules, plans)
    if problems:
        bad = {d.scenario_id for d in problems if d.scenario_id}
        for o in result.outcomes:
            if o.scenario_id in bad:
                o.status = Status.GENERATION_ERROR
                o.diagnostics += [d for d in problems if d.scenario_id == o.scenario_id]
        global_diags += [d for d in problems if not d.scenario_id]
    result.support_files = {
        "conftest.py": codegen.build_conftest(list(summary.fixtures)),
        f"{codegen.SUPPORT_MODULE}.py": SUPPORT_SOURCE.read_text(encoding="utf-8"),
        "pytest.ini": codegen.build_pytest_ini(summary.settings_module, pytest_ini_pythonpath),
    }
    # Not: çıktı dizinine __init__.py yazılmaz. Paket olursa pytest modülleri "<dizin_adı>.<modül>" olarak
    # içe aktarır ve dizin adı standart kütüphaneyle (ör. "copy") çakışınca paket yüklenemez.
    return result


def write_output(result: GenerationResult, out_dir: Path) -> list[Path]:
    """Üretilen dosyaları yazar; bu dizindeki eski üretilmiş test dosyalarını temizler."""
    if result.global_diagnostics and any(d.severity is Severity.ERROR for d in result.global_diagnostics):
        errors = [d for d in result.global_diagnostics if d.severity is Severity.ERROR]
        if any(CODE_STATUS.get(d.code) is Status.GENERATION_ERROR for d in errors):
            raise RuntimeError("Üretim doğrulaması başarısız; dosyalar yazılmadı: "
                               + "; ".join(f"{d.code.value}: {d.message} {d.detail}" for d in errors))
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in out_dir.iterdir():
        if f.is_file() and GENERATED_FILE_RX.match(f.name) and f.name not in result.modules:
            f.unlink()
    cache = out_dir / "__pycache__"
    if cache.exists():
        shutil.rmtree(cache)
    written = []
    for name, src in sorted({**result.support_files, **result.modules}.items()):
        path = out_dir / name
        path.write_text(src, encoding="utf-8", newline="\n")
        written.append(path)
    return written


def relative_pythonpath(out_dir: Path, target_app: Path) -> str:
    return os.path.relpath(target_app.resolve(), out_dir.resolve()).replace(os.sep, "/")
