"""Yükleme, rota çözümleme ve kapsam analizinin izole birim testleri — H3-02 / Issue #28."""
from __future__ import annotations

import json

import pytest
from conftest import ARTICLES, USERS, make_scenario

from scenario_eda import coverage as cov
from scenario_eda.data import (
    EXPECTATION_FLAW,
    EXPECTATION_INCONSISTENT,
    EXPECTATION_REJECTION,
    EXPECTATION_SUCCESS,
    actor_relation,
    annotate_scenarios,
    expectation_class,
    find_repo_root,
    pygoat_inventory,
    resolve_route,
)


def test_parse_routes_router_and_paths(routes):
    pats = {r.pattern: r.kind for r in routes}
    assert {r.view_name: r.view_module for r in routes} == {
        "PublishView": "views", "BadDetail": "insecure", "ItemViewSet": "views"}
    assert pats == {
        "/api/articles/<int:pk>/publish/": "guvenli_nesne_aksiyonu",
        "/api/insecure/articles/<int:pk>/": "guvensiz_nesne",
        "/api/articles/": "guvenli_koleksiyon",
        "/api/articles/<pk>/": "guvenli_nesne",
    }


@pytest.mark.parametrize("endpoint,pattern,pk", [
    ("/api/articles/", "/api/articles/", None),
    ("/api/articles/5/", "/api/articles/<pk>/", "5"),
    ("/api/articles/5/publish/", "/api/articles/<int:pk>/publish/", "5"),
    ("/api/articles/5/publish", None, None),
    ("/api/other/", None, None),
])
def test_resolve_route(routes, endpoint, pattern, pk):
    r, got_pk = resolve_route(endpoint, routes)
    assert (r.pattern if r else None) == pattern and got_pk == pk


def test_actor_relation_uses_fixture_ownership():
    by_name = {u["fields"]["username"]: u for u in USERS}
    by_pk = {a["pk"]: a for a in ARTICLES}
    assert actor_relation(None, 10, by_name, by_pk) == "anonim"
    assert actor_relation("root", 10, by_name, by_pk) == "yonetici"
    assert actor_relation("u_owner", 10, by_name, by_pk) == "kaynak_sahibi"
    assert actor_relation("u_other", 10, by_name, by_pk) == "sahip_olmayan"
    assert actor_relation("u_other", None, by_name, by_pk) == "kimligi_dogrulanmis"
    assert actor_relation("u_other", 999, by_name, by_pk) == "belirlenemez"
    assert actor_relation("ghost", 10, by_name, by_pk) == "belirlenemez"


def test_expectation_class():
    assert expectation_class("positive", 201, False) == EXPECTATION_SUCCESS
    assert expectation_class("negative", 404, False) == EXPECTATION_REJECTION
    assert expectation_class("negative", 200, True) == EXPECTATION_FLAW
    assert expectation_class("positive", 403, False) == EXPECTATION_INCONSISTENT
    assert expectation_class("positive", "200", False) == EXPECTATION_INCONSISTENT


def _df(records, routes):
    return annotate_scenarios(records, USERS, ARTICLES, routes)


def test_annotate_tolerates_broken_records(routes):
    df = _df([{"id": "SC-TST-001"}, make_scenario(id="SC-TST-002")], routes)
    assert len(df) == 2 and df.loc[0, "endpoint_kind"] == "cozumlenemedi"


def test_method_distribution_reports_all_five_methods_even_if_absent(routes):
    df = _df([make_scenario(), make_scenario(id="SC-TST-002", http_method="PUT")], routes)
    dist = cov.method_distribution(df)
    assert list(dist["deger"]) == ["GET", "POST", "PUT", "PATCH", "DELETE"]
    absent = dist[dist["senaryo_sayisi"] == 0]["deger"].tolist()
    assert absent == ["POST", "PATCH", "DELETE"]
    assert set(dist.loc[dist["senaryo_sayisi"] == 0, "temsil_durumu"]) == {"Temsil edilmiyor"}
    assert dist["yuzde"].sum() == pytest.approx(100.0)


