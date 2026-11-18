"""Proje sahipliği bazlı yetkilendirme testleri — H4-02 / Issue #34."""
from types import SimpleNamespace

import pytest
from rest_framework import generics
from rest_framework.test import APIRequestFactory, force_authenticate

from core.auth.permissions import IsProjectOwner, OwnedQuerysetMixin, owned_queryset, owning_user_id
from core.models import AnalysisRun, Endpoint, Project, SecurityFinding, TestExecution
from core.serializers import ReferenceRequirementSerializer

from .conftest import make_endpoint, make_execution, make_project, make_requirement, make_run, make_test, sha

pytestmark = pytest.mark.django_db


def _req(user):
    return SimpleNamespace(user=user)


# --- owned_queryset: kullanıcıya göre filtreleme ---
def test_owned_queryset_project(user, django_user_model):
    mine = make_project(user)
    other = make_project(django_user_model.objects.create_user(username="other1", password="x"))
    result = list(owned_queryset(Project.objects.all(), user))
    assert mine in result and other not in result


def test_owned_queryset_analysis_run(user, django_user_model):
    mine = make_run(make_project(user))
    other = make_run(make_project(django_user_model.objects.create_user(username="other2", password="x")))
    result = list(owned_queryset(AnalysisRun.objects.all(), user))
    assert mine in result and other not in result


# --- IsProjectOwner: nesne düzeyi ---
def test_is_project_owner_object_permission(user, django_user_model):
    project = make_project(user)
    stranger = django_user_model.objects.create_user(username="stranger", password="x")
    perm = IsProjectOwner()
    assert perm.has_object_permission(_req(user), None, project) is True
    assert perm.has_object_permission(_req(stranger), None, project) is False


def test_is_project_owner_resolves_fk_chain(user):
    # GeneratedTest → analysis_run → project → owner
    gentest = make_test(make_run(make_project(user)))
    assert owning_user_id(gentest) == user.id
    # ReferenceRequirement → project → owner
    req = make_requirement(make_project(user))
    assert owning_user_id(req) == user.id


def _finding(run, rule, fp):
    return SecurityFinding.objects.create(
        analysis_run=run, source=SecurityFinding.Source.AUTH_TEST, rule_id=rule,
        severity=SecurityFinding.Severity.HIGH, title="Bulgu", fingerprint=sha(fp),
    )


def test_ownership_protects_related_records(user, django_user_model):
    """İlişkili kayıtlar (test yürütme, güvenlik bulgusu, endpoint) de sahipliğe göre korunur (madde 11)."""
    run = make_run(make_project(user))
    mine = {
        TestExecution: make_execution(make_test(run)),
        Endpoint: make_endpoint(run),
        SecurityFinding: _finding(run, "R-1", "f1"),
    }
    other_run = make_run(make_project(django_user_model.objects.create_user(username="other4", password="x")))
    theirs = {
        TestExecution: make_execution(make_test(other_run)),
        Endpoint: make_endpoint(other_run),
        SecurityFinding: _finding(other_run, "R-2", "f2"),
    }
    for model in (TestExecution, Endpoint, SecurityFinding):
        result = list(owned_queryset(model.objects.all(), user))
        assert mine[model] in result and theirs[model] not in result
        assert owning_user_id(mine[model]) == user.id
        assert owning_user_id(theirs[model]) != user.id


# --- OwnedQuerysetMixin entegrasyonu: başkasının kaydı 404 ---
class _ProjectDetail(OwnedQuerysetMixin, generics.RetrieveAPIView):
    queryset = Project.objects.all()
    serializer_class = ReferenceRequirementSerializer  # yanıt şekli önemsiz; erişim kontrolü test ediliyor

    def get_serializer(self, *a, **k):
        class _S:
            data = {"ok": True}
        return _S()


def test_mixin_owner_can_retrieve(user):
    project = make_project(user)
    request = APIRequestFactory().get("/")
    force_authenticate(request, user=user)
    resp = _ProjectDetail.as_view()(request, pk=project.pk)
    assert resp.status_code == 200


def test_mixin_hides_others_record_as_404(user, django_user_model):
    others_project = make_project(django_user_model.objects.create_user(username="other3", password="x"))
    request = APIRequestFactory().get("/")
    force_authenticate(request, user=user)  # başkasının projesini istiyor
    resp = _ProjectDetail.as_view()(request, pk=others_project.pk)
    assert resp.status_code == 404  # queryset dışı → bilgi sızdırmadan 404


def test_mixin_requires_authentication(user):
    project = make_project(user)
    request = APIRequestFactory().get("/")  # kimlik yok
    resp = _ProjectDetail.as_view()(request, pk=project.pk)
    assert resp.status_code in (401, 403)
