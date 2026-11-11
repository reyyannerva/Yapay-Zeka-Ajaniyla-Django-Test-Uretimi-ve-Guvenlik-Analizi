"""Model yanıtından Pytest kodunu ayıklama — H3-05 / Issue #31."""
from __future__ import annotations

import re

_FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_code(text: str) -> str:
    """İlk ```python ...``` bloğunu döndürür; yoksa metnin kendisini (kırpılmış) döndürür."""
    if not text:
        return ""
    m = _FENCE.search(text)
    if m:
        return m.group(1).strip("\n")
    # Kod bloğu yoksa: metin zaten kod olabilir.
    return text.strip().strip("`").strip()
