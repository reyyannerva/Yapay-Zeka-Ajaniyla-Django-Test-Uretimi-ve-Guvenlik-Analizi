"""Pytest kaynak kodu üretimi (AST tabanlı) — H3-04 / Issue #30.

Kaynak kod metin birleştirmeyle değil, Python AST düğümleriyle kurulur. Sabit kod parçaları
yalnızca tanımlayıcı içeren şablonlardır; senaryo verisi (URL adı, gövde, kimlik, beklenen kod)
``literal()`` ile doğrulanmış ``ast.Constant``/``ast.Dict`` düğümleri olarak yerleştirilir.
Çıktı ``ast.unparse`` ile üretilir; aynı girdi her zaman aynı kaynak kodu verir.
"""
from __future__ import annotations

import ast
import re
from typing import Any

from .contracts import TestPlan

SUPPORT_MODULE = "h304_support"
GENERATOR_ID = "agent.test_generation.rule_based"
GENERATOR_VERSION = "1.0.0"


class LiteralError(ValueError):
    pass


def literal(value: Any) -> ast.expr:
    """JSON uyumlu bir değeri güvenli AST ifadesine dönüştürür."""
    if value is None or isinstance(value, (bool, str)):
        return ast.Constant(value)
    if isinstance(value, (int, float)):
        return ast.Constant(value)
    if isinstance(value, (list, tuple)):
        node = ast.List if isinstance(value, list) else ast.Tuple
        return node(elts=[literal(v) for v in value], ctx=ast.Load())
    if isinstance(value, dict):
        if not all(isinstance(k, str) for k in value):
            raise LiteralError(f"Sözlük anahtarları metin olmalı: {list(value)!r}")
        keys = sorted(value)
        return ast.Dict(keys=[ast.Constant(k) for k in keys], values=[literal(value[k]) for k in keys])
    raise LiteralError(f"Desteklenmeyen değer tipi: {type(value).__name__}")


class _Fill(ast.NodeTransformer):
    def __init__(self, values: dict[str, Any]):
        self.values = values

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if node.id.startswith("__") and node.id.endswith("__") and node.id in self.values:
            return literal(self.values[node.id])
        return node


def stmts(template: str, **values: Any) -> list[ast.stmt]:
    """Tanımlayıcı şablonu ayrıştırır ve ``__AD__`` yer tutucularını değerlerle doldurur."""
    tree = ast.parse(template)
    mapping = {f"__{k}__": v for k, v in values.items()}
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id in mapping}
    missing = set(mapping) - used
    if missing:
        raise LiteralError(f"Şablonda kullanılmayan yer tutucu: {sorted(missing)}")
    return _Fill(mapping).visit(tree).body


def _docstring(p: TestPlan) -> str:
    who = "anonim" if p.username is None else f"{p.user_role} ({p.username}; fixture ilişkisi: {p.actor_relation})"
    lines = [
        f"{p.scenario_id} · {p.http_method} {p.path} · {who} · beklenen {p.expected_status}",
        "",
        f"Beklenen davranış: {p.expected_behavior}",
        f"Referans: ground_truth.json ({p.reference_source}, {p.validation_status}); kategori: {p.category}",
        f"Endpoint: {p.endpoint_id} ({p.url_name}), işlem: {p.action}; yan etki kuralı: {p.side_effect_check}",
    ]
    if p.is_known_flaw:
        sf = p.security_finding or {}
        lines.append(f"Bilinen güvenlik kusuru: {sf.get('finding_type')} — güvensiz uçta gözlenen "
                     f"{sf.get('observed_flawed_status')} ({sf.get('deviation_kind')} sapması).")
    for w in p.warnings:
        lines.append(f"Uyarı [{w.code.value}]: {w.message}")
    return "\n    ".join(lines) + "\n    "


