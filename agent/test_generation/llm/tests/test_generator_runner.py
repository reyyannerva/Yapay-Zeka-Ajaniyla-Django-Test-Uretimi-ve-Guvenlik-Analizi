"""Üretici (sahte istemci ile) ve sınıflandırıcı testleri — ağ/anahtar gerekmez."""
import re

from agent.test_generation.llm import generator, runner
from agent.test_generation.llm.client import LLMError, LLMResponse
from agent.test_generation.llm.contracts import GenerationOutcome
from agent.test_generation.llm.prompt import test_name as make_test_name

_TNAME = re.compile(r"test_[a-z0-9_]+")


class _Fake:
    api_key_env = "GROQ_API_KEY"

    def __init__(self, mode="good"):
        self.mode = mode

    def complete(self, system, user):
        tname = _TNAME.search(user).group(0)
        if self.mode == "good":
            text = f"```python\nimport pytest\npytestmark = pytest.mark.django_db\n\n\ndef {tname}(seeded_db, api_client):\n    assert True\n```"
        elif self.mode == "bad":
            text = f"```python\ndef {tname}(:\n    pass\n```"
        elif self.mode == "empty":
            text = ""
        elif self.mode == "error":
            raise LLMError("quota", "429")
        return LLMResponse(text=text, prompt_tokens=10, completion_tokens=20, latency_ms=5)


def _one_case(cases):
    return [cases["SC-UPD-001"]]


def test_generator_good(cases, tmp_path):
    out, raw = tmp_path / "gen", tmp_path / "raw"
    res = generator.run(_one_case(cases), _Fake("good"), out, raw, "fake")
    assert res[0].status == "GENERATED"
    assert (out / "test_sc_upd_001.py").exists()
    assert (raw / "SC-UPD-001.txt").exists()


def test_generator_bad_syntax(cases, tmp_path):
    res = generator.run(_one_case(cases), _Fake("bad"), tmp_path / "g", tmp_path / "r", "fake")
    assert res[0].status == "INVALID_SYNTAX"
    assert not (tmp_path / "g" / "test_sc_upd_001.py").exists()


def test_generator_empty(cases, tmp_path):
    res = generator.run(_one_case(cases), _Fake("empty"), tmp_path / "g", tmp_path / "r", "fake")
    assert res[0].status == "EMPTY_OUTPUT"


def test_generator_llm_error(cases, tmp_path):
    # Kalıcı quota: yeniden denemeler tükenince LLM_ERROR (gerçekten uyumadan test edilir).
    res = generator.run(_one_case(cases), _Fake("error"), tmp_path / "g", tmp_path / "r", "fake",
                        max_retries=2, sleep=lambda *_: None)
    assert res[0].status == "LLM_ERROR" and "quota" in res[0].error


def test_generator_retry_then_success(cases, tmp_path):
    """Geçici quota sonrası başarı: retry mantığı doğrulanır (no-op sleep)."""
    class _Flaky:
        api_key_env = "GROQ_API_KEY"
        def __init__(self):
            self.calls = 0
        def complete(self, system, user):
            self.calls += 1
            if self.calls == 1:
                raise LLMError("quota", "Rate limit... try again in 0.1s")
            import re as _re
            tname = _re.search(r"test_[a-z0-9_]+", user).group(0)
            return LLMResponse(
                text=f"```python\nimport pytest\npytestmark = pytest.mark.django_db\n\n\ndef {tname}(seeded_db, api_client):\n    assert True\n```",
                prompt_tokens=1, completion_tokens=1, latency_ms=1)
    res = generator.run(_one_case(cases), _Flaky(), tmp_path / "g", tmp_path / "r", "fake",
                        sleep=lambda *_: None)
    assert res[0].status == "GENERATED"


_JUNIT = """<?xml version="1.0"?>
<testsuites><testsuite>
<testcase name="test_sc_upd_001"/>
<testcase name="test_sc_flw_001"><failure message="x"/></testcase>
<testcase name="test_sc_flw_003"/>
<testcase name="test_sc_aut_001"><failure message="y"/></testcase>
</testsuite></testsuites>
"""


def test_classify_taxonomy(cases, tmp_path):
    ids = ["SC-UPD-001", "SC-FLW-001", "SC-FLW-003", "SC-AUT-001"]
    case_list = [cases[i] for i in ids]
    gen = [GenerationOutcome(scenario_id=i, status="GENERATED", test_name=make_test_name(i),
                             http_method=cases[i].http_method, model="fake", prompt_version="pytest_v1")
           for i in ids]
    junit = tmp_path / "j.xml"
    junit.write_text(_JUNIT, encoding="utf-8")
    result = {e.scenario_id: e.classification for e in runner.classify(case_list, gen, junit)}
    assert result["SC-UPD-001"] == "PASSED"
    assert result["SC-FLW-001"] == "KNOWN_FLAW_DETECTED"
    assert result["SC-FLW-003"] == "KNOWN_FLAW_NOT_DETECTED"
    assert result["SC-AUT-001"] == "APPLICATION_MISMATCH"
