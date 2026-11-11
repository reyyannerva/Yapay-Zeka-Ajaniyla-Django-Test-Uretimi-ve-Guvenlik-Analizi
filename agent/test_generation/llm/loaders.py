"""Girdi yükleyiciler ve birleştirme — H3-05 / Issue #31.

Üç ortak girdi: endpoint_summary.json (H3-04), ground_truth.json (H3-03), scenarios.json (H3-01).
Her senaryo, referansı ve endpoint'iyle eşleştirilerek `Case`'e dönüştürülür.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .contracts import Case

_SEG_INT = re.compile(r"^\d+$")


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def templatize(path: str) -> tuple[str, int | None]:
    """Somut yolu şablona çevirir ve pk'yi çıkarır.

    '/api/articles/2/publish/' -> ('/api/articles/{pk}/publish/', 2)
    '/api/articles/' -> ('/api/articles/', None)
    """
    pk: int | None = None
    out = []
    for seg in path.split("/"):
        if _SEG_INT.match(seg):
            pk = int(seg)
            out.append("{pk}")
        else:
            out.append(seg)
    return "/".join(out), pk


def build_endpoint_index(summary: dict) -> dict[str, dict]:
    """Şablon yol -> endpoint kaydı."""
    index: dict[str, dict] = {}
    for ep in summary["endpoints"]:
        index[ep["path"]] = ep
    return index


def _endpoint_for(path: str, index: dict[str, dict]) -> tuple[dict | None, int | None]:
    template, pk = templatize(path)
    return index.get(template), pk


def join_cases(scenarios: dict, ground_truth: dict, endpoint_index: dict[str, dict]
               ) -> tuple[list[Case], list[str]]:
    """Senaryo + referans + endpoint -> Case listesi. İkinci dönüş: eşleşmeyen uyarılar."""
    gt_by_id = {r["scenario_id"]: r for r in ground_truth["records"]}
    cases: list[Case] = []
    warnings: list[str] = []

    for sc in scenarios["scenarios"]:
        sid = sc["id"]
        ref = gt_by_id.get(sid)
        if ref is None:
            warnings.append(f"{sid}: ground_truth kaydı yok; atlandı")
            continue
        ep, pk = _endpoint_for(sc["endpoint"], endpoint_index)
        if ep is None:
            warnings.append(f"{sid}: endpoint özeti eşleşmedi ({sc['endpoint']}); atlandı")
            continue
        op = ep["operations"].get(sc["http_method"], {})
        sf = ref.get("security_finding") or {}
        cases.append(Case(
            scenario_id=sid,
            http_method=sc["http_method"],
            endpoint_path=sc["endpoint"],
            url_name=ep["url_name"],
            pk=pk,
            user_username=sc["fixture_ref"].get("user"),
            user_role=sc["user_role"],
            request_input=sc.get("request_input"),
            writable_fields=ep.get("request", {}).get("writable_fields", {}),
            category=sc["category"],
            expected_secure_status=ref["expected_result"]["secure_status"],
            expected_behavior=ref["expected_result"]["behavior"],
            is_known_flaw=ref.get("is_known_flaw", False),
            deviation_kind=sf.get("deviation_kind"),
            observed_flawed_status=sf.get("observed_flawed_status"),
        ))
    return cases, warnings