def test_missing_coverage_combination_is_reported(routes, schema):
    # Yalnızca sahip PUT senaryosu var → PATCH sahip "dolaylı", DELETE sahip "kapsanmıyor"
    df = _df([make_scenario(http_method="PUT")], routes)
    m = cov.coverage_matrix(df)

    def cell(kind, method, cond):
        return m[(m.endpoint_turu == kind) & (m.http_metodu == method) & (m.kosul == cond)].iloc[0]

    assert cell("guvenli_nesne", "PUT", "kaynak_sahibi")["durum"] == cov.STATUS_PRESENT
    assert cell("guvenli_nesne", "PATCH", "kaynak_sahibi")["durum"] == cov.STATUS_INDIRECT
    assert cell("guvenli_nesne", "DELETE", "kaynak_sahibi")["durum"] == cov.STATUS_MISSING
    assert cell("guvenli_nesne", "DELETE", "gecersiz_girdi")["durum"] == cov.STATUS_NA
    gaps = cov.coverage_gaps(df, m, schema, USERS, ARTICLES, {"dataset": "t", "target_app": "t"})
    hit = gaps[(gaps.endpoint_turu == "guvenli_nesne") & (gaps.http_metodu == "DELETE")
               & (gaps.kosul == "kaynak_sahibi")]
    assert hit.iloc[0]["siniflandirma"] == cov.GAP_CONFIRMED
    missing_methods = gaps[(gaps.kapsam_boyutu == "HTTP metodu")]["http_metodu"].tolist()
    assert missing_methods == ["GET", "POST", "PATCH", "DELETE"]
    # NA hücreleri boşluk olarak raporlanmaz
    assert not ((gaps.kosul == "gecersiz_girdi") & (gaps.http_metodu == "DELETE")).any()


def test_condition_precedence(routes):
    df = _df([
        make_scenario(id="SC-TST-001", endpoint="/api/articles/99/", fixture_ref={"user": "u_owner", "article": 99},
                      expected_http_status=404, label="negative"),
        make_scenario(id="SC-TST-002", category="INPUT_VALIDATION", http_method="PUT", expected_http_status=400,
                      label="negative"),
        make_scenario(id="SC-TST-003", endpoint="/api/articles/", http_method="DELETE", expected_http_status=405,
                      label="negative", fixture_ref={"user": "u_owner", "article": None}),
    ], routes)
    assert list(df["condition"]) == ["kaynak_yok", "gecersiz_girdi", "metot_desteklenmiyor"]


def test_intentional_flaw_counterpart(routes):
    df = _df([
        make_scenario(id="SC-TST-001", http_method="PUT", fixture_ref={"user": "u_other", "article": 10},
                      user_role="user", expected_http_status=403, label="negative"),
        make_scenario(id="SC-TST-002", http_method="PUT", endpoint="/api/insecure/articles/10/", user_role="user",
                      fixture_ref={"user": "u_other", "article": 10}, label="negative", is_intentional_flaw=True),
    ], routes)
    sc = [{"id": "SC-TST-002", "flaw_explanation": "BOLA. Güvenli uçta beklenen 403."}]
    t = cov.intentional_flaws(df, sc)
    assert t.iloc[0]["guvenli_karsilik_idleri"] == "SC-TST-001"
    assert t.iloc[0]["aciklama_karsilik_uyumu"] == "Uyumlu"


def test_pygoat_inventory_counts_only_real_records(tmp_path):
    d = tmp_path / "pygoat"
    d.mkdir()
    (d / "README.md").write_text("notlar", encoding="utf-8")
    assert pygoat_inventory(d)["scenario_records"] == 0
    (d / "s.json").write_text(json.dumps({"scenarios": [{"id": 1}, {"id": 2}]}), encoding="utf-8")
    inv = pygoat_inventory(d)
    assert inv["scenario_records"] == 2 and inv["data_files"] == ["s.json"]
    assert pygoat_inventory(tmp_path / "yok")["dir_exists"] is False


def test_find_repo_root_env_var_errors(monkeypatch, tmp_path):
    monkeypatch.setenv("H302_REPO_ROOT", str(tmp_path))
    with pytest.raises(FileNotFoundError, match="H302_REPO_ROOT"):
        find_repo_root()
    monkeypatch.delenv("H302_REPO_ROOT")
    with pytest.raises(FileNotFoundError):
        find_repo_root(tmp_path)


def test_django_resolution_degrades_gracefully(tmp_path):
    from scenario_eda.data import django_method_support

    support, note = django_method_support(tmp_path, ["/api/articles/"])  # ayar modülü yok
    assert support is None and "atlandı" in note
