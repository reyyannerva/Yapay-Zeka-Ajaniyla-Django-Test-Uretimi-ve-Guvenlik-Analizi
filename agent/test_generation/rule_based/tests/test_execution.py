"""Uçtan uca: üretilen testleri kontrollü fixture'da çalıştırma ve sınıflandırma — H3-04 / Issue #30.

Üretilen paket geçici dizine yazılır ve ayrı bir pytest sürecinde (kendi pytest.ini'si ile) çalıştırılır.
"""
from __future__ import annotations

import dataclasses
import json
import shutil

import pytest
from conftest import EXP, REPO, TARGET_APP

from agent.test_generation.rule_based import runner
from agent.test_generation.rule_based.generator import generate, relative_pythonpath, write_output

pytest.importorskip("django")
pytest.importorskip("pytest_django")
pytest.importorskip("rest_framework")


def _materialize(tmp_path, cases, summary, users, resources, diags=None, name="gen"):
    out = tmp_path / name
    res = generate(cases, summary, users, resources, {"x": "0"}, diags, relative_pythonpath(out, TARGET_APP))
    write_output(res, out)
    return res, out


@pytest.fixture(scope="module")
def suite(tmp_path_factory, references, summary, users, resources):
    tmp = tmp_path_factory.mktemp("h304")
    cases, diags = references
    res, out = _materialize(tmp, cases, summary, users, resources, diags)
    raw, log, code = runner.run(out, tmp / "suite.xml")
    return res, out, raw, runner.classify_all(res.plans, raw), tmp


def test_every_generated_test_is_collected(suite):
    res, out, *_ = suite
    nodes, log = runner.collect(out)
    assert len(nodes) == len(res.plans), log


def test_no_generation_errors_or_application_mismatches(suite):
    *_, results, _ = suite
    bad = [(r.scenario_id, r.classification, r.evidence) for r in results
           if r.classification in ("GENERATION_ERROR", "APPLICATION_MISMATCH")]
    assert not bad


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
def test_each_method_has_a_passing_generated_test(suite, method):
    *_, results, _ = suite
    assert any(r.http_method == method and r.pytest_outcome == "passed" for r in results)


def test_known_status_flaws_are_detected_and_still_failed(suite, raw_gt):
    *_, results, _ = suite
    by = {r.scenario_id: r for r in results}
    for rec in raw_gt["records"]:
        if not rec["is_known_flaw"]:
            continue
        r = by[rec["scenario_id"]]
        if rec["security_finding"]["deviation_kind"] == "status":
            assert r.pytest_outcome == "failed" and r.classification == "KNOWN_FLAW_DETECTED"
            assert r.observed_status == rec["security_finding"]["observed_flawed_status"]
        else:
            assert r.pytest_outcome == "passed" and r.classification == "KNOWN_FLAW_NOT_DETECTED"


def test_non_flaw_scenarios_pass(suite, raw_gt):
    *_, results, _ = suite
    flaws = {r["scenario_id"] for r in raw_gt["records"] if r["is_known_flaw"]}
    assert all(r.pytest_outcome == "passed" for r in results if r.scenario_id not in flaws)


def test_isolation_single_and_reverse_order(suite):
    res, out, raw, _, tmp = suite
    subset = [p for p in res.plans if p.scenario_id in
              ("SC-DEL-001", "SC-DEL-002", "SC-UPD-001", "SC-UPD-003", "SC-RET-001", "SC-CRT-001", "SC-LST-003")]
    iso = runner.isolation_check(out, subset, raw, tmp)
    assert iso["isolated"], iso


def test_tampered_route_is_classified_as_generation_error(tmp_path, cases, summary, users, resources):
    res, out = _materialize(tmp_path, [cases["SC-UPD-001"], cases["SC-RET-001"]], summary, users, resources)
    put = out / "test_put_generated.py"
    put.write_text(put.read_text(encoding="utf-8").replace("'article-detail'", "'article-detail-x'"), encoding="utf-8")
    get = out / "test_get_generated.py"
    get.write_text(get.read_text(encoding="utf-8").replace("kwargs={'pk': 1}", "kwargs={'pk': 2}"), encoding="utf-8")
    raw, *_ = runner.run(out, tmp_path / "t.xml")
    by = {r.scenario_id: r for r in runner.classify_all(res.plans, raw)}
    assert by["SC-UPD-001"].classification == "GENERATION_ERROR"   # NoReverseMatch
    assert by["SC-RET-001"].classification == "GENERATION_ERROR" and by["SC-RET-001"].check == "route"


