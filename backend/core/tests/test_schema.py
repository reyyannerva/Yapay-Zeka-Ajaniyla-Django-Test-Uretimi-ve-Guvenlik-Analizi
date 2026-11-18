"""Migration ve şema doğrulaması (PostgreSQL)."""
from io import StringIO

import pytest
from django.apps import apps
from django.core.management import call_command
from django.db import connection

APP_TABLES = {"projects", "reference_requirements", "analysis_runs", "endpoints", "generated_tests",
              "test_executions", "security_findings", "reports", "llm_calls"}
CORE_SEVEN = ["auth.User", "core.Project", "core.ReferenceRequirement", "core.AnalysisRun", "core.GeneratedTest",
              "core.TestExecution", "core.SecurityFinding"]


def test_database_is_postgresql(db):
    assert connection.vendor == "postgresql"
    with connection.cursor() as cur:
        cur.execute("SHOW server_version_num")
        assert int(cur.fetchone()[0]) >= 140000


def test_seven_core_models_exist():
    for label in CORE_SEVEN:
        assert apps.get_model(label) is not None


def test_no_pending_migrations(db):
    out = StringIO()
    call_command("makemigrations", "--check", "--dry-run", stdout=out)
    assert "No changes detected" in out.getvalue()


def test_all_application_tables_exist(db):
    assert APP_TABLES <= set(connection.introspection.table_names())


def test_axes_tables_exist(db):
    tables = set(connection.introspection.table_names())
    assert {"axes_accessattempt", "axes_accessattemptexpiration", "axes_accessfailurelog", "axes_accesslog"} <= tables


def _constraints(table):
    with connection.cursor() as cur:
        return connection.introspection.get_constraints(cur, table)


def test_named_constraints_exist_in_database(db):
    names = {n for t in APP_TABLES for n in _constraints(t)}
    for model in apps.get_app_config("core").get_models():
        for c in model._meta.constraints:
            assert c.name in names, c.name
        for i in model._meta.indexes:
            assert i.name in names, i.name


def test_json_columns_are_jsonb(db):
    with connection.cursor() as cur:
        cur.execute("SELECT table_name, column_name FROM information_schema.columns "
                    "WHERE table_schema = current_schema() AND data_type = 'jsonb'")
        cols = set(cur.fetchall())
    assert ("reference_requirements", "specification") in cols
    assert ("analysis_runs", "processing_metadata") in cols and ("test_executions", "result_details") in cols
    assert len([c for c in cols if c[0] in APP_TABLES]) == 11


@pytest.mark.django_db(transaction=True)
def test_core_migrations_roll_back_and_reapply_cleanly():
    call_command("migrate", "core", "zero", verbosity=0)
    assert "projects" not in connection.introspection.table_names()
    call_command("migrate", "core", verbosity=0)
    assert APP_TABLES <= set(connection.introspection.table_names())
