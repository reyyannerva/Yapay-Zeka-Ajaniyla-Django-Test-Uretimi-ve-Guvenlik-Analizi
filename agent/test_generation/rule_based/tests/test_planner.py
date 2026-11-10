"""Planlama kuralları: endpoint eşleme, rol/sahiplik, beklenen durum, yan etki — H3-04 / Issue #30."""
from __future__ import annotations

import dataclasses

import pytest
from conftest import EXP, REPO

from agent.test_generation.rule_based.contracts import Code, Status
from agent.test_generation.rule_based.examples import run_examples
from agent.test_generation.rule_based.planner import plan_case, resolve_endpoint


@pytest.mark.parametrize("path,endpoint_id,kwargs", [
    ("/api/articles/", "EP-ARTICLE-LIST", {}),
    ("/api/articles/7/", "EP-ARTICLE-DETAIL", {"pk": 7}),
    ("/api/articles/7/publish/", "EP-ARTICLE-PUBLISH", {"pk": 7}),
    ("/api/insecure/articles/", "EP-INSECURE-ARTICLE-LIST", {}),
    ("/api/insecure/articles/12/", "EP-INSECURE-ARTICLE-DETAIL", {"pk": 12}),
])
def test_dynamic_route_resolution(summary, path, endpoint_id, kwargs):
    matches = resolve_endpoint(path, summary.endpoints)
    assert [(m[0].endpoint_id, m[1]) for m in matches] == [(endpoint_id, kwargs)]


@pytest.mark.parametrize("path", ["/api/articles/abc/publish/", "/api/articles", "/api/other/", "/api/articles/1/x/"])
def test_unresolvable_routes(summary, path):
    assert resolve_endpoint(path, summary.endpoints) == []


def plan(cases, summary, users, resources, sid, **override):
    case = dataclasses.replace(cases[sid], **override) if override else cases[sid]
    return plan_case(case, summary, users, resources)


@pytest.mark.parametrize("sid,method,action,rule", [
    ("SC-LST-001", "GET", "list", "none"),
    ("SC-RET-006", "GET", "retrieve", "none"),
    ("SC-CRT-001", "POST", "create", "count_plus_one"),
    ("SC-INP-001", "POST", "create", "count_unchanged"),
    ("SC-PUB-001", "POST", "custom_action", "none"),
    ("SC-UPD-001", "PUT", "update", "update_applied"),
    ("SC-INP-003", "PUT", "update", "resource_unchanged"),
    ("SC-NF-001", "PUT", "update", "resource_still_absent"),
    ("SC-UPD-003", "PATCH", "partial_update", "partial_update_applied"),
    ("SC-AUZ-002", "PATCH", "partial_update", "resource_unchanged"),
    ("SC-DEL-001", "DELETE", "destroy", "resource_deleted"),
    ("SC-AUZ-003", "DELETE", "destroy", "resource_unchanged"),
    ("SC-NF-002", "DELETE", "destroy", "resource_still_absent"),
    ("SC-MNA-001", "DELETE", "method_not_allowed", "count_unchanged"),
    ("SC-MNA-002", "PUT", "method_not_allowed", "count_unchanged"),
])
def test_each_method_plans_correct_action_and_side_effect(cases, summary, users, resources, sid, method, action, rule):
    out = plan(cases, summary, users, resources, sid)
    assert out.status is Status.GENERATED
    assert (out.plan.http_method, out.plan.action, out.plan.side_effect_check) == (method, action, rule)


def test_method_not_allowed_is_reported_and_expectation_from_reference(cases, summary, users, resources):
    out = plan(cases, summary, users, resources, "SC-MNA-001")
    assert out.plan.method_allowed is False and out.plan.expected_status == cases["SC-MNA-001"].expected_status
    assert Code.METHOD_NOT_IN_OPERATIONS in {d.code for d in out.diagnostics}


@pytest.mark.parametrize("sid,relation", [
    ("SC-UPD-001", "kaynak_sahibi"), ("SC-AUZ-001", "sahip_olmayan"), ("SC-UPD-002", "yonetici"),
    ("SC-AUT-002", "anonim"), ("SC-CRT-001", "kimligi_dogrulanmis"), ("SC-FLW-002", "sahip_olmayan"),
])
def test_ownership_comes_from_fixture_records(cases, summary, users, resources, sid, relation):
    assert plan(cases, summary, users, resources, sid).plan.actor_relation == relation


