"""Üretilen testlerin çalıştırılması ve sonuç sınıflandırması — H3-04 / Issue #30.

Pytest sonucu (passed/failed/error) olduğu gibi korunur; ``xfail`` veya istisna yutma kullanılmaz.
Sınıflandırma ayrı bir alandır:

* ``PASSED``                  — test geçti; referanstaki güvenli beklenti karşılandı.
* ``KNOWN_FLAW_DETECTED``     — test BAŞARISIZ; bilinen (bilerek eklenmiş) güvenlik kusuru tespit edildi
                                (gözlenen kod = ground truth'taki ``observed_flawed_status``).
* ``KNOWN_FLAW_NOT_DETECTED`` — test geçti, ancak senaryo bilinen bir kusur; kusur bu testle görünmedi
                                (ör. içerik düzeyi sapma, durum kodu aynı).
* ``APPLICATION_MISMATCH``    — test doğru çalıştı fakat uygulama davranışı referanstan farklı.
* ``GENERATION_ERROR``        — üretici kaynaklı teknik hata (yanlış URL, içe aktarma, fixture, kurulum,
                                beklenmeyen istisna, toplanamayan test).
* ``ENVIRONMENT_ERROR``       — hedef uygulama/ortam yüklenemiyor (ör. hedef kodda sözdizimi hatası, eksik
                                bağımlılık). Ön kontrolde tespit edilir; üreticiye yüklenmez.
"""
from __future__ import annotations

import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path

from .contracts import TestPlan

MARKER_RX = re.compile(r"\[H304\] scenario=(?P<sid>\S+) check=(?P<check>\w+) expected=(?P<exp>\S+) "
                       r"observed=(?P<obs>\S+)")

CLASS_LABELS = {
    "PASSED": "Geçti — referanstaki güvenli beklenti karşılandı",
    "KNOWN_FLAW_DETECTED": "Başarısız — bilinen güvenlik kusuru tespit edildi",
    "KNOWN_FLAW_NOT_DETECTED": "Geçti — bilinen güvenlik kusuru bu testle tespit edilemedi",
    "APPLICATION_MISMATCH": "Başarısız — uygulama davranışı bağımsız referanstan farklı",
    "GENERATION_ERROR": "Üretim kaynaklı teknik hata",
    "ENVIRONMENT_ERROR": "Hedef uygulama/ortam yüklenemedi (üretici kaynaklı değil)",
}

_ENV_PROBE = (
    "import importlib, django\n"
    "django.setup()\n"
    "from django.conf import settings\n"
    "importlib.import_module(settings.ROOT_URLCONF)\n"
)


def check_environment(out_dir: Path) -> tuple[bool, str]:
    """Üretilen paketin pytest.ini'sindeki ayarlarla hedef uygulamanın yüklenebildiğini doğrular."""
    import configparser
    import os

    ini = configparser.ConfigParser()
    ini.read(out_dir / "pytest.ini", encoding="utf-8")
    sect = ini["pytest"]
    paths = [str((out_dir / p).resolve()) for p in sect.get("pythonpath", ".").split()]
    env = dict(os.environ, DJANGO_SETTINGS_MODULE=sect["DJANGO_SETTINGS_MODULE"],
               PYTHONPATH=os.pathsep.join(paths + [os.environ.get("PYTHONPATH", "")]).rstrip(os.pathsep))
    proc = subprocess.run([sys.executable, "-c", _ENV_PROBE], cwd=out_dir, env=env, capture_output=True, text=True,
                          timeout=300)
    last = (proc.stderr.strip().splitlines() or [""])[-1]
    return proc.returncode == 0, last


@dataclass
class TestResult:
    __test__ = False

    scenario_id: str
    test_name: str
    module: str
    http_method: str
    expected_status: int
    observed_status: int | None
    pytest_outcome: str
    check: str | None
    classification: str
    evidence: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["classification_label"] = CLASS_LABELS[self.classification]
        return d


def _pytest(args: list[str], cwd: Path, timeout: int = 900) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "pytest", *args], cwd=cwd, capture_output=True, text=True,
                          timeout=timeout)


def collect(out_dir: Path) -> tuple[list[str], str]:
    """Pytest keşfi: toplanan test düğüm kimlikleri ve ham çıktı."""
    proc = _pytest(["--collect-only", "-q"], out_dir)
    nodes = [ln.strip() for ln in proc.stdout.splitlines() if "::" in ln]
    return nodes, proc.stdout + proc.stderr


