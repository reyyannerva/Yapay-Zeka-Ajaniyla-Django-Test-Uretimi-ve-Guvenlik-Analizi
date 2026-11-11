#!/usr/bin/env python
"""scenarios.json -> scenarios.csv dışa aktarımı — H3-01 / Issue #27.

JSON kanoniktir; CSV, EDA (H3-02) ve okunurluk için türetilmiş bir kopyadır.
Kullanım:  python scripts/export_scenarios_csv.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "scenarios" / "scenarios.json"
DST = BASE / "scenarios" / "scenarios.csv"

COLS = [
    "id", "category", "http_method", "endpoint", "user_role",
    "expected_http_status", "label", "is_intentional_flaw",
    "fixture_user", "fixture_article", "request_input", "expected_behavior",
    "flaw_explanation", "requirement_refs",
]


def main() -> int:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    with DST.open("w", newline="", encoding="utf-8") as fh:
        # LF satır sonu: depodaki kanonik biçim (denetim D-03); csv modülünün varsayılanı CRLF'tir.
        writer = csv.DictWriter(fh, fieldnames=COLS, lineterminator="\n")
        writer.writeheader()
        for s in data["scenarios"]:
            writer.writerow({
                "id": s["id"],
                "category": s["category"],
                "http_method": s["http_method"],
                "endpoint": s["endpoint"],
                "user_role": s["user_role"],
                "expected_http_status": s["expected_http_status"],
                "label": s["label"],
                "is_intentional_flaw": s["is_intentional_flaw"],
                "fixture_user": s["fixture_ref"]["user"] or "",
                "fixture_article": s["fixture_ref"]["article"] if s["fixture_ref"]["article"] is not None else "",
                "request_input": json.dumps(s["request_input"], ensure_ascii=False) if s["request_input"] else "",
                "expected_behavior": s["expected_behavior"],
                "flaw_explanation": s.get("flaw_explanation", ""),
                "requirement_refs": ";".join(s["requirement_refs"]),
            })
    print(f"{len(data['scenarios'])} satır yazıldı -> {DST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