def test_ownership_uses_fixture_owner_field_not_username(cases, summary, users, resources):
    # Makale 1'in sahibini fixture kopyasında bob yaparsak alice artık sahip değildir → ROLE_MISMATCH.
    swapped = [dict(r, fields=dict(r["fields"], owner=3)) if r["pk"] == 1 else r for r in resources]
    out = plan_case(cases["SC-UPD-001"], summary, users, swapped)
    assert out.status is Status.INVALID_INPUT and out.diagnostics[0].code is Code.ROLE_MISMATCH


def test_admin_role_requires_is_staff(cases, summary, users, resources):
    demoted = [dict(u, fields=dict(u["fields"], is_staff=False)) if u["fields"]["username"] == "admin" else u
               for u in users]
    out = plan_case(cases["SC-UPD-002"], summary, demoted, resources)
    assert out.diagnostics[0].code is Code.ROLE_MISMATCH


@pytest.mark.parametrize("new_status", [200, 204, 400, 403, 404])
def test_expected_status_is_never_inferred_from_role_or_method(cases, summary, users, resources, new_status):
    # Anonim PUT senaryosunun referans beklentisi değişirse plan da birebir onu kullanır (401 sabit değil).
    out = plan(cases, summary, users, resources, "SC-AUT-002", expected_status=new_status)
    assert out.plan.expected_status == new_status


@pytest.mark.parametrize("override,code,status", [
    ({"http_method": "get"}, Code.UNKNOWN_METHOD, Status.INVALID_INPUT),
    ({"http_method": "OPTIONS"}, Code.UNSUPPORTED_METHOD, Status.UNSUPPORTED),
    ({"expected_status": 302}, Code.INVALID_STATUS, Status.INVALID_INPUT),
    ({"expected_status": "200"}, Code.INVALID_STATUS, Status.INVALID_INPUT),
    ({"expected_status": True}, Code.INVALID_STATUS, Status.INVALID_INPUT),
    ({"endpoint": None}, Code.MISSING_ENDPOINT_METADATA, Status.INVALID_INPUT),
    ({"endpoint": "/api/unknown/1/"}, Code.UNRESOLVED_ROUTE, Status.INVALID_INPUT),
    ({"fixture_user": "mallory"}, Code.MISSING_FIXTURE_USER, Status.INVALID_INPUT),
    ({"fixture_user": None}, Code.ROLE_MISMATCH, Status.INVALID_INPUT),
    ({"user_role": "root"}, Code.UNKNOWN_ROLE, Status.INVALID_INPUT),
    ({"fixture_resource": None}, Code.MISSING_ROUTE_PARAM, Status.INVALID_INPUT),
    ({"fixture_resource": 3}, Code.ROUTE_PARAM_MISMATCH, Status.INVALID_INPUT),
    ({"request_input": "title=x"}, Code.INVALID_PAYLOAD, Status.INVALID_INPUT),
])
def test_invalid_inputs_are_reported_not_skipped(cases, summary, users, resources, override, code, status):
    out = plan(cases, summary, users, resources, "SC-UPD-001", **override)
    assert out.status is status and out.plan is None
    assert out.diagnostics[0].code is code and out.diagnostics[0].scenario_id == "SC-UPD-001"


def test_body_on_get_is_invalid(cases, summary, users, resources):
    out = plan(cases, summary, users, resources, "SC-RET-001", request_input={"x": 1})
    assert out.diagnostics[0].code is Code.INVALID_PAYLOAD


def test_unknown_payload_field_is_warned(cases, summary, users, resources):
    out = plan(cases, summary, users, resources, "SC-UPD-001", request_input={"title": "a", "owner": "bob"})
    assert out.status is Status.GENERATED and Code.UNKNOWN_PAYLOAD_FIELD in {d.code for d in out.diagnostics}


def test_content_level_flaw_is_reported_as_limitation(cases, summary, users, resources):
    out = plan(cases, summary, users, resources, "SC-FLW-003")
    assert out.status is Status.GENERATED
    assert Code.CONTENT_ASSERTION_UNSUPPORTED in {d.code for d in out.diagnostics}


def test_owner_on_collection_generates_with_ownership_warning(cases, summary, users, resources):
    out = plan(cases, summary, users, resources, "SC-CRT-002")
    assert out.status is Status.GENERATED and Code.OWNERSHIP_UNVERIFIABLE in {d.code for d in out.diagnostics}


def test_all_unsupported_examples_produce_expected_diagnostics():
    rep = run_examples(EXP / "examples" / "unsupported_cases.json", EXP / "endpoint_summary.json", REPO)
    mismatched = [e["example_id"] for e in rep["examples"] if not e["matched"]]
    assert rep["total"] >= 20 and not mismatched