def run(out_dir: Path, junit_path: Path, node_ids: list[str] | None = None) -> tuple[dict[str, dict], str, int]:
    """Testleri çalıştırır; JUnit XML'den test adı → (outcome, message) eşlemesi döndürür."""
    junit_path.parent.mkdir(parents=True, exist_ok=True)
    proc = _pytest(["-q", "-rA", f"--junitxml={junit_path}", *(node_ids or [])], out_dir)
    results: dict[str, dict] = {}
    if junit_path.exists():
        for case in ET.parse(junit_path).getroot().iter("testcase"):
            name = case.get("name", "")
            outcome, msg = "passed", ""
            for tag in ("failure", "error", "skipped"):
                el = case.find(tag)
                if el is not None:
                    outcome = {"failure": "failed", "error": "error", "skipped": "skipped"}[tag]
                    msg = (el.get("message") or "") + "\n" + (el.text or "")
                    break
            results[name] = {"outcome": outcome, "message": msg.strip(), "file": case.get("classname", "")}
    return results, proc.stdout[-4000:] + proc.stderr[-2000:], proc.returncode


def classify(plan: TestPlan, raw: dict | None) -> TestResult:
    base = dict(scenario_id=plan.scenario_id, test_name=plan.test_name, module=plan.module,
                http_method=plan.http_method, expected_status=plan.expected_status)
    if raw is None:
        return TestResult(**base, observed_status=None, pytest_outcome="not_collected", check=None,
                          classification="GENERATION_ERROR", evidence="Test pytest tarafından toplanmadı/çalışmadı.")
    outcome, msg = raw["outcome"], raw["message"]
    m = MARKER_RX.search(msg)
    observed = int(m.group("obs")) if m and m.group("check") == "status" and m.group("obs").isdigit() else None
    if outcome == "passed":
        cls = "KNOWN_FLAW_NOT_DETECTED" if plan.is_known_flaw else "PASSED"
        ev = ("Durum kodu referansla eşleşti; kusurun sapması bu testin doğruladığı boyutta değil "
              f"({(plan.security_finding or {}).get('deviation_kind')})." if plan.is_known_flaw
              else "Durum kodu ve yan etki kontrolleri geçti.")
        return TestResult(**base, observed_status=plan.expected_status, pytest_outcome=outcome, check=None,
                          classification=cls, evidence=ev)
    first = msg.splitlines()[0][:500] if msg else ""
    if outcome == "failed" and m and m.group("check") in ("status", "side_effect"):
        check = m.group("check")
        sf = plan.security_finding or {}
        if plan.is_known_flaw and check == "status" and observed == sf.get("observed_flawed_status"):
            return TestResult(**base, observed_status=observed, pytest_outcome=outcome, check=check,
                              classification="KNOWN_FLAW_DETECTED",
                              evidence=f"Gözlenen {observed}, ground truth'taki bilinen kusur durumuyla "
                                       f"(observed_flawed_status={sf.get('observed_flawed_status')}) aynı; "
                                       f"güvenli beklenti {plan.expected_status}. {sf.get('finding_type', '')}")
        return TestResult(**base, observed_status=observed, pytest_outcome=outcome, check=check,
                          classification="APPLICATION_MISMATCH", evidence=first)
    return TestResult(**base, observed_status=observed, pytest_outcome=outcome,
                      check=m.group("check") if m else None, classification="GENERATION_ERROR", evidence=first)


def classify_all(plans: list[TestPlan], raw: dict[str, dict], environment_error: str | None = None) -> list[TestResult]:
    ordered = sorted(plans, key=lambda p: p.scenario_id)
    if environment_error is not None:
        return [TestResult(scenario_id=p.scenario_id, test_name=p.test_name, module=p.module,
                           http_method=p.http_method, expected_status=p.expected_status, observed_status=None,
                           pytest_outcome=(raw.get(p.test_name) or {}).get("outcome", "not_run"), check=None,
                           classification="ENVIRONMENT_ERROR", evidence=environment_error[:500]) for p in ordered]
    return [classify(p, raw.get(p.test_name)) for p in ordered]


def isolation_check(out_dir: Path, plans: list[TestPlan], suite_raw: dict[str, dict],
                    work_dir: Path) -> dict:
    """Her testi tek başına ve tüm paketi ters sırayla çalıştırıp sonuçların aynı kaldığını doğrular."""
    nodes = [f"{p.module}::{p.test_name}" for p in sorted(plans, key=lambda p: (p.module, p.scenario_id))]
    reversed_raw, _, _ = run(out_dir, work_dir / "reversed.xml", list(reversed(nodes)))
    single_diff, reversed_diff = [], []
    for node, p in zip(nodes, sorted(plans, key=lambda p: (p.module, p.scenario_id))):
        one, _, _ = run(out_dir, work_dir / "single.xml", [node])
        if one.get(p.test_name, {}).get("outcome") != suite_raw.get(p.test_name, {}).get("outcome"):
            single_diff.append(p.test_name)
        if reversed_raw.get(p.test_name, {}).get("outcome") != suite_raw.get(p.test_name, {}).get("outcome"):
            reversed_diff.append(p.test_name)
    return {"tests": len(nodes), "single_run_differences": single_diff, "reversed_order_differences": reversed_diff,
            "isolated": not single_diff and not reversed_diff}
