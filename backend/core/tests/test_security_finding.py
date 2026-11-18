import pytest

from core.models import SecurityFinding

from .conftest import assert_integrity, at, make_endpoint, make_execution, make_test, sha

pytestmark = pytest.mark.django_db


def make_finding(run, **kw):
    data = dict(analysis_run=run, source="AUTH_TEST", rule_id="BOLA_UPDATE", severity="HIGH",
                title="Sahip olmayan kullanıcı güncelleyebiliyor", fingerprint=sha(kw.get("rule_id", "f")))
    data.update(kw)
    return SecurityFinding.objects.create(**data)


def test_create_with_classification_evidence_and_relations(run):
    ep = make_endpoint(run, http_method="PUT")
    ex = make_execution(make_test(run), status="FAIL", started_at=at(0), finished_at=at(1))
    details = {"schema_version": 1, "owasp": "API1:2023", "expected_status": 403, "observed_status": 200}
    f = make_finding(run, endpoint=ep, test_execution=ex, classification="VERIFIED", details=details,
                     evidence_excerpt="PUT /api/articles/1/ -> 200", file_path="catalog/insecure.py", line_number=12)
    got = SecurityFinding.objects.get(pk=f.pk)
    assert (got.severity, got.classification, got.details, got.endpoint, got.test_execution) == (
        "HIGH", "VERIFIED", details, ep, ex)
    assert list(run.security_findings.all()) == [got] and list(ex.security_findings.all()) == [got]


def test_default_classification_is_possible(run):
    assert make_finding(run).classification == "POSSIBLE"


@pytest.mark.parametrize("kw,constraint", [
    ({"source": "ZAP"}, "ck_security_findings_source_valid"),
    ({"severity": "CRITICAL"}, "ck_security_findings_severity_valid"),
    ({"classification": "CONFIRMED"}, "ck_security_findings_classification_valid"),
    ({"rule_id": ""}, "ck_security_findings_rule_id_not_blank"),
    ({"title": ""}, "ck_security_findings_title_not_blank"),
    ({"file_path": "/etc/passwd"}, "ck_security_findings_file_path_relative"),
    ({"file_path": "a/../../b"}, "ck_security_findings_file_path_relative"),
    ({"line_number": 0}, "ck_security_findings_line_number_positive"),
    ({"fingerprint": "abc"}, "ck_security_findings_fingerprint_format"),
])
def test_db_constraints(run, kw, constraint):
    assert_integrity(lambda: make_finding(run, **kw), constraint)


def test_fingerprint_unique_per_run(run):
    make_finding(run, fingerprint=sha("same"))
    assert_integrity(lambda: make_finding(run, fingerprint=sha("same")), "uq_security_findings_run_fingerprint")


def test_execution_delete_keeps_finding_run_delete_removes_it(run):
    ex = make_execution(make_test(run))
    f = make_finding(run, test_execution=ex)
    ex.delete()
    f.refresh_from_db()
    assert f.test_execution is None
    run.delete()
    assert not SecurityFinding.objects.exists()
