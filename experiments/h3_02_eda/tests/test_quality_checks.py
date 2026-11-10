"""Veri kalitesi kontrollerinin izole birim testleri (sentetik kayıtlarla) — H3-02 / Issue #28."""
from __future__ import annotations

import pandas as pd
import pytest
from conftest import ARTICLES, USERS, make_scenario

from scenario_eda import quality as q


def issues(findings, issue=None):
    return [f for f in findings if issue is None or f["sorun_turu"] == issue]


def test_valid_record_has_no_field_findings(schema):
    assert q.check_record_fields([make_scenario()], schema) == []
    assert q.check_label_consistency([make_scenario()]) == []


def test_duplicate_scenario_id_reported_for_each_occurrence():
    sc = [make_scenario(), make_scenario(endpoint="/api/articles/11/", fixture_ref={"user": "u_owner", "article": 11})]
    out = q.check_duplicate_ids(sc)
    assert len(out) == 2
    assert {f["konum"] for f in out} == {"scenarios[0]", "scenarios[1]"}
    assert all(f["senaryo_id"] == "SC-TST-001" and f["onem_derecesi"] == "Kritik" for f in out)


def test_duplicate_content_with_different_ids():
    sc = [make_scenario(), make_scenario(id="SC-TST-002")]
    out = q.check_duplicate_content(sc)
    assert {f["senaryo_id"] for f in out} == {"SC-TST-001", "SC-TST-002"}


def test_missing_required_field_and_schema_violation(schema):
    rec = make_scenario()
    del rec["expected_behavior"]
    out = q.check_record_fields([rec], schema)
    assert [(f["alan"], f["sorun_turu"]) for f in out] == [("expected_behavior", "EKSIK_ZORUNLU_ALAN")]
    data = {"dataset": "x", "version": "1.0.0", "scenarios": [rec] + [make_scenario(id=f"SC-TST-{i:03d}")
                                                                      for i in range(2, 31)]}
    sch = q.check_json_schema(data, schema)
    assert any(f["alan"] == "expected_behavior" and f["senaryo_id"] == "SC-TST-001" for f in sch)


def test_missing_id_uses_locator_not_invented_id(schema):
    rec = make_scenario()
    del rec["id"]
    out = q.check_record_fields([rec], schema)
    f = issues(out, "EKSIK_ZORUNLU_ALAN")[0]
    assert f["senaryo_id"] is None and f["konum"] == "scenarios[0]"


def test_null_and_empty_string(schema):
    out = q.check_record_fields([make_scenario(category=None, expected_behavior="  ")], schema)
    assert issues(out, "NULL_ZORUNLU_ALAN")[0]["alan"] == "category"
    assert issues(out, "BOS_METIN")[0]["alan"] == "expected_behavior"


def test_nullable_fields_are_not_flagged(schema):
    rec = make_scenario(user_role="anonymous", fixture_ref={"user": None, "article": None},
                        endpoint="/api/articles/", request_input=None)
    assert q.check_record_fields([rec], schema) == []


@pytest.mark.parametrize("method", ["get", "HEAD", "FETCH"])
def test_invalid_http_method(schema, method):
    out = issues(q.check_record_fields([make_scenario(http_method=method)], schema), "GECERSIZ_HTTP_METODU")
    assert len(out) == 1
    if method == "get":
        assert "'GET' olmalı" in out[0]["aciklama"]


def test_invalid_role_and_category(schema):
    out = q.check_record_fields([make_scenario(user_role="superuser", category="XSS")], schema)
    assert issues(out, "GECERSIZ_ROL") and issues(out, "GECERSIZ_KATEGORI")


@pytest.mark.parametrize("status", [418, "200", 200.0, True])
def test_invalid_or_malformed_status_code(schema, status):
    out = issues(q.check_record_fields([make_scenario(expected_http_status=status)], schema), "GECERSIZ_DURUM_KODU")
    assert len(out) == 1


def test_flaw_without_explanation(schema):
    out = q.check_record_fields([make_scenario(is_intentional_flaw=True, label="negative")], schema)
    assert issues(out, "EKSIK_HATA_ACIKLAMASI")


def test_label_inconsistencies():
    out = q.check_label_consistency([
        make_scenario(id="SC-TST-001", label="positive", expected_http_status=403),
        make_scenario(id="SC-TST-002", label="negative", expected_http_status=200),
        make_scenario(id="SC-TST-003", label="negative", expected_http_status=200, is_intentional_flaw=True),
    ])
    assert [f["senaryo_id"] for f in out] == ["SC-TST-001", "SC-TST-002"]


def test_broken_fixture_references(routes):
    out = q.check_fixture_references([
        make_scenario(id="SC-TST-001", fixture_ref={"user": "ghost", "article": 10}),
        make_scenario(id="SC-TST-002", endpoint="/api/articles/77/", fixture_ref={"user": "u_owner", "article": 77}),
        make_scenario(id="SC-TST-003", endpoint="/api/articles/77/", fixture_ref={"user": "u_owner", "article": 77},
                      expected_http_status=404, label="negative"),
    ], USERS, ARTICLES, routes)
    broken = issues(out, "KIRIK_FIXTURE_REFERANSI")
    assert [f["senaryo_id"] for f in broken] == ["SC-TST-001", "SC-TST-002"]
    # 404 beklenen mevcut olmayan kaynak kırık referans değildir; sahiplik doğrulanamaz (Bilgi)
    assert "SC-TST-003" in {f["senaryo_id"] for f in issues(out, "ROL_DOGRULANAMIYOR")}


