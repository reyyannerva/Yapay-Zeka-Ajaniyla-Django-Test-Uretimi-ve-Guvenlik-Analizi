"""Girdi sözleşmesi ve referans yükleme testleri — H3-04 / Issue #30."""
from __future__ import annotations

import copy
import dataclasses

import pytest
from conftest import EXP, REPO

from agent.test_generation.rule_based.contracts import Code
from agent.test_generation.rule_based.loaders import InputError, join_references, parse_endpoint_summary, read_json


def test_real_endpoint_summary_is_valid_and_declares_no_ast(summary):
    assert {e.endpoint_id for e in summary.endpoints} == {
        "EP-ARTICLE-LIST", "EP-ARTICLE-DETAIL", "EP-ARTICLE-PUBLISH", "EP-INSECURE-ARTICLE-LIST",
        "EP-INSECURE-ARTICLE-DETAIL"}
    assert summary.ast_integration is False and summary.source_kind == "manual_fixture_metadata"
    assert all(p.type == "int" for e in summary.endpoints for p in e.route_params)


@pytest.mark.parametrize("path,code", [
    ("endpoints/0/url_name", Code.SCHEMA_VIOLATION),
    ("target_app", Code.SCHEMA_VIOLATION),
    ("endpoints/1/route_params/0", Code.MISSING_ROUTE_PARAM),
])
def test_endpoint_summary_contract_violations(summary_copy, path, code):
    node = summary_copy
    keys = path.split("/")
    for k in keys[:-1]:
        node = node[int(k)] if isinstance(node, list) else node[k]
    del node[int(keys[-1]) if isinstance(node, list) else keys[-1]]
    with pytest.raises(InputError) as exc:
        parse_endpoint_summary(summary_copy)
    assert code in {d.code for d in exc.value.diagnostics}


def test_duplicate_endpoint_ids_rejected(summary_copy):
    summary_copy["endpoints"].append(copy.deepcopy(summary_copy["endpoints"][0]))
    with pytest.raises(InputError, match="Yinelenen endpoint_id"):
        parse_endpoint_summary(summary_copy)


def test_unsupported_endpoint_requires_reason(summary_copy):
    summary_copy["endpoints"][0]["supported"] = False
    with pytest.raises(InputError):
        parse_endpoint_summary(summary_copy)


def test_invalid_json_file(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(InputError) as exc:
        read_json(bad)
    assert exc.value.diagnostics[0].code is Code.INVALID_JSON


def test_real_references_join_without_diagnostics(references, raw_gt):
    cases, diags = references
    assert diags == []
    assert len(cases) == len(raw_gt["records"])


def test_expected_status_comes_from_ground_truth_not_scenarios(cases, raw_scen, raw_gt):
    scen = {s["id"]: s for s in raw_scen["scenarios"]}
    gold = {r["scenario_id"]: r["expected_result"]["secure_status"] for r in raw_gt["records"]}
    for sid, case in cases.items():
        assert case.expected_status == gold[sid]
    # Bilerek-hatalı senaryolarda iki kaynak farklıdır; üretici güvenli beklentiyi kullanır.
    flawed = [sid for sid in cases if cases[sid].is_known_flaw
              and gold[sid] != scen[sid]["expected_http_status"]]
    assert flawed, "Ground truth ile gözlemlenen hatalı durum ayrımı test verisinde bulunmalı"


def _pair(raw_gt, raw_scen, sid):
    r = copy.deepcopy(next(x for x in raw_gt["records"] if x["scenario_id"] == sid))
    s = copy.deepcopy(next(x for x in raw_scen["scenarios"] if x["id"] == sid))
    return r, s


def test_missing_reference_and_missing_scenario_data(raw_gt, raw_scen):
    r, s = _pair(raw_gt, raw_scen, "SC-UPD-001")
    _, diags = join_references({"records": []}, {"scenarios": [s]})
    assert [(d.code, d.scenario_id) for d in diags] == [(Code.MISSING_REFERENCE, "SC-UPD-001")]
    _, diags = join_references({"records": [r]}, {"scenarios": []})
    assert [(d.code, d.scenario_id) for d in diags] == [(Code.MISSING_SCENARIO_DATA, "SC-UPD-001")]


def test_reference_conflict_and_duplicates(raw_gt, raw_scen):
    r, s = _pair(raw_gt, raw_scen, "SC-UPD-001")
    s2 = dict(s, user_role="admin")
    cases, diags = join_references({"records": [r]}, {"scenarios": [s2]})
    assert not cases and diags[0].code is Code.REFERENCE_CONFLICT
    cases, diags = join_references({"records": [r, r]}, {"scenarios": [s, s]})
    assert [d.code for d in diags].count(Code.DUPLICATE_SCENARIO) == 2 and len(cases) == 1


def test_reference_case_is_immutable(cases):
    with pytest.raises(dataclasses.FrozenInstanceError):
        cases["SC-UPD-001"].expected_status = 500


def test_examples_file_uses_only_synthetic_ids():
    spec = read_json(EXP / "examples" / "unsupported_cases.json")
    assert spec["base"]["reference"]["scenario_id"].startswith("SC-EXM-")
    real_ids = {s["id"] for s in read_json(REPO / "benchmarks/drf_fixtures/scenarios/scenarios.json")["scenarios"]}
    assert spec["base"]["scenario"]["id"] not in real_ids
