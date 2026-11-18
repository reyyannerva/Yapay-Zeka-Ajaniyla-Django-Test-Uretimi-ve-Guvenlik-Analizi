"""Değerlendirme hattı: artefakt eşleme, güvenlik ön kontrolü, toplama/çalıştırma ve sınıflandırma.

Bu testler değerlendiricinin kendisini sınar; sentetik test modülleri yalnızca hattın hata durumlarını
nasıl sınıflandırdığını göstermek içindir ve hiçbir baseline sonucunun yerine kullanılmaz.
"""
import json
import shutil

import pytest

from agent.evaluation import artifacts as A
from agent.evaluation import execution as X
from agent.evaluation import manifest as mf
from agent.evaluation.metrics import Outcome, compute

HEADER = "import pytest\nfrom django.urls import reverse\npytestmark = pytest.mark.django_db\n\n"
CONFTEST = mf.H305 / "generated_tests" / "conftest.py"
REC = {"scenario_id": "SC-X-001", "http_method": "GET", "user_role": "anonymous", "secure_status": 200,
       "is_known_flaw": False, "deviation_kind": None}
FLAW = dict(REC, scenario_id="SC-X-002", is_known_flaw=True, deviation_kind="status")


def art(body, sid="SC-X-001", fn="test_x"):
    return A.Artifact(sid, "synthetic", "synthetic", HEADER + body, fn, {"conftest.py": CONFTEST})


def ev(tmp_path, rec, arts, **kw):
    return X.evaluate_scenario(rec, arts, tmp_path / "work", tmp_path / "logs", **kw)


# ------------------------------------------------------------------ interpret / observed_status

def _probe(*recs):
    return {"records": [dict({"nodeid": "t::x", "xfail": False, "exc_type": None, "message": ""}, **r) for r in recs]}


@pytest.mark.parametrize("probe,expected", [
    (_probe({"when": "setup", "outcome": "passed"}, {"when": "call", "outcome": "passed"}), "PASS"),
    (_probe({"when": "call", "outcome": "failed", "exc_type": "AssertionError"}), "FAIL"),
    (_probe({"when": "call", "outcome": "failed", "exc_type": "NoReverseMatch"}), "ERROR"),
    (_probe({"when": "setup", "outcome": "failed", "exc_type": "FixtureLookupError"}), "ERROR"),
    (_probe({"when": "collect", "outcome": "failed", "exc_type": "CollectionError"}), "COLLECTION_ERROR"),
    (_probe({"when": "setup", "outcome": "skipped"}), "ERROR"),
    (_probe({"when": "call", "outcome": "skipped", "xfail": True}), "ERROR"),
    (_probe({"when": "call", "outcome": "failed", "exc_type": "AssertionError",
             "message": "[H304] scenario=S check=route expected=/a/ observed=/b/"}), "ERROR"),
    (None, "COLLECTION_ERROR"),
    ({"records": []}, "COLLECTION_ERROR"),
])
def test_interpret(probe, expected):
    assert X.interpret(probe)[0] == expected


def test_observed_status_parsing():
    assert X.observed_status("assert 200 == 403\n + where") == 200
    assert X.observed_status("[H304] scenario=S check=status expected=403 observed=204 | x") == 204
    assert X.observed_status("ValueError: x") is None


# ------------------------------------------------------------------ güvenlik ön kontrolü

@pytest.mark.parametrize("src,unsafe", [
    ("import requests\n", True),
    ("from urllib.request import urlopen\n", True),
    ("import socket\n", True),
    ("import subprocess\n", True),
    ("import os\nos.system('ls')\n", True),
    ("u = 'https://example.com/api/'\n", True),
    ("u = 'http://testserver/api/'\n", False),
    ("from django.urls import reverse\nu = '/api/articles/'\n", False),
])
def test_safety_violations(src, unsafe):
    assert bool(A.safety_violations(src)) is unsafe


# ------------------------------------------------------------------ uçtan uca (gerçek pytest süreçleri)

def test_passing_test_is_tn(tmp_path):
    r = ev(tmp_path, REC, [art("def test_x(api_client):\n    assert api_client.get('/api/articles/').status_code == 200\n")])
    assert (r["outcome"], r["confusion_cell"], r["syntax_valid"], r["collected"]) == ("PASS", "TN", True, True)
    assert (tmp_path / "logs" / "SC-X-001" / "run.log").exists()


def test_assertion_failure_on_flaw_is_tp_with_observed_status(tmp_path):
    body = "def test_x(api_client):\n    r = api_client.get('/api/articles/')\n    assert r.status_code == 403\n"
    r = ev(tmp_path, FLAW, [art(body, sid="SC-X-002")])
    assert (r["outcome"], r["confusion_cell"], r["observed_status"]) == ("FAIL", "TP", 200)


def test_assertion_failure_on_clean_scenario_is_fp(tmp_path):
    body = "def test_x(api_client):\n    assert api_client.get('/api/articles/').status_code == 418\n"
    assert ev(tmp_path, REC, [art(body)])["confusion_cell"] == "FP"


def test_runtime_exception_is_error_not_detection(tmp_path):
    body = "def test_x(api_client):\n    reverse('olmayan-rota')\n"
    r = ev(tmp_path, FLAW, [art(body, sid="SC-X-002")])
    assert (r["outcome"], r["exc_type"], r["confusion_cell"]) == ("ERROR", "NoReverseMatch", "FN")


