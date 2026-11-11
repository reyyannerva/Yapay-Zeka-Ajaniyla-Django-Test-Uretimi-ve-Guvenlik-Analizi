"""Pytest eklentisi: her testin aşama sonucunu ve istisna türünü JSON'a yazar — H3-06 / Issue #32.

JUnit XML, doğrulama (``AssertionError``) başarısızlığını diğer istisnalardan güvenilir biçimde ayırmaz.
Bu eklenti ``H306_PROBE_OUT`` ortam değişkenindeki dosyaya, her test aşaması (setup/call/teardown) için
sonuç ve istisna türünü kaydeder. Test kodunu değiştirmez; yalnızca gözlemler.
"""
from __future__ import annotations

import json
import os

import pytest

_RECORDS: list[dict] = []


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    exc = call.excinfo
    _RECORDS.append({
        "nodeid": rep.nodeid,
        "when": rep.when,
        "outcome": rep.outcome,
        "xfail": bool(getattr(rep, "wasxfail", False)),
        "exc_type": exc.typename if exc is not None else None,
        "message": str(exc.value)[:1500] if exc is not None else "",
    })


def pytest_collectreport(report):
    if report.failed:
        _RECORDS.append({"nodeid": report.nodeid, "when": "collect", "outcome": "failed", "xfail": False,
                         "exc_type": "CollectionError", "message": str(report.longrepr)[-1500:]})


def pytest_sessionfinish(session, exitstatus):
    path = os.environ.get("H306_PROBE_OUT")
    if path:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"exitstatus": int(exitstatus), "records": _RECORDS}, fh, ensure_ascii=False, indent=1)
