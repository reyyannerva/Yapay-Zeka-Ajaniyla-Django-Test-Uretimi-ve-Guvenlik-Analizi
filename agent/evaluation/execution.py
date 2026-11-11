"""Senaryo başına yalıtılmış sözdizimi → toplama → çalıştırma hattı — H3-06 / Issue #32.

Her iki baseline'a **aynı** işlem uygulanır:

1. Senaryo ↔ artefakt eşlemesi (yok → ``NO_ARTIFACT``, birden fazla → ``DUPLICATE_ARTIFACT``).
2. ``ast.parse`` ile sözdizimi kontrolü (``SYNTAX_INVALID``).
3. Güvenlik ön kontrolü: dış ağ/süreç erişimi içeren test çalıştırılmaz (``UNSAFE_BLOCKED``).
4. Geçici, senaryoya özel bir dizinde ``pytest --collect-only`` (``COLLECTION_ERROR``).
5. Ayrı bir pytest sürecinde çalıştırma, zaman aşımı ile (``TIMEOUT``); sonuç ``pytest_probe`` ile
   aşama/istisna türü düzeyinde okunur: doğrulama başarısızlığı ``FAIL``, kurulum hatası veya doğrulama
   dışı istisna ``ERROR``, başarı ``PASS``.

Testler yalnızca Django test istemcisiyle kontrollü ``sample_app``'e karşı, geçici test veritabanında
çalışır; üretim veya dış hedef kullanılmaz. Hiçbir test onarılmaz veya yeniden üretilmez.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import manifest as mf
from .artifacts import Artifact, safety_violations, sid_token, syntax_error
from .metrics import confusion_cell, pytest_summary

SAMPLE_APP = mf.REPO / "benchmarks" / "drf_fixtures" / "sample_app"
SETTINGS = "config.settings"
DEFAULT_TIMEOUT = 120
_H304_MARK = re.compile(r"\[H304\] scenario=\S+ check=(?P<check>\w+) expected=\S+ observed=(?P<obs>\S+)")
_ASSERT_STATUS = re.compile(r"assert (\d{3}) == (\d{3})")
_ENV_PROBE = ("import importlib, django\ndjango.setup()\nfrom django.conf import settings\n"
              "importlib.import_module(settings.ROOT_URLCONF)\n")

PYTEST_INI = """[pytest]
DJANGO_SETTINGS_MODULE = {settings}
python_files = test_*.py
addopts = -p no:cacheprovider -p agent.evaluation.pytest_probe
"""


def _env(work: Path) -> dict:
    paths = [str(work), str(SAMPLE_APP), str(mf.REPO)]
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GROQ_", "OPENAI_", "ANTHROPIC_"))}
    env.update(DJANGO_SETTINGS_MODULE=SETTINGS, PYTHONPATH=os.pathsep.join(paths), PYTHONDONTWRITEBYTECODE="1",
               PYTHONHASHSEED="0")
    return env


def _sanitize(text: str, work: Path) -> str:
    return text.replace(str(work), "<WORK>").replace(str(mf.REPO), "<REPO>")


def check_environment(timeout: int = 300) -> tuple[bool, str]:
    """Hedef uygulama yüklenebiliyor mu? Değilse sonuçlar üreticiye değil ortama yazılır."""
    with tempfile.TemporaryDirectory(prefix="h306_env_") as tmp:
        proc = subprocess.run([sys.executable, "-c", _ENV_PROBE], cwd=tmp, env=_env(Path(tmp)),
                              capture_output=True, text=True, timeout=timeout)
    return proc.returncode == 0, (proc.stderr.strip().splitlines() or ["ok"])[-1]


def materialize(art: Artifact, work: Path) -> Path:
    work.mkdir(parents=True, exist_ok=True)
    for name, src in art.support_files.items():
        shutil.copyfile(src, work / name)
    (work / "pytest.ini").write_text(PYTEST_INI.format(settings=SETTINGS), encoding="utf-8")
    test_file = work / f"test_{sid_token(art.scenario_id)}.py"
    test_file.write_text(art.source, encoding="utf-8", newline="\n")
    return test_file


def _pytest(args: list[str], work: Path, timeout: int, probe_out: Path | None = None):
    env = _env(work)
    if probe_out is not None:
        env["H306_PROBE_OUT"] = str(probe_out)
    return subprocess.run([sys.executable, "-m", "pytest", *args], cwd=work, env=env, capture_output=True,
                          text=True, timeout=timeout)


def interpret(probe: dict | None) -> tuple[str, str | None, str]:
    """Probe kayıtlarından (outcome, exc_type, message) üretir."""
    if not probe or not probe.get("records"):
        return "COLLECTION_ERROR", None, "pytest hiçbir test sonucu raporlamadı"
    recs = probe["records"]
    collect_fail = [r for r in recs if r["when"] == "collect"]
    if collect_fail:
        r = collect_fail[0]
        return "COLLECTION_ERROR", r["exc_type"], r["message"]
    phase_err = [r for r in recs if r["when"] in ("setup", "teardown") and r["outcome"] == "failed"]
    if phase_err:
        r = phase_err[0]
        return "ERROR", r["exc_type"], f"[{r['when']}] {r['message']}"
    calls = [r for r in recs if r["when"] == "call"]
    skipped = [r for r in recs if r["outcome"] == "skipped" or r["xfail"]]
    if skipped or not calls:
        r = (skipped or recs)[0]
        return "ERROR", r["exc_type"] or "Skipped", "test atlandı/xfail; sonuç ölçülemez"
    failed = [r for r in calls if r["outcome"] == "failed"]
    if not failed:
        return "PASS", None, ""
    r = failed[0]
    if r["exc_type"] != "AssertionError":
        return "ERROR", r["exc_type"], r["message"]
    mark = _H304_MARK.search(r["message"])
    if mark and mark.group("check") == "route":
        return "ERROR", "RouteAssertion", r["message"]  # üretici kaynaklı yanlış URL (H3-04 işareti)
    return "FAIL", "AssertionError", r["message"]


def observed_status(message: str) -> int | None:
    mark = _H304_MARK.search(message or "")
    if mark and mark.group("obs").isdigit():
        return int(mark.group("obs"))
    m = _ASSERT_STATUS.search(message or "")
    return int(m.group(1)) if m else None


def evaluate_scenario(rec: dict, arts: list[Artifact], work_root: Path, log_dir: Path | None,
                      timeout: int = DEFAULT_TIMEOUT, env_ok: bool = True) -> dict:
    sid = rec["scenario_id"]
    result = {k: rec[k] for k in ("scenario_id", "http_method", "user_role", "secure_status", "is_known_flaw",
                                  "deviation_kind")}
    result.update(artifact_origin=None, artifact_sha256=None, test_function=None, syntax_valid=None,
                  collected=None, collected_count=None, exc_type=None, observed_status=None, evidence="")

    def done(outcome: str, **kw) -> dict:
        result.update(kw)
        result["outcome"] = outcome
        result["pytest_summary"] = pytest_summary(outcome)
        result["confusion_cell"] = confusion_cell(rec["is_known_flaw"], outcome)
        return result

    if not arts:
        return done("NO_ARTIFACT", evidence="senaryo için test artefaktı bulunamadı")
    if len(arts) > 1:
        return done("DUPLICATE_ARTIFACT", evidence="birden fazla aday: " + ", ".join(a.origin for a in arts))
    art = arts[0]
    result.update(artifact_origin=art.origin, test_function=art.function,
                  artifact_sha256=hashlib.sha256(art.source.encode("utf-8")).hexdigest())
    err = syntax_error(art.source)
    if err:
        return done("SYNTAX_INVALID", syntax_valid=False, evidence=err)
    result["syntax_valid"] = True
    unsafe = safety_violations(art.source)
    if unsafe:
        return done("UNSAFE_BLOCKED", evidence="; ".join(unsafe))
    if not env_ok:
        return done("ENVIRONMENT_ERROR", evidence="hedef uygulama yüklenemedi; test çalıştırılmadı")

    work = work_root / sid
    test_file = materialize(art, work)
    logs = log_dir / sid if log_dir else None
    if logs:
        logs.mkdir(parents=True, exist_ok=True)
        (logs / "test_module.py").write_text(art.source, encoding="utf-8", newline="\n")
    try:
        col = _pytest(["--collect-only", "-q", test_file.name], work, timeout)
    except subprocess.TimeoutExpired:
        return done("TIMEOUT", collected=False, evidence=f"toplama {timeout} sn içinde bitmedi")
    nodes = [ln.strip() for ln in col.stdout.splitlines() if "::" in ln]
    if logs:
        (logs / "collect.log").write_text(_sanitize(col.stdout + col.stderr, work), encoding="utf-8",
                                          newline="\n")
    result.update(collected=bool(nodes), collected_count=len(nodes))
    if not nodes:
        tail = [ln for ln in (col.stdout + col.stderr).splitlines() if ln.strip()][-3:]
        return done("COLLECTION_ERROR", evidence=_sanitize(" | ".join(tail), work)[:600])

    probe_out = work / "probe.json"
    try:
        run = _pytest(["-q", "-rA", test_file.name], work, timeout, probe_out)
    except subprocess.TimeoutExpired:
        return done("TIMEOUT", evidence=f"çalıştırma {timeout} sn içinde bitmedi")
    probe = json.loads(probe_out.read_text(encoding="utf-8")) if probe_out.exists() else None
    if logs:
        (logs / "run.log").write_text(_sanitize(run.stdout + run.stderr, work), encoding="utf-8", newline="\n")
        if probe is not None:
            (logs / "probe.json").write_text(_sanitize(json.dumps(probe, ensure_ascii=False, indent=1), work)
                                             + "\n", encoding="utf-8", newline="\n")
    outcome, exc_type, message = interpret(probe)
    message = _sanitize(message, work)
    return done(outcome, exc_type=exc_type, observed_status=observed_status(message),
                evidence=message.strip().splitlines()[0][:400] if message.strip() else "")


def evaluate_baseline(records: list[dict], artifacts: dict[str, list[Artifact]], log_dir: Path | None = None,
                      timeout: int = DEFAULT_TIMEOUT, env_ok: bool | None = None) -> list[dict]:
    if env_ok is None:
        env_ok, _ = check_environment()
    with tempfile.TemporaryDirectory(prefix="h306_") as tmp:
        return [evaluate_scenario(r, artifacts.get(r["scenario_id"], []), Path(tmp), log_dir, timeout, env_ok)
                for r in records]