def test_missing_fixture_is_error(tmp_path):
    r = ev(tmp_path, REC, [art("def test_x(olmayan_fixture):\n    assert True\n")])
    assert r["outcome"] == "ERROR" and r["confusion_cell"] == "EXCLUDED"


def test_syntax_error_not_executed(tmp_path):
    r = ev(tmp_path, FLAW, [art("def test_x(:\n    pass\n", sid="SC-X-002")])
    assert (r["outcome"], r["syntax_valid"], r["confusion_cell"]) == ("SYNTAX_INVALID", False, "FN")
    assert not (tmp_path / "work" / "SC-X-002").exists()


def test_collection_error(tmp_path):
    r = ev(tmp_path, REC, [art("import olmayan_modul_h306\n\ndef test_x():\n    assert True\n")])
    assert (r["outcome"], r["collected"]) == ("COLLECTION_ERROR", False)


def test_module_without_tests_is_collection_error(tmp_path):
    assert ev(tmp_path, REC, [art("def yardimci():\n    return 1\n")])["outcome"] == "COLLECTION_ERROR"


def test_timeout(tmp_path):
    r = ev(tmp_path, REC, [art("import time\n\ndef test_x():\n    time.sleep(60)\n")], timeout=15)
    assert r["outcome"] == "TIMEOUT" and r["pytest_summary"] == "ERROR"


def test_unsafe_test_is_blocked_before_execution(tmp_path):
    r = ev(tmp_path, FLAW, [art("import requests\n\ndef test_x():\n    requests.get('https://example.com')\n",
                               sid="SC-X-002")])
    assert (r["outcome"], r["confusion_cell"]) == ("UNSAFE_BLOCKED", "FN")
    assert not (tmp_path / "work" / "SC-X-002").exists()


def test_missing_and_duplicate_artifacts(tmp_path):
    assert ev(tmp_path, FLAW, [])["outcome"] == "NO_ARTIFACT"
    assert ev(tmp_path, FLAW, [])["confusion_cell"] == "FN"
    dup = [art("def test_x():\n    assert True\n"), art("def test_y():\n    assert True\n")]
    assert ev(tmp_path, REC, dup)["outcome"] == "DUPLICATE_ARTIFACT"


def test_environment_error_is_not_blamed_on_generator(tmp_path):
    r = ev(tmp_path, REC, [art("def test_x():\n    assert True\n")], env_ok=False)
    assert (r["outcome"], r["confusion_cell"]) == ("ENVIRONMENT_ERROR", "EXCLUDED")


def test_environment_check_passes_here():
    assert X.check_environment()[0] is True


def test_api_keys_not_passed_to_test_processes(tmp_path, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gizli")
    assert "GROQ_API_KEY" not in X._env(tmp_path)


# ------------------------------------------------------------------ baseline adaptörleri (gerçek artefaktlar)

IDS = mf.load_test_set()


@pytest.mark.parametrize("baseline", ["rule_based", "llm"])
def test_every_test_set_scenario_maps_to_exactly_one_artifact(baseline):
    arts = A.ADAPTERS[baseline](IDS)
    assert set(arts) == set(IDS)
    assert {sid: len(v) for sid, v in arts.items()} == {sid: 1 for sid in IDS}


def test_rule_based_extraction_keeps_only_target_function_unchanged():
    arts = A.rule_based_artifacts(IDS)
    for sid, (a,) in arts.items():
        names = [ln for ln in a.source.splitlines() if ln.startswith("def test_")]
        assert names == [f"def {a.function}(seeded_db, api_client):"], sid
        module, fn = a.origin.split("::")
        assert a.source.split("\n\n\n", 1)[1].rstrip("\n") in (mf.REPO / module).read_text(encoding="utf-8")


def test_llm_artifact_equals_committed_generated_file_body():
    for sid, (a,) in A.llm_artifacts(IDS).items():
        gen = (mf.H305 / "generated_tests" / f"test_{A.sid_token(sid)}.py").read_text(encoding="utf-8")
        assert gen.rstrip("\n").endswith(a.source.rstrip("\n")), sid


def test_llm_missing_or_empty_raw_response_is_no_artifact(tmp_path):
    base = tmp_path / "h305"
    shutil.copytree(mf.H305 / "reports", base / "reports")
    shutil.copytree(mf.H305 / "generated_tests", base / "generated_tests")
    (base / "raw_responses").mkdir()
    (base / "raw_responses" / "SC-FLW-001.txt").write_text("", encoding="utf-8")
    arts = A.llm_artifacts(["SC-FLW-001", "SC-FLW-002"], base=base)
    assert arts == {"SC-FLW-001": [], "SC-FLW-002": []}


def test_unknown_scenarios_in_artifacts_are_ignored():
    arts = A.llm_artifacts(["SC-FLW-001"])
    assert list(arts) == ["SC-FLW-001"]  # dev kümesi artefaktları değerlendirmeye girmez


# ------------------------------------------------------------------ kayıtlı sonuçların tutarlılığı

def test_committed_metrics_recompute_from_committed_results():
    out = mf.OUT / "results"
    summary = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
    for b in ("rule_based", "llm"):
        rows = json.loads((out / b / "results.json").read_text(encoding="utf-8"))["results"]
        assert [r["scenario_id"] for r in rows] == IDS
        m = compute(Outcome(r["scenario_id"], r["http_method"], r["is_known_flaw"], r["outcome"]) for r in rows)
        assert m == summary["baselines"][b]["metrics"]
