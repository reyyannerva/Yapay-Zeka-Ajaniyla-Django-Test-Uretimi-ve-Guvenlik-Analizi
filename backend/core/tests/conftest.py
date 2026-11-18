"""Ortak test yardımcıları — H4-01 / Issue #33. Testler geçici PostgreSQL test veritabanında çalışır."""
import hashlib
from datetime import timedelta
from itertools import count

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from core.models import AnalysisRun, Endpoint, GeneratedTest, Project, ReferenceRequirement, TestExecution

_seq = count(1)
T0 = timezone.now().replace(microsecond=0)


def sha(text: str = "x") -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def at(seconds: int):
    """Sabit başlangıca göre zaman damgası (duvar saatine bağımlı olmayan testler)."""
    return T0 + timedelta(seconds=seconds)


def assert_integrity(callable_, constraint: str | None = None):
    """Veritabanının işlemi reddettiğini doğrular; full_clean() kullanılmaz (kısıt veritabanındadır)."""
    with pytest.raises(IntegrityError) as exc:
        with transaction.atomic():
            callable_()
    if constraint:
        assert constraint in str(exc.value), str(exc.value)


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username=f"u{next(_seq)}", password="Gizli-Parola-123")


@pytest.fixture
def project(user):
    return make_project(user)


def make_project(user, **kw):
    data = dict(owner=user, name=f"proje-{next(_seq)}", source_type=Project.SourceType.ALLOWED_DIRECTORY,
                source_directory="samples/shop")
    data.update(kw)
    return Project.objects.create(**data)


@pytest.fixture
def run(project):
    return make_run(project)


def make_run(project, **kw):
    data = dict(project=project, method=AnalysisRun.Method.RULE_BASED)
    data.update(kw)
    return AnalysisRun.objects.create(**data)


def make_requirement(project, **kw):
    data = dict(project=project, requirement_code=f"ACC-{next(_seq)}", category="ACCESS_RULE",
                title="Sipariş silme", expected_result="anonim 401, staff 204",
                specification={"schema_version": 1, "endpoint": "/api/orders/<int:pk>/", "method": "DELETE",
                               "expected_status_by_role": {"anonymous": 401, "staff": 204}})
    data.update(kw)
    return ReferenceRequirement.objects.create(**data)


def make_endpoint(run, **kw):
    data = dict(analysis_run=run, path=f"/api/items/{next(_seq)}/", http_method="GET", view_name="items.views.Item")
    data.update(kw)
    return Endpoint.objects.create(**data)


def make_test(run, **kw):
    n = next(_seq)
    data = dict(analysis_run=run, test_module=f"test_mod_{n}.py", test_name=f"test_case_{n}",
                generation_method=GenerationMethod.RULE_BASED, source_code="def test_x():\n    assert True\n",
                code_sha256=sha(str(n)))
    data.update(kw)
    return GeneratedTest.objects.create(**data)


GenerationMethod = GeneratedTest.GenerationMethod


def make_execution(test, **kw):
    data = dict(generated_test=test, attempt_number=1)
    data.update(kw)
    return TestExecution.objects.create(**data)
