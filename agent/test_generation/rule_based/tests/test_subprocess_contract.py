"""Alt süreç yürütme sözleşmesi — H3-04 / Issue #30 Windows regresyonu.

Üretilen paket ayrı bir pytest sürecinde çalışır. Bu süreç geliştiricinin kabuğundaki Django/Python
ayarlarına bağlı olmamalı ve hedef uygulamanın kaynak ağacına yazmamalıdır:

* Dışarıda tanımlı ``DJANGO_SETTINGS_MODULE`` alt sürece sızmamalı (pytest-django ortam değişkenini
  ``pytest.ini`` değerinden önce kullanır).
* Alt süreç hedef uygulamaya bayt kodu (``__pycache__``) yazmamalı. Depo OneDrive gibi eşitlenen bir
  klasördeyken bu yazımlar eşitleme istemcisinin dosyalara erişmesine yol açar; ekip ortamında aynı dosyalar
  (``config/settings``, ``catalog/migrations/0001_initial``) aralıklı olarak içe aktarılamamıştır.

Testler gerçek alt süreç çalıştırır ve migration'ları uygulayan bir üretilmiş testi koşturur.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest
from conftest import TARGET_APP

from agent.test_generation.rule_based import runner
from agent.test_generation.rule_based import codegen
from agent.test_generation.rule_based.generator import (
    PythonpathError,
    generate,
    relative_pythonpath,
    write_output,
)

pytest.importorskip("django")
pytest.importorskip("pytest_django")
pytest.importorskip("rest_framework")


def _copy_app(tmp_path: Path) -> Path:
    app = tmp_path / "app"
    shutil.copytree(TARGET_APP, app, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.sqlite3"))
    return app


def _generate(tmp_path, cases, summary, users, resources, app: Path, sid: str = "SC-UPD-001") -> tuple:
    out = tmp_path / "gen"
    res = generate([cases[sid]], summary, users, resources, {"x": "0"}, None, relative_pythonpath(out, app))
    write_output(res, out)
    return res, out


def _bytecode(root: Path) -> list[str]:
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*.pyc"))


def test_subprocess_env_is_explicit_and_does_not_mutate_parent(tmp_path, cases, summary, users, resources,
                                                               monkeypatch):
    app = _copy_app(tmp_path)
    _, out = _generate(tmp_path, cases, summary, users, resources, app)
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "dis_proje.settings")
    monkeypatch.setenv("DJANGO_CONFIGURATION", "Dis")
    before = dict(os.environ)
    env = runner.subprocess_env(out)
    assert dict(os.environ) == before
    assert env["DJANGO_SETTINGS_MODULE"] == "config.settings"
    assert "DJANGO_CONFIGURATION" not in env
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"
    entries = [Path(p) for p in env["PYTHONPATH"].split(os.pathsep) if p]
    assert all(p.is_absolute() for p in entries)
    target = [p for p in entries if (p / "config" / "settings.py").is_file()]
    assert target and target[0] == app.resolve()
    assert (target[0] / "catalog" / "migrations" / "0001_initial.py").is_file()


def test_external_django_settings_module_does_not_leak_into_generated_run(tmp_path, cases, summary, users,
                                                                          resources, monkeypatch):
    """Önceki uygulamada alt süreç dıştaki DJANGO_SETTINGS_MODULE'ü kullanıyordu ve toplama 0 test buluyordu."""
    app = _copy_app(tmp_path)
    res, out = _generate(tmp_path, cases, summary, users, resources, app)
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "h304_olmayan_proje.settings")
    ok, msg = runner.check_environment(out)
    assert ok, msg
    nodes, log = runner.collect(out)
    assert len(nodes) == 1, log
    raw, log, code = runner.run(out, tmp_path / "t.xml")
    results = runner.classify_all(res.plans, raw)
    assert [r.classification for r in results] == ["PASSED"], log


