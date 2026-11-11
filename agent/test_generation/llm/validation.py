"""Üretilen kodun sözdizimi ve temel yapı doğrulaması — H3-05 / Issue #31."""
from __future__ import annotations

import ast


def check_syntax(code: str, expected_func: str | None = None) -> tuple[bool, str | None]:
    """(geçerli_mi, hata). Python sözdizimini ve (verildiyse) beklenen test fonksiyonunu kontrol eder."""
    if not code or not code.strip():
        return False, "boş çıktı"
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, f"SyntaxError: {exc.msg} (satır {exc.lineno})"
    if expected_func is not None:
        funcs = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        if expected_func not in funcs:
            return False, f"beklenen test fonksiyonu yok: {expected_func} (bulunan: {sorted(funcs)})"
    return True, None
