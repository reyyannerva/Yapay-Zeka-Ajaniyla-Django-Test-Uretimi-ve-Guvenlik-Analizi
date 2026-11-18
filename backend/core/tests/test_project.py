import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from core.models import AnalysisRun, Project, ReferenceRequirement

from .conftest import assert_integrity, make_project, make_requirement, make_run, sha

pytestmark = pytest.mark.django_db


def test_create_and_read_back(user):
    p = make_project(user, name="Mağaza", description="örnek")
    got = Project.objects.get(pk=p.pk)
    assert (got.owner, got.name, got.validation_status, got.validation_report) == (user, "Mağaza", "PENDING", {})
    assert got.created_at and got.updated_at and str(got) == "Mağaza"
    assert list(user.projects.all()) == [got]


def test_archive_project_requires_archive_and_hash(user):
    p = Project.objects.create(owner=user, name="arsiv", source_type="ARCHIVE",
                               source_archive="project_archives/2026/11/a.zip", archive_sha256=sha())
    assert p.source_directory is None
    assert_integrity(lambda: Project.objects.create(owner=user, name="eksik", source_type="ARCHIVE"),
                     "ck_projects_archive_source_present")


def test_directory_project_rules(user):
    assert_integrity(lambda: make_project(user, source_directory=None), "ck_projects_directory_source_present")
    assert_integrity(lambda: make_project(user, source_directory="../etc"), "ck_projects_source_directory_relative")
    assert_integrity(lambda: make_project(user, source_directory="/etc"), "ck_projects_source_directory_relative")


@pytest.mark.parametrize("field,value,constraint", [
    ("name", "", "ck_projects_name_not_blank"),
    ("source_type", "GIT", "ck_projects_source_type_valid"),
    ("validation_status", "OK", "ck_projects_validation_status_valid"),
])
def test_db_rejects_invalid_values(user, field, value, constraint):
    assert_integrity(lambda: make_project(user, **{field: value}), constraint)


def test_archive_sha256_format(user):
    assert_integrity(lambda: Project.objects.create(owner=user, name="a", source_type="ARCHIVE",
                                                    source_archive="a.zip", archive_sha256="ABC"),
                     "ck_projects_archive_sha256_format")


def test_unique_name_per_owner_but_not_globally(user):
    make_project(user, name="ayni")
    assert_integrity(lambda: make_project(user, name="ayni"), "uq_projects_owner_name")
    other = get_user_model().objects.create_user(username="baska")
    assert make_project(other, name="ayni").pk


def test_owner_required(db):
    assert_integrity(lambda: Project.objects.create(name="sahipsiz", source_type="ALLOWED_DIRECTORY",
                                                    source_directory="x"))


def test_model_validation_also_rejects_invalid_choice(user):
    p = Project(owner=user, name="x", source_type="GIT", source_directory="x")
    with pytest.raises(ValidationError):
        p.full_clean()


def test_deleting_user_cascades_to_projects_and_children(user):
    p = make_project(user)
    make_run(p)
    make_requirement(p)
    user.delete()
    assert not Project.objects.exists()
    assert not AnalysisRun.objects.exists() and not ReferenceRequirement.objects.exists()
