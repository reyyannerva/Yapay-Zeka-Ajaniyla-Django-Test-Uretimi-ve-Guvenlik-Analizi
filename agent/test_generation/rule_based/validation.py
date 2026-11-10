"""Üretilen kodun statik doğrulaması — H3-04 / Issue #30.

Çalıştırmadan önce: ``ast.parse``, ``compile``, dosya adı kuralı, yinelenen test adı, senaryo↔test
izlenebilirliği ve gerekli içe aktarımlar denetlenir. Pytest keşfi (``--collect-only``) ayrıca
``runner.collect`` ile doğrulanır.
"""
from __future__ import annotations

import ast
import re

from .contracts import Code, Diagnostic, Severity, TestPlan

MODULE_NAME_RX = re.compile(r"^test_[a-z]+_generated\.py$")
REQUIRED_IMPORTS = {"pytest", "User", "reverse", "model_count", "route_message", "side_effect_message",
                    "snapshot", "status_message"}


def _err(code: Code, msg: str, detail: str = "", scenario_id: str | None = None) -> Diagnostic:
    return Diagnostic(code, Severity.ERROR, msg, scenario_id=scenario_id, detail=detail)


def validate_module(filename: str, source: str, plans: list[TestPlan]) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    if not MODULE_NAME_RX.match(filename):
        out.append(_err(Code.TRACEABILITY_ERROR, "Dosya adı üretim kuralına uymuyor", filename))
    try:
        tree = ast.parse(source, filename=filename)
        compile(source, filename, "exec")
    except SyntaxError as exc:
        return out + [_err(Code.SYNTAX_ERROR, f"{filename}: sözdizimi hatası", f"satır {exc.lineno}: {exc.msg}")]
    imported = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            imported |= {a.asname or a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported |= {a.asname or a.name for a in node.names}
    missing = REQUIRED_IMPORTS - imported
    if missing:
        out.append(_err(Code.SYNTAX_ERROR, f"{filename}: gerekli içe aktarımlar eksik", ", ".join(sorted(missing))))
    funcs = [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    dup = sorted({f for f in funcs if funcs.count(f) > 1})
    for name in dup:
        out.append(_err(Code.DUPLICATE_TEST_NAME, f"{filename}: yinelenen test adı", name))
    expected = {p.test_name: p.scenario_id for p in plans}
    for name, sid in expected.items():
        if name not in funcs:
            out.append(_err(Code.TRACEABILITY_ERROR, f"{filename}: planlanan test üretilen kodda yok", name, sid))
    for name in funcs:
        if name not in expected:
            out.append(_err(Code.TRACEABILITY_ERROR, f"{filename}: planı olmayan test fonksiyonu", name))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in expected:
            sid = expected[node.name]
            consts = {c.value for c in ast.walk(node) if isinstance(c, ast.Constant) and isinstance(c.value, str)}
            if sid not in consts:
                out.append(_err(Code.TRACEABILITY_ERROR, "Test, senaryo kimliğini doğrulama iletisinde taşımıyor",
                                node.name, sid))
            args = [a.arg for a in node.args.args]
            if args != ["seeded_db", "api_client"]:
                out.append(_err(Code.TRACEABILITY_ERROR, "Test gerekli fixture'ları istemiyor", f"{node.name}: {args}",
                                sid))
    return out


def validate_suite(modules: dict[str, str], plans: list[TestPlan]) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    by_module: dict[str, list[TestPlan]] = {}
    for p in plans:
        by_module.setdefault(p.module, []).append(p)
    names = [p.test_name for p in plans]
    for name in sorted({n for n in names if names.count(n) > 1}):
        out.append(_err(Code.DUPLICATE_TEST_NAME, "Birden fazla senaryo aynı test adını üretiyor", name))
    for filename, source in sorted(modules.items()):
        out += validate_module(filename, source, by_module.get(filename, []))
    return out
