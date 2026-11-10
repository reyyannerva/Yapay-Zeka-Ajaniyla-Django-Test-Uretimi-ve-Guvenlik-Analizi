"""Desteklenmeyen / geçersiz girdi örneklerinin çalıştırılması — H3-04 / Issue #30.

Örnekler SENTETİKTİR (``SC-EXM-*`` / ``EX-*``) ve yalnızca tanı davranışını göstermek içindir; gerçek
değerlendirme sonuçlarına karışmaz. Her örnek gerçek yükleyici ve planlayıcıdan geçirilir ve
beklenen durum/kod ile karşılaştırılır.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .contracts import Status
from .loaders import InputError, join_references, load_fixture_records, parse_endpoint_summary, read_json
from .planner import plan_case
from .reporting import table


def _merge(base: dict, override: dict | None) -> dict:
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def _remove(data: dict, path: str) -> None:
    keys = path.split("/")
    node: Any = data
    for k in keys[:-1]:
        node = node[int(k)] if isinstance(node, list) else node[k]
    last = keys[-1]
    del node[int(last) if isinstance(node, list) else last]


def run_example(ex: dict, base_summary: dict, base: dict, users: list[dict], resources: list[dict]) -> dict:
    kind = ex["kind"]
    status, codes = None, []
    if kind == "endpoint_summary_json":
        try:
            parse_endpoint_summary(json.loads(ex["raw"]))
        except json.JSONDecodeError as exc:
            status, codes = Status.INVALID_INPUT.value, ["INVALID_JSON"]
            detail = f"satır {exc.lineno}: {exc.msg}"
        else:
            detail = "beklenmedik biçimde ayrıştırıldı"
        return {"status": status, "codes": codes, "detail": detail}
    summary_dict = copy.deepcopy(base_summary)
    for p in ex.get("remove_fields", []):
        _remove(summary_dict, p)
    summary_dict["endpoints"] += copy.deepcopy(ex.get("extra_endpoints", []))
    if "auth_mechanisms" in ex:
        summary_dict["authentication"]["mechanisms"] = ex["auth_mechanisms"]
    try:
        summary = parse_endpoint_summary(summary_dict)
    except InputError as exc:
        return {"status": Status.INVALID_INPUT.value, "codes": sorted({d.code.value for d in exc.diagnostics}),
                "detail": "; ".join(f"{d.message} {d.detail}" for d in exc.diagnostics)[:400]}
    refs = [] if ex.get("omit_reference") else [_merge(base["reference"], ex.get("reference_override"))]
    scens = [] if ex.get("omit_scenario") else [_merge(base["scenario"], ex.get("scenario_override"))]
    cases, diags = join_references({"records": refs}, {"scenarios": scens})
    if diags:
        return {"status": "MISSING_REFERENCE" if diags[0].code.value in ("MISSING_REFERENCE", "MISSING_SCENARIO_DATA")
                else Status.INVALID_INPUT.value,
                "codes": [d.code.value for d in diags], "detail": "; ".join(f"{d.message} {d.detail}" for d in diags)}
    outcome = plan_case(cases[0], summary, users, resources)
    return {"status": outcome.status.value, "codes": [d.code.value for d in outcome.diagnostics],
            "detail": "; ".join(f"{d.message} ({d.detail})" if d.detail else d.message for d in outcome.diagnostics)}


def run_examples(examples_path: Path, endpoints_path: Path, repo_root: Path) -> dict:
    spec = read_json(examples_path)
    base_summary = read_json(endpoints_path)
    users = load_fixture_records(repo_root / base_summary["target_app"]["fixture_files"]["users"])
    resources = load_fixture_records(repo_root / base_summary["target_app"]["fixture_files"]["resources"])
    rows = []
    for ex in spec["examples"]:
        got = run_example(ex, base_summary, spec["base"], users, resources)
        code_ok = (not got["codes"]) if ex["expected_code"] == "-" else ex["expected_code"] in got["codes"]
        ok = got["status"] == ex["expected_status"] and code_ok
        rows.append({"example_id": ex["example_id"], "description": ex["description"],
                     "expected_status": ex["expected_status"], "expected_code": ex["expected_code"],
                     "actual_status": got["status"], "actual_codes": got["codes"], "detail": got["detail"],
                     "matched": ok})
    return {"report": "H3-04 desteklenmeyen / geçersiz girdi örnekleri", "synthetic": True,
            "total": len(rows), "matched": sum(r["matched"] for r in rows), "examples": rows}


def markdown(rep: dict) -> str:
    return "\n".join([
        "# H3-04 | Desteklenmeyen ve Geçersiz Girdi Örnekleri",
        "",
        "> Otomatik üretilmiştir (`python -m agent.test_generation.rule_based examples`). Örnekler **sentetiktir** "
        "ve yalnızca üreticinin bu durumları sessizce atlamadığını, gerekçeli tanı ürettiğini gösterir.",
        "",
        f"Toplam **{rep['total']}** örnek; beklenen durum ve tanı koduyla uyumlu: **{rep['matched']}**.",
        "",
        table(["Örnek", "Açıklama", "Beklenen", "Gerçekleşen", "Tanı kodları", "Ayrıntı", "Uyum"],
              [[r["example_id"], r["description"], f"{r['expected_status']} / {r['expected_code']}",
                r["actual_status"], ", ".join(r["actual_codes"]), r["detail"], "✓" if r["matched"] else "✗"]
               for r in rep["examples"]]),
        "",
    ])