def test_role_semantics_from_fixtures_not_usernames(routes):
    out = q.check_fixture_references([
        make_scenario(id="SC-TST-001", fixture_ref={"user": "u_other", "article": 10}),          # owner değil
        make_scenario(id="SC-TST-002", user_role="admin", fixture_ref={"user": "u_owner", "article": 10}),
        make_scenario(id="SC-TST-003", user_role="anonymous", fixture_ref={"user": "u_owner", "article": 10}),
        make_scenario(id="SC-TST-004", user_role="user", fixture_ref={"user": "u_owner", "article": 10}),
    ], USERS, ARTICLES, routes)
    ids = sorted(f["senaryo_id"] for f in issues(out, "ROL_TUTARSIZLIGI"))
    assert ids == ["SC-TST-001", "SC-TST-002", "SC-TST-003", "SC-TST-004"]


def test_unresolvable_endpoint_and_pk_mismatch(routes):
    out = q.check_fixture_references([
        make_scenario(id="SC-TST-001", endpoint="/api/unknown/"),
        make_scenario(id="SC-TST-002", endpoint="/api/articles/11/"),
    ], USERS, ARTICLES, routes)
    assert issues(out, "COZUMLENEMEYEN_ENDPOINT")[0]["senaryo_id"] == "SC-TST-001"
    assert issues(out, "TUTARSIZ_FIXTURE_REFERANSI")[0]["senaryo_id"] == "SC-TST-002"


def test_insecure_endpoint_flag_consistency(routes):
    out = q.check_fixture_references([
        make_scenario(id="SC-TST-001", endpoint="/api/insecure/articles/10/"),
        make_scenario(id="SC-TST-002", is_intentional_flaw=True, flaw_explanation="x", label="negative"),
    ], USERS, ARTICLES, routes)
    assert sorted(f["senaryo_id"] for f in issues(out, "TUTARSIZ_ETIKET")) == ["SC-TST-001", "SC-TST-002"]


def test_method_support_vs_405():
    support = {"/api/articles/10/": {"view": "v", "view_type": "ViewSet", "allowed_methods": ["GET", "PUT"]}}
    out = q.check_method_support([
        make_scenario(id="SC-TST-001", http_method="POST", expected_http_status=201),
        make_scenario(id="SC-TST-002", http_method="PUT", expected_http_status=405, label="negative"),
        make_scenario(id="SC-TST-003", http_method="POST", expected_http_status=405, label="negative"),
    ], support)
    assert [f["senaryo_id"] for f in out] == ["SC-TST-001", "SC-TST-002"]
    assert q.check_method_support([make_scenario()], None) == []


def test_status_plausibility_is_review_only():
    out = q.check_status_plausibility([
        make_scenario(id="SC-TST-001", user_role="anonymous", expected_http_status=403, label="negative",
                      fixture_ref={"user": None, "article": 10}),
        make_scenario(id="SC-TST-002", http_method="PUT", expected_http_status=204),
        make_scenario(id="SC-TST-003", http_method="DELETE", expected_http_status=200),  # 200 DELETE işaretlenmez
    ])
    assert [f["senaryo_id"] for f in out] == ["SC-TST-001", "SC-TST-002"]
    assert {f["onem_derecesi"] for f in out} == {"Bilgi"}


def test_csv_consistency_detects_cell_and_row_differences():
    sc = [make_scenario(), make_scenario(id="SC-TST-002")]
    cols = list(q.expected_csv_row(sc[0]).keys())
    good = pd.DataFrame([q.expected_csv_row(s) for s in sc], columns=cols)
    assert q.check_csv_consistency(sc, good, cols) == []
    bad = good.copy()
    bad.loc[1, "http_method"] = "POST"
    bad = bad.iloc[[1]]
    out = q.check_csv_consistency(sc, bad, cols)
    types = {f["sorun_turu"] for f in out}
    assert {"CSV_SATIR_UYUSMAZLIGI", "CSV_EKSIK_KAYIT", "CSV_DEGER_UYUSMAZLIGI"} <= types
    assert any(f["senaryo_id"] == "SC-TST-002" and f["alan"] == "http_method" for f in out)


def test_empty_findings_frame_keeps_headers():
    df = q.findings_frame([])
    assert df.empty and list(df.columns) == q.FINDING_COLUMNS


def test_findings_frame_sorted_by_severity():
    rows = [q.finding(1, make_scenario(id="SC-TST-002"), "a", "X", "Bilgi", "L", "e", "k", "d"),
            q.finding(0, make_scenario(), "a", "Y", "Kritik", "L", "e", "k", "d")]
    df = q.findings_frame(rows)
    assert list(df["onem_derecesi"]) == ["Kritik", "Bilgi"]
    assert list(df["bulgu_no"]) == ["DQ-001", "DQ-002"]