def test_broken_fixture_setup_is_generation_error(tmp_path, cases, summary, users, resources):
    res, out = _materialize(tmp_path, [cases["SC-UPD-001"]], summary, users, resources)
    conf = out / "conftest.py"
    conf.write_text(conf.read_text(encoding="utf-8").replace("['users', 'articles']", "['nope']"), encoding="utf-8")
    raw, *_ = runner.run(out, tmp_path / "t.xml")
    r = runner.classify_all(res.plans, raw)[0]
    assert r.pytest_outcome == "error" and r.classification == "GENERATION_ERROR"


def test_reference_mismatch_is_application_mismatch(tmp_path, cases, summary, users, resources):
    wrong = dataclasses.replace(cases["SC-UPD-001"], expected_status=204)
    res, out = _materialize(tmp_path, [wrong], summary, users, resources)
    raw, *_ = runner.run(out, tmp_path / "t.xml")
    r = runner.classify_all(res.plans, raw)[0]
    assert (r.pytest_outcome, r.classification, r.observed_status) == ("failed", "APPLICATION_MISMATCH", 200)


def test_side_effect_violation_is_detected(tmp_path, cases, summary, users, resources):
    # Gerçek uygulamada SC-UPD-001 başlığı günceller; beklenen değeri değiştirip yan etki kontrolünü sınarız.
    res, out = _materialize(tmp_path, [cases["SC-UPD-001"]], summary, users, resources)
    put = out / "test_put_generated.py"
    src = put.read_text(encoding="utf-8")
    assert "assert observed == {'body': 'örnek içerik', 'title': 'Örnek Başlık'}" in src
    put.write_text(src.replace("assert observed == {'body': 'örnek içerik', 'title': 'Örnek Başlık'}",
                               "assert observed == {'body': 'örnek içerik', 'title': 'Başka'}"), encoding="utf-8")
    raw, *_ = runner.run(out, tmp_path / "t.xml")
    r = runner.classify_all(res.plans, raw)[0]
    assert r.check == "side_effect" and r.classification == "APPLICATION_MISMATCH"


@pytest.mark.parametrize("raw,flaw,expected", [
    ({"outcome": "passed", "message": ""}, False, "PASSED"),
    ({"outcome": "failed", "message": "[H304] scenario=S check=status expected=403 observed=200 | x"}, True,
     "KNOWN_FLAW_DETECTED"),
    ({"outcome": "failed", "message": "[H304] scenario=S check=status expected=403 observed=500 | x"}, True,
     "APPLICATION_MISMATCH"),
    ({"outcome": "failed", "message": "[H304] scenario=S check=status expected=403 observed=200 | x"}, False,
     "APPLICATION_MISMATCH"),
    ({"outcome": "failed", "message": "[H304] scenario=S check=route expected=/a/ observed=/b/ | x"}, False,
     "GENERATION_ERROR"),
    ({"outcome": "failed", "message": "NameError: name 'x' is not defined"}, False, "GENERATION_ERROR"),
    ({"outcome": "error", "message": "fixture 'seeded_db' not found"}, False, "GENERATION_ERROR"),
    (None, False, "GENERATION_ERROR"),
])
def test_classification_rules(suite, raw, flaw, expected):
    res = suite[0]
    base = next(p for p in res.plans if p.scenario_id == ("SC-FLW-001" if flaw else "SC-UPD-001"))
    plan = dataclasses.replace(base, is_known_flaw=flaw, security_finding=base.security_finding if flaw else None)
    assert runner.classify(plan, raw).classification == expected


def test_committed_generated_suite_matches_fresh_generation(references, summary, users, resources):
    committed = EXP / "generated_tests"
    rep = json.loads((EXP / "reports" / "generation_report.json").read_text(encoding="utf-8"))
    cases, diags = references
    res = generate(cases, summary, users, resources, rep["inputs_sha256"], diags,
                   relative_pythonpath(committed, TARGET_APP))
    for name, src in {**res.modules, **res.support_files}.items():
        assert (committed / name).read_text(encoding="utf-8") == src, f"{name} güncel değil; yeniden üretin"
    stale = [p.name for p in committed.glob("test_*_generated.py") if p.name not in res.modules]
    assert not stale


def test_committed_input_digests_match_current_inputs():
    from agent.test_generation.rule_based.generator import sha256
    rep = json.loads((EXP / "reports" / "generation_report.json").read_text(encoding="utf-8"))
    assert {p: sha256(REPO / p) for p in rep["inputs_sha256"]} == rep["inputs_sha256"]


def test_committed_generated_suite_runs_in_place(tmp_path):
    out = tmp_path / "copy"
    shutil.copytree(EXP / "generated_tests", out, ignore=shutil.ignore_patterns("__pycache__"))
    ini = out / "pytest.ini"
    ini.write_text(ini.read_text(encoding="utf-8").replace(
        "../../../benchmarks/drf_fixtures/sample_app", relative_pythonpath(out, TARGET_APP)), encoding="utf-8")
    nodes, log = runner.collect(out)
    assert len(nodes) >= 5, log


