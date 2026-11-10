"""Kod üretimi, sözdizimi doğrulaması ve determinizm testleri — H3-04 / Issue #30."""
from __future__ import annotations

import ast
import dataclasses
import random

import pytest

from agent.test_generation.rule_based import codegen
from agent.test_generation.rule_based.contracts import Code, Status
from agent.test_generation.rule_based.generator import generate
from agent.test_generation.rule_based.validation import validate_module, validate_suite

DIGESTS = {"input.json": "0" * 64}


@pytest.fixture(scope="module")
def result(references, summary, users, resources):
    cases, diags = references
    return generate(cases, summary, users, resources, DIGESTS, diags)


def test_all_real_scenarios_generate(result, references):
    assert result.counts()["GENERATED"] == len(references[0])
    assert set(result.modules) == {f"test_{m}_generated.py" for m in ("get", "post", "put", "patch", "delete")}


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
def test_each_method_module_is_valid_python(result, method):
    name = f"test_{method.lower()}_generated.py"
    src = result.modules[name]
    tree = ast.parse(src)
    compile(src, name, "exec")
    funcs = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
    planned = sorted(p.test_name for p in result.plans if p.http_method == method)
    assert sorted(funcs) == planned and len(funcs) >= 1


def test_each_test_carries_reference_status_and_scenario_id(result):
    trees = {n: ast.parse(s) for n, s in result.modules.items()}
    for p in result.plans:
        fn = next(f for f in trees[p.module].body if isinstance(f, ast.FunctionDef) and f.name == p.test_name)
        status_asserts = [a for a in ast.walk(fn) if isinstance(a, ast.Assert)
                          and isinstance(a.test, ast.Compare) and ast.unparse(a.test.left) == "response.status_code"]
        assert len(status_asserts) == 1
        assert ast.literal_eval(status_asserts[0].test.comparators[0]) == p.expected_status
        assert p.scenario_id in ast.unparse(fn)


def test_patch_checks_partial_semantics_and_put_full(result):
    patch = next(p for p in result.plans if p.scenario_id == "SC-UPD-003")
    put = next(p for p in result.plans if p.scenario_id == "SC-UPD-001")
    patch_src = ast.unparse(next(f for f in ast.parse(result.modules[patch.module]).body
                                 if isinstance(f, ast.FunctionDef) and f.name == patch.test_name))
    put_src = ast.unparse(next(f for f in ast.parse(result.modules[put.module]).body
                               if isinstance(f, ast.FunctionDef) and f.name == put.test_name))
    assert "api_client.patch(" in patch_src and "{**before" in patch_src
    assert "api_client.put(" in put_src and "{**before" not in put_src and "observed == " in put_src


def test_delete_success_checks_resource_removed(result):
    p = next(p for p in result.plans if p.scenario_id == "SC-DEL-001")
    fn = next(f for f in ast.parse(result.modules[p.module]).body if isinstance(f, ast.FunctionDef)
              and f.name == p.test_name)
    assert "assert after is None" in ast.unparse(fn)


def test_generation_is_deterministic_and_order_independent(references, summary, users, resources, result):
    cases, diags = references
    shuffled = list(cases)
    random.Random(7).shuffle(shuffled)
    again = generate(shuffled, summary, users, resources, DIGESTS, diags)
    assert again.modules == result.modules and again.support_files == result.support_files


def test_unsafe_text_is_embedded_as_literal(cases, summary, users, resources):
    nasty = 'Tırnak """ ve \'tek\' \\ ters eğik çizgi\n yeni satır; import os; os.system("x")'
    case = dataclasses.replace(cases["SC-UPD-001"], expected_behavior=nasty,
                               request_input={"title": nasty, "body": "x"})
    res = generate([case], summary, users, resources, DIGESTS)
    src = res.modules["test_put_generated.py"]
    tree = ast.parse(src)
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "system"]
    assert not calls, "Veri, çalıştırılabilir koda dönüşmemeli"
    assert nasty in {c.value for c in ast.walk(tree) if isinstance(c, ast.Constant)}


@pytest.mark.parametrize("value", [object(), {1: "a"}, {"a": {1, 2}}])
def test_literal_rejects_unsupported_values(value):
    with pytest.raises(codegen.LiteralError):
        codegen.literal(value)


def test_template_placeholders_must_be_used():
    with pytest.raises(codegen.LiteralError):
        codegen.stmts("x = 1", UNUSED=2)


def test_validation_detects_syntax_error_missing_and_duplicate_tests(result):
    plans = [p for p in result.plans if p.module == "test_get_generated.py"]
    broken = validate_module("test_get_generated.py", "def test_x(:\n", plans)
    assert broken[-1].code is Code.SYNTAX_ERROR
    src = result.modules["test_get_generated.py"]
    first = plans[0].test_name
    dup = src + f"\n\ndef {first}(seeded_db, api_client):\n    pass\n"
    codes = {d.code for d in validate_module("test_get_generated.py", dup, plans)}
    assert Code.DUPLICATE_TEST_NAME in codes
    missing = validate_module("test_get_generated.py", src.replace(f"def {first}(", "def renamed_fn("), plans)
    assert Code.TRACEABILITY_ERROR in {d.code for d in missing}
    assert validate_module("bad_name.py", src, plans)[0].code is Code.TRACEABILITY_ERROR


def test_duplicate_plan_names_marked_as_generation_error(result):
    plans = list(result.plans)
    clone = dataclasses.replace(plans[0], scenario_id="SC-DUP-001")
    diags = validate_suite(result.modules, plans + [clone])
    assert Code.DUPLICATE_TEST_NAME in {d.code for d in diags}


def test_validation_failure_turns_scenarios_into_generation_error(references, summary, users, resources, monkeypatch):
    cases, diags = references
    monkeypatch.setattr(codegen, "build_module", lambda method, plans, digests: "def broken(:\n")
    res = generate(cases, summary, users, resources, DIGESTS, diags)
    assert any(d.code is Code.SYNTAX_ERROR for d in res.global_diagnostics)
    with pytest.raises(RuntimeError, match="dosyalar yazılmadı"):
        from agent.test_generation.rule_based.generator import write_output
        write_output(res, __import__("pathlib").Path("/nonexistent-should-not-be-created"))


def test_pytest_ini_values_are_validated():
    with pytest.raises(codegen.LiteralError):
        codegen.build_pytest_ini("config.settings\naddopts = -x", ".")
    with pytest.raises(codegen.LiteralError):
        codegen.build_pytest_ini("config.settings", "../a b")


def test_status_enum_values_match_repository_naming():
    assert [s.value for s in Status] == ["GENERATED", "UNSUPPORTED", "INVALID_INPUT", "MISSING_REFERENCE",
                                         "GENERATION_ERROR"]
