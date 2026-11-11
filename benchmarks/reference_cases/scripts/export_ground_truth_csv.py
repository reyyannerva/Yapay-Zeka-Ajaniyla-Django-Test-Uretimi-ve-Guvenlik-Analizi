#!/usr/bin/env python
"""ground_truth.json -> ground_truth.csv — H3-03 / Issue #29. JSON kanoniktir."""
from __future__ import annotations

import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "ground_truth.json"
SPLIT = BASE / "split.json"
DST = BASE / "ground_truth.csv"

COLS = [
    "scenario_id", "split", "http_method", "user_role", "secure_status", "label",
    "reference_source", "validation_status", "is_known_flaw",
    "finding_type", "deviation_kind", "observed_flawed_status", "expected_behavior",
]


def main() -> int:
    gt = json.loads(SRC.read_text(encoding="utf-8"))
    scenario_split = json.loads(SPLIT.read_text(encoding="utf-8"))["scenario_split"]
    with DST.open("w", newline="", encoding="utf-8") as fh:
        # LF satır sonu: depodaki kanonik biçim (denetim D-03); csv modülünün varsayılanı CRLF'tir.
        w = csv.DictWriter(fh, fieldnames=COLS, lineterminator="\n")
        w.writeheader()
        for r in gt["records"]:
            sf = r.get("security_finding", {})
            w.writerow({
                "scenario_id": r["scenario_id"],
                "split": scenario_split.get(r["scenario_id"], ""),
                "http_method": r["http_method"],
                "user_role": r["user_role"],
                "secure_status": r["expected_result"]["secure_status"],
                "label": r["label"],
                "reference_source": r["reference_source"],
                "validation_status": r["validation_status"],
                "is_known_flaw": r["is_known_flaw"],
                "finding_type": sf.get("finding_type", ""),
                "deviation_kind": sf.get("deviation_kind", ""),
                "observed_flawed_status": sf.get("observed_flawed_status", ""),
                "expected_behavior": r["expected_result"]["behavior"],
            })
    print(f"{len(gt['records'])} satır yazıldı -> {DST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
