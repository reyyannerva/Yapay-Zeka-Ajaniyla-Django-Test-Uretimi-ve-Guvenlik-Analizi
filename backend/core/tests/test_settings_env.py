import pytest
from django.core.exceptions import ImproperlyConfigured

from config import env


def test_missing_required_variable_names_variable_not_value(monkeypatch):
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    with pytest.raises(ImproperlyConfigured, match="POSTGRES_PASSWORD"):
        env.database_config()


def test_database_config_from_environment(monkeypatch):
    for k, v in {"POSTGRES_DB": "d", "POSTGRES_USER": "u", "POSTGRES_PASSWORD": "p", "POSTGRES_HOST": "db",
                 "POSTGRES_PORT": "6543"}.items():
        monkeypatch.setenv(k, v)
    cfg = env.database_config()
    assert (cfg["ENGINE"], cfg["NAME"], cfg["USER"], cfg["HOST"], cfg["PORT"]) == (
        "django.db.backends.postgresql", "d", "u", "db", "6543")


@pytest.mark.parametrize("port", ["0", "70000", "abc"])
def test_invalid_port_rejected(monkeypatch, port):
    monkeypatch.setenv("POSTGRES_PORT", port)
    with pytest.raises(ImproperlyConfigured, match="POSTGRES_PORT"):
        env.env_int("POSTGRES_PORT", 5432, minimum=1, maximum=65535)


@pytest.mark.parametrize("raw,expected", [("true", True), ("1", True), ("false", False), ("0", False)])
def test_bool_parsing(monkeypatch, raw, expected):
    monkeypatch.setenv("X_FLAG", raw)
    assert env.env_bool("X_FLAG") is expected


def test_invalid_bool_rejected(monkeypatch):
    monkeypatch.setenv("X_FLAG", "belki")
    with pytest.raises(ImproperlyConfigured):
        env.env_bool("X_FLAG")


def test_check_database_command_succeeds(db):
    from io import StringIO

    from django.core.management import call_command
    out = StringIO()
    call_command("check_database", stdout=out)
    assert "Bağlantı başarılı" in out.getvalue() and "PostgreSQL" in out.getvalue()