def build_test_function(p: TestPlan) -> ast.FunctionDef:
    body: list[ast.stmt] = [ast.Expr(ast.Constant(_docstring(p)))]
    sid, model, fields = p.scenario_id, p.model, list(p.writable_fields)
    if p.username is not None:
        body += stmts("api_client.force_authenticate(user=User.objects.get(username=__USER__))", USER=p.username)
    if p.url_kwargs:
        body += stmts("url = reverse(__NAME__, kwargs=__KWARGS__)", NAME=p.url_name, KWARGS=p.url_kwargs)
    else:
        body += stmts("url = reverse(__NAME__)", NAME=p.url_name)
    body += stmts("assert url == __PATH__, route_message(__SID__, __PATH__, url)", PATH=p.path, SID=sid)

    rule = p.side_effect_check
    expected_subset = {k: v for k, v in (p.payload or {}).items() if k in p.writable_fields}
    if rule in ("update_applied", "partial_update_applied") and not expected_subset:
        rule = "none"
    if rule in ("count_plus_one", "count_unchanged"):
        body += stmts("before_count = model_count(__MODEL__)", MODEL=model)
    if rule in ("update_applied", "partial_update_applied", "resource_unchanged", "resource_deleted"):
        body += stmts("before = snapshot(__MODEL__, __PK__, __FIELDS__)", MODEL=model, PK=p.lookup_value,
                      FIELDS=fields)

    m = p.http_method.lower()
    if p.http_method in ("GET", "DELETE"):
        body += stmts(f"response = api_client.{m}(url)")
    elif p.payload is None:
        body += stmts(f"response = api_client.{m}(url, format='json')")
    else:
        body += stmts(f"response = api_client.{m}(url, __PAYLOAD__, format='json')", PAYLOAD=p.payload)
    body += stmts("assert response.status_code == __EXP__, status_message(__SID__, __EXP__, response, __BEH__)",
                  EXP=p.expected_status, SID=sid, BEH=p.expected_behavior)

    if rule == "count_plus_one":
        body += stmts("after_count = model_count(__MODEL__)\n"
                      "assert after_count == before_count + 1, side_effect_message(__SID__, __RULE__, "
                      "before_count + 1, after_count)", MODEL=model, SID=sid, RULE=rule)
    elif rule == "count_unchanged":
        body += stmts("after_count = model_count(__MODEL__)\n"
                      "assert after_count == before_count, side_effect_message(__SID__, __RULE__, "
                      "before_count, after_count)", MODEL=model, SID=sid, RULE=rule)
    elif rule == "update_applied":
        body += stmts("after = snapshot(__MODEL__, __PK__, __FIELDS__)\n"
                      "observed = {key: after[key] for key in __KEYS__} if after else None\n"
                      "assert observed == __EXPECTED__, side_effect_message(__SID__, __RULE__, __EXPECTED__, observed)",
                      MODEL=model, PK=p.lookup_value, FIELDS=fields, KEYS=sorted(expected_subset),
                      EXPECTED=expected_subset, SID=sid, RULE=rule)
    elif rule == "partial_update_applied":
        body += stmts("after = snapshot(__MODEL__, __PK__, __FIELDS__)\n"
                      "expected_after = {**before, **__EXPECTED__}\n"
                      "assert after == expected_after, side_effect_message(__SID__, __RULE__, expected_after, after)",
                      MODEL=model, PK=p.lookup_value, FIELDS=fields, EXPECTED=expected_subset, SID=sid, RULE=rule)
    elif rule == "resource_unchanged":
        body += stmts("after = snapshot(__MODEL__, __PK__, __FIELDS__)\n"
                      "assert after == before, side_effect_message(__SID__, __RULE__, before, after)",
                      MODEL=model, PK=p.lookup_value, FIELDS=fields, SID=sid, RULE=rule)
    elif rule in ("resource_deleted", "resource_still_absent"):
        body += stmts("after = snapshot(__MODEL__, __PK__, __FIELDS__)\n"
                      "assert after is None, side_effect_message(__SID__, __RULE__, None, after)",
                      MODEL=model, PK=p.lookup_value, FIELDS=fields, SID=sid, RULE=rule)

    extra = {"type_params": []} if "type_params" in ast.FunctionDef._fields else {}
    return ast.FunctionDef(
        name=p.test_name,
        args=ast.arguments(posonlyargs=[], args=[ast.arg("seeded_db"), ast.arg("api_client")], vararg=None,
                           kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
        body=body, decorator_list=[], returns=None, **extra,
    )


def module_header(method: str, input_digests: dict[str, str]) -> str:
    lines = [
        f"{method} senaryoları için kural tabanlı üretilmiş Pytest testleri — H3-04 / Issue #30.",
        "",
        "BU DOSYA OTOMATİK ÜRETİLMİŞTİR; ELLE DÜZENLEMEYİN. Yeniden üretmek için:",
        "    python -m agent.test_generation.rule_based generate",
        "",
        f"Üretici: {GENERATOR_ID} v{GENERATOR_VERSION} (LLM kullanılmaz).",
        "Beklenen durum kodları bağımsız referanstan (ground_truth.json → secure_status) alınmıştır.",
        "Girdi özetleri (SHA-256):",
    ]
    lines += [f"    {name}: {digest}" for name, digest in sorted(input_digests.items())]
    return "\n".join(lines)


def build_module(method: str, plans: list[TestPlan], input_digests: dict[str, str]) -> str:
    body: list[ast.stmt] = [ast.Expr(ast.Constant(module_header(method, input_digests)))]
    body += ast.parse(
        "import pytest\n"
        "from django.contrib.auth.models import User\n"
        "from django.urls import reverse\n"
        f"from {SUPPORT_MODULE} import model_count, route_message, side_effect_message, snapshot, status_message\n"
        "pytestmark = pytest.mark.django_db\n").body
    for p in sorted(plans, key=lambda x: x.scenario_id):
        body.append(build_test_function(p))
    module = ast.Module(body=body, type_ignores=[])
    ast.fix_missing_locations(module)
    return ast.unparse(module) + "\n"


def build_conftest(fixtures: list[str]) -> str:
    module = ast.Module(body=[
        ast.Expr(ast.Constant("Üretilen testlerin ortak fixture'ları — H3-04 / Issue #30 (otomatik üretilmiştir).\n\n"
                              "Her test kendi işlem (transaction) kapsamında çalışır; pytest-django her testten sonra "
                              "veritabanını geri alır. Fixture verisi her test için yeniden yüklenir, böylece testler "
                              "birbirine ve çalışma sırasına bağımlı değildir.")),
        *ast.parse("import pytest\nfrom django.core.management import call_command\n"
                   "from rest_framework.test import APIClient\n").body,
        *stmts("FIXTURES = __FIX__", FIX=list(fixtures)),
        *ast.parse("@pytest.fixture\ndef seeded_db(db):\n    call_command('loaddata', *FIXTURES, verbosity=0)\n\n"
                   "@pytest.fixture\ndef api_client():\n    return APIClient()\n").body,
    ], type_ignores=[])
    ast.fix_missing_locations(module)
    return ast.unparse(module) + "\n"


_SETTINGS_RX = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")
_PATH_RX = re.compile(r"^[A-Za-z0-9_./-]+$")


def build_pytest_ini(settings_module: str, target_pythonpath: str) -> str:
    """Üretilen test dizininin pytest yapılandırması; değerler biçim denetiminden geçer."""
    if not _SETTINGS_RX.match(settings_module):
        raise LiteralError(f"Geçersiz Django ayar modülü: {settings_module!r}")
    if not _PATH_RX.match(target_pythonpath):
        raise LiteralError(f"Geçersiz pythonpath: {target_pythonpath!r}")
    return ("# Otomatik üretilmiştir (H3-04 / Issue #30); elle düzenlemeyin.\n"
            "[pytest]\n"
            f"DJANGO_SETTINGS_MODULE = {settings_module}\n"
            f"pythonpath = . {target_pythonpath}\n"
            "python_files = test_*_generated.py\n"
            "addopts = -p no:cacheprovider\n")