def test_generated_run_applies_migrations_without_writing_into_target_app(tmp_path, cases, summary, users,
                                                                          resources):
    """Migration'lar (catalog.migrations.0001_initial) alt süreçte yüklenir; hedef ağaca .pyc yazılmaz."""
    app = _copy_app(tmp_path)
    assert _bytecode(app) == []
    res, out = _generate(tmp_path, cases, summary, users, resources, app)
    assert runner.check_environment(out)[0]
    raw, log, code = runner.run(out, tmp_path / "t.xml")
    assert [r.classification for r in runner.classify_all(res.plans, raw)] == ["PASSED"], log
    assert code == 0, log
    assert _bytecode(app) == [], "alt süreç hedef uygulamaya bayt kodu yazdı"


def test_repeated_runs_give_identical_results(tmp_path, cases, summary, users, resources):
    app = _copy_app(tmp_path)
    res, out = _generate(tmp_path, cases, summary, users, resources, app)
    outcomes = []
    for i in range(3):
        raw, log, _ = runner.run(out, tmp_path / f"t{i}.xml")
        outcomes.append([(r.scenario_id, r.classification) for r in runner.classify_all(res.plans, raw)])
    assert outcomes[0] == outcomes[1] == outcomes[2] == [("SC-UPD-001", "PASSED")]


def test_external_pythonpath_cannot_shadow_target_settings(tmp_path, cases, summary, users, resources,
                                                           monkeypatch):
    shadow = tmp_path / "shadow"
    (shadow / "config").mkdir(parents=True)
    (shadow / "config" / "__init__.py").write_text("", encoding="utf-8")
    (shadow / "config" / "settings.py").write_text("raise RuntimeError('yanlış ayar modülü')\n", encoding="utf-8")
    app = _copy_app(tmp_path)
    res, out = _generate(tmp_path, cases, summary, users, resources, app)
    monkeypatch.setenv("PYTHONPATH", str(shadow))
    assert runner.check_environment(out)[0]
    raw, log, _ = runner.run(out, tmp_path / "t.xml")
    assert [r.classification for r in runner.classify_all(res.plans, raw)] == ["PASSED"], log


def test_run_does_not_depend_on_parent_working_directory(tmp_path, cases, summary, users, resources,
                                                         monkeypatch):
    app = _copy_app(tmp_path)
    res, out = _generate(tmp_path, cases, summary, users, resources, app)
    elsewhere = tmp_path / "baska_dizin"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    nodes, log = runner.collect(out)
    assert len(nodes) == 1, log


# ------------------------------------------------------------------ yol taşınabilirliği

def test_target_app_copy_keeps_relative_path_short_and_safe(tmp_path, target_app):
    """Testler hedef uygulamanın geçici kopyasını kullanır: depo yolu ne olursa olsun yol güvenlidir."""
    out = tmp_path / "gen"
    rel = relative_pythonpath(out, target_app)
    assert codegen.is_safe_pythonpath(rel) and rel.endswith("target_app") and " " not in rel
    assert (target_app / "catalog" / "migrations" / "0001_initial.py").is_file()
    assert _bytecode(target_app) == []


def test_relative_pythonpath_with_space_gives_clear_error(tmp_path):
    app = tmp_path / "boşluklu dizin" / "app"
    app.mkdir(parents=True)
    with pytest.raises(PythonpathError, match="boşluk"):
        relative_pythonpath(tmp_path / "gen", app)


def test_relative_pythonpath_across_drives_gives_clear_error(tmp_path, monkeypatch):
    """Windows'ta os.path.relpath farklı sürücüler için ValueError verir; bu durum açık hataya dönüşür."""
    def relpath(*_args):
        raise ValueError("path is on mount 'C:', start on mount 'D:'")
    monkeypatch.setattr("agent.test_generation.rule_based.generator.os.path.relpath", relpath)
    with pytest.raises(PythonpathError, match="farklı sürücü"):
        relative_pythonpath(tmp_path / "gen", tmp_path / "app")


def test_pytest_ini_security_rule_is_unchanged():
    for bad in ("../a b", "../a\nb", "../a'b", '../a"b', "../a=b", "../a;b", "C:/x"):
        with pytest.raises(codegen.LiteralError):
            codegen.build_pytest_ini("config.settings", bad)
    assert "pythonpath = . ../target_app" in codegen.build_pytest_ini("config.settings", "../target_app")
