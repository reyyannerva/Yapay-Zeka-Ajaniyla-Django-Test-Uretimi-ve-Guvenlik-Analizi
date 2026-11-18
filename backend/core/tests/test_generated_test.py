import pytest

from core.models import Endpoint, GeneratedTest

from .conftest import assert_integrity, make_endpoint, make_project, make_run, make_test, sha

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("method", ["RULE_BASED", "LLM"])
def test_create_with_generation_method_and_metadata(run, method):
    meta = {"schema_version": 1, "prompt_template_version": "pytest_v1", "fallback": {"used": False}}
    t = make_test(run, generation_method=method, generation_metadata=meta, requirement_code="ACC-1",
                  role="anonymous", expected_status=401, is_security_test=True)
    got = GeneratedTest.objects.get(pk=t.pk)
    assert (got.generation_method, got.generation_metadata, got.analysis_run) == (method, meta, run)
    assert got.validation_status == "PENDING" and got.repair_count == 0 and got.validation_errors == []
    assert list(run.generated_tests.all()) == [got]


def test_validation_errors_json(run):
    errors = [{"type": "SyntaxError", "message": "invalid syntax", "line": 7}]
    t = make_test(run, validation_status="INVALID_SYNTAX", validation_errors=errors)
    assert GeneratedTest.objects.get(pk=t.pk).validation_errors == errors


@pytest.mark.parametrize("kw,constraint", [
    ({"generation_method": "MANUAL"}, "ck_generated_tests_method_valid"),
    ({"test_module": "tests.py"}, "ck_generated_tests_module_format"),
    ({"test_name": "check_x"}, "ck_generated_tests_name_format"),
    ({"expected_status": 99}, "ck_generated_tests_expected_status_range"),
    ({"validation_status": "OK"}, "ck_generated_tests_validation_status_valid"),
    ({"repair_count": 2}, "ck_generated_tests_repair_count_range"),
    ({"code_sha256": "z" * 64}, "ck_generated_tests_code_sha256_format"),
])
def test_db_constraints(run, kw, constraint):
    assert_integrity(lambda: make_test(run, **kw), constraint)


def test_unique_module_and_name_per_run(run):
    make_test(run, test_module="test_a.py", test_name="test_one")
    assert_integrity(lambda: make_test(run, test_module="test_a.py", test_name="test_one"),
                     "uq_generated_tests_run_module_name")


def test_same_test_name_allowed_in_another_run(user):
    a, b = make_run(make_project(user)), make_run(make_project(user))
    make_test(a, test_module="test_a.py", test_name="test_one", code_sha256=sha("a"))
    assert make_test(b, test_module="test_a.py", test_name="test_one", code_sha256=sha("a")).pk


def test_requires_analysis_run(db):
    assert_integrity(lambda: GeneratedTest.objects.create(test_module="test_a.py", test_name="test_a",
                                                          generation_method="LLM", source_code="x",
                                                          code_sha256=sha()))


def test_endpoint_delete_sets_null_and_run_delete_cascades(run):
    ep = make_endpoint(run)
    t = make_test(run, endpoint=ep)
    ep.delete()
    t.refresh_from_db()
    assert t.endpoint is None
    run.delete()
    assert not GeneratedTest.objects.exists() and not Endpoint.objects.exists()
