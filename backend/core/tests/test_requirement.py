import pytest
from django.core.exceptions import ValidationError

from core.choices import HTTP_METHODS
from core.models import ReferenceRequirement
from core.serializers import ReferenceRequirementSerializer

from .conftest import assert_integrity, make_project, make_requirement

pytestmark = pytest.mark.django_db


def spec(method):
    return {"schema_version": 1, "endpoint": "/api/orders/", "method": method,
            "expected_status_by_role": {"anonymous": 401}}


def test_supported_methods_are_exactly_the_five():
    assert HTTP_METHODS == ("GET", "POST", "PUT", "PATCH", "DELETE")


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
def test_all_five_methods_stored_and_read_back(project, method):
    r = make_requirement(project, specification=spec(method))
    got = ReferenceRequirement.objects.get(pk=r.pk)
    assert got.http_method == method and got.specification["method"] == method
    got.full_clean()
    assert ReferenceRequirement.objects.filter(specification__method=method).count() == 1


@pytest.mark.parametrize("method", ["HEAD", "OPTIONS", "get", "TRACE", "", None, 1])
def test_db_rejects_invalid_method(project, method):
    assert_integrity(lambda: make_requirement(project, specification=spec(method)),
                     "ck_reference_requirements_access_rule_method")


def test_db_rejects_access_rule_without_method(project):
    assert_integrity(lambda: make_requirement(project, specification={"schema_version": 1}),
                     "ck_reference_requirements_access_rule_method")


@pytest.mark.parametrize("method", ["HEAD", "patch", None])
def test_model_validation_rejects_invalid_method(project, method):
    r = ReferenceRequirement(project=project, requirement_code="ACC-X", category="ACCESS_RULE", title="t",
                             expected_result="e", specification=spec(method))
    with pytest.raises(ValidationError) as exc:
        r.full_clean()
    assert "specification" in exc.value.message_dict


def test_role_and_deploy_rows_do_not_need_method(project):
    role = make_requirement(project, requirement_code="ROLE-STAFF", category="ROLE", title="staff",
                            expected_result="", specification={"schema_version": 1, "role": "staff"})
    dep = make_requirement(project, requirement_code="DEP-DEBUG", category="DEPLOY_EXPECTATION", title="DEBUG",
                           specification={"schema_version": 1, "setting": "DEBUG", "expected_value": False})
    assert role.http_method is None and dep.http_method is None


def test_unique_code_per_project(project, user):
    make_requirement(project, requirement_code="ACC-1")
    assert_integrity(lambda: make_requirement(project, requirement_code="ACC-1"),
                     "uq_reference_requirements_project_code")
    assert make_requirement(make_project(user), requirement_code="ACC-1").pk


@pytest.mark.parametrize("kw,constraint", [
    ({"requirement_code": "-bad"}, "ck_reference_requirements_code_format"),
    ({"category": "OTHER"}, "ck_reference_requirements_category_valid"),
    ({"source": "API"}, "ck_reference_requirements_source_valid"),
    ({"title": ""}, "ck_reference_requirements_title_not_blank"),
    ({"expected_result": ""}, "ck_reference_requirements_expected_result_not_blank"),
    ({"revision": 0}, "ck_reference_requirements_revision_positive"),
])
def test_db_constraints(project, kw, constraint):
    assert_integrity(lambda: make_requirement(project, **kw), constraint)


def test_foreign_key_integrity(db):
    assert_integrity(lambda: make_requirement(None))


# ---------------------------------------------------------------- serializer sözleşmesi

def payload(project, method, **kw):
    data = {"project": project.pk, "requirement_code": "ACC-API", "category": "ACCESS_RULE", "title": "t",
            "expected_result": "401", "specification": spec(method)}
    data.update(kw)
    return data


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
def test_serializer_accepts_five_methods(project, method):
    s = ReferenceRequirementSerializer(data=payload(project, method))
    assert s.is_valid(), s.errors
    assert s.save().http_method == method


@pytest.mark.parametrize("method", ["HEAD", "OPTIONS", "delete", ""])
def test_serializer_rejects_other_methods(project, method):
    s = ReferenceRequirementSerializer(data=payload(project, method))
    assert not s.is_valid()
    assert "method" in s.errors["specification"]


def test_serializer_validates_status_codes_and_expected_result(project):
    bad = payload(project, "GET")
    bad["specification"]["expected_status_by_role"] = {"anonymous": 99}
    assert not ReferenceRequirementSerializer(data=bad).is_valid()
    assert not ReferenceRequirementSerializer(data=payload(project, "GET", expected_result="")).is_valid()