@pytest.mark.parametrize("dirname", ["copy", "json", "tests"])
def test_generated_suite_does_not_depend_on_output_directory_name(tmp_path, cases, summary, users, resources,
                                                                  dirname):
    res, out = _materialize(tmp_path, [cases["SC-RET-001"]], summary, users, resources, name=dirname)
    assert not (out / "__init__.py").exists()
    nodes, log = runner.collect(out)
    assert len(nodes) == 1, log


FAULTS = [
    # Nesne düzeyi yetkilendirme kaldırılırsa sahip-olmayan PUT/PATCH/DELETE senaryoları yakalanmalı.
    ("authz", "catalog/permissions.py",
     [("return obj.owner_id == request.user.id or request.user.is_staff", "return True")],
     {"SC-AUZ-001", "SC-AUZ-002", "SC-AUZ-003"}),
    # Başlık zorunluluğu ve boş başlık kontrolü kaldırılırsa girdi doğrulama senaryoları yakalanmalı.
    # (Yalnızca validate_title'ı devre dışı bırakmak eşdeğer mutanttır: DRF CharField boşlukları kırpar ve
    # boş değeri zaten reddeder; bu durumda hiçbir testin başarısız olmaması doğrudur.)
    ("input", "catalog/serializers.py",
     [('read_only_fields = ["id", "owner", "created_at"]',
       'read_only_fields = ["id", "owner", "created_at"]\n        extra_kwargs = {"title": {"required": False, '
       '"allow_blank": True}}'),
      ('if not value.strip():\n            raise serializers.ValidationError("Başlık boş olamaz.")', 'pass')],
     {"SC-INP-001", "SC-INP-002"}),
    # PATCH, gövdede olmayan alanı (body) silerse kısmi güncelleme yan etki kontrolü yakalamalı.
    ("partial", "catalog/views.py",
     [("    def perform_create(self, serializer):",
       "    def perform_update(self, serializer):\n"
       "        serializer.save(body='') if self.request.method == 'PATCH' else serializer.save()\n\n"
       "    def perform_create(self, serializer):")],
     {"SC-UPD-003", "SC-UPD-004"}),
]


def _mutated_app(tmp_path, target_file, replacements):
    app = tmp_path / "app"
    shutil.copytree(TARGET_APP, app, ignore=shutil.ignore_patterns("__pycache__", "*.sqlite3"))
    f = app / target_file
    src = f.read_text(encoding="utf-8")
    for old, new in replacements:
        assert old in src, old
        src = src.replace(old, new)
    f.write_text(src, encoding="utf-8")
    return app


@pytest.mark.parametrize("name,target_file,replacements,expected_failures", FAULTS, ids=[f[0] for f in FAULTS])
def test_generated_suite_detects_injected_faults(tmp_path, references, summary, users, resources,
                                                  name, target_file, replacements, expected_failures):
    """Hedef uygulamanın GEÇİCİ bir kopyasına hata enjekte edilir; depodaki uygulama değişmez."""
    app = _mutated_app(tmp_path, target_file, replacements)
    cases, diags = references
    out = tmp_path / "gen"
    res = generate(cases, summary, users, resources, {"x": "0"}, diags, relative_pythonpath(out, app))
    write_output(res, out)
    ok, msg = runner.check_environment(out)
    assert ok, msg
    raw, *_ = runner.run(out, tmp_path / "t.xml")
    results = runner.classify_all(res.plans, raw)
    mismatches = {r.scenario_id for r in results if r.classification == "APPLICATION_MISMATCH"}
    assert expected_failures <= mismatches, (expected_failures, mismatches)
    assert not [r for r in results if r.classification == "GENERATION_ERROR"]


def test_broken_target_app_is_environment_error_not_generator_error(tmp_path, cases, summary, users, resources):
    app = _mutated_app(tmp_path, "catalog/serializers.py", [("class Meta:", "class Meta(:")])
    out = tmp_path / "gen"
    res = generate([cases["SC-UPD-001"]], summary, users, resources, {"x": "0"}, None,
                   relative_pythonpath(out, app))
    write_output(res, out)
    ok, msg = runner.check_environment(out)
    assert not ok and "SyntaxError" in msg
    raw, *_ = runner.run(out, tmp_path / "t.xml")
    r = runner.classify_all(res.plans, raw, msg)[0]
    assert r.classification == "ENVIRONMENT_ERROR"


def test_real_target_environment_loads(suite):
    ok, msg = runner.check_environment(suite[1])
    assert ok, msg
