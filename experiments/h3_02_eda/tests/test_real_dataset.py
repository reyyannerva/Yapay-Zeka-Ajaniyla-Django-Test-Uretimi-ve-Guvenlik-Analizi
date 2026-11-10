"""Gerçek H3-01 veri kümesi üzerinde doğrulama ve yeniden üretilebilirlik testleri — H3-02 / Issue #28.

Beklenen sayılar test içinde SABİT YAZILMAZ; kanonik JSON'dan bağımsız olarak yeniden hesaplanır
ve analiz paketinin çıktılarıyla karşılaştırılır.
"""
from __future__ import annotations

import json
from collections import Counter

import pandas as pd
import pytest
from conftest import PKG_ROOT, REPO_ROOT

from scenario_eda import coverage as cov
from scenario_eda import load_context, report

REPORTS = PKG_ROOT / "reports"


@pytest.fixture(scope="module")
def ctx():
    return load_context(REPO_ROOT)


@pytest.fixture(scope="module")
def raw():
    return json.loads((REPO_ROOT / "benchmarks/drf_fixtures/scenarios/scenarios.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def tables(ctx):
    return report.build_report_tables(ctx)


def test_statistics_match_raw_json(ctx, raw, tables):
    sc = raw["scenarios"]
    assert len(ctx.df) == len(sc)
    md = tables["method_distribution"].set_index("deger")["senaryo_sayisi"].to_dict()
    raw_methods = Counter(s["http_method"] for s in sc)
    assert md == {m: raw_methods.get(m, 0) for m in ("GET", "POST", "PUT", "PATCH", "DELETE")}
    cat = tables["category_distribution"].set_index("deger")["senaryo_sayisi"]
    assert cat[cat > 0].to_dict() == dict(Counter(s["category"] for s in sc))
    st = tables["status_code_distribution"].set_index("deger")["senaryo_sayisi"]
    assert st[st > 0].to_dict() == dict(Counter(s["expected_http_status"] for s in sc))
    lab = tables["class_distribution"]
    lab = lab[lab["boyut"] == "label"].set_index("deger")["senaryo_sayisi"].to_dict()
    assert lab == dict(Counter(s["label"] for s in sc))
    flaws = sorted(s["id"] for s in sc if s["is_intentional_flaw"])
    assert sorted(tables["intentional_flaws"]["senaryo_id"]) == flaws


def test_all_five_methods_assessed(tables):
    assert list(tables["method_distribution"]["deger"]) == ["GET", "POST", "PUT", "PATCH", "DELETE"]
    authz = tables["authorization_coverage"]
    assert set(authz["http_metodu"]) == {"PUT", "PATCH", "DELETE"}


def test_findings_reference_real_ids(tables, raw):
    ids = {s["id"] for s in raw["scenarios"]}
    f = tables["data_quality_findings"]
    assert set(f["senaryo_id"].dropna()) <= ids
    for col in ("senaryo_idleri",):
        used = {i for v in tables["coverage_matrix"][col] for i in str(v).split(";") if i}
        assert used <= ids


def test_pygoat_separation(tables, ctx):
    src = tables["source_comparison"].set_index("kaynak")
    files = [p for p in (REPO_ROOT / "benchmarks/pygoat").rglob("*") if p.is_file()]
    data_files = [p for p in files if p.suffix.lower() in {".json", ".csv", ".yaml", ".yml", ".jsonl"}]
    assert ctx.pygoat["data_files"] == [p.name for p in data_files]
    if not data_files:
        assert int(src.loc["PyGoat", "senaryo_kaydi"]) == 0
        assert pd.isna(src.loc["PyGoat", "http_metodu"])
    assert int(src.loc["Kontrollü Django/DRF fixture", "senaryo_kaydi"]) == len(ctx.df)
    assert set(ctx.df["source"]) == {"Kontrollü Django/DRF fixture"}


def test_csv_consistency_check_ran(tables):
    inv = tables["data_quality_checks"].set_index("kontrol_katmani")
    assert inv.loc["JSON/CSV tutarlılığı", "durum"] == "Çalıştırıldı"
    assert inv.loc["JSON Schema", "durum"] == "Çalıştırıldı"


def test_every_scenario_maps_to_a_coverage_cell(ctx):
    assert cov.unmodelled_scenarios(ctx.df).empty


@pytest.mark.parametrize("fname,key", sorted(report.REPORT_FILES.items()))
def test_committed_reports_are_reproducible(tables, fname, key, tmp_path):
    path = REPORTS / fname
    assert path.is_file(), f"{fname} depoda yok; notebook'u çalıştırın."
    report.write_csv(tables[key], tmp_path / fname)
    assert (tmp_path / fname).read_text(encoding="utf-8") == path.read_text(encoding="utf-8"), (
        f"{fname} güncel değil; notebook'u yeniden çalıştırın.")


def test_committed_summary_is_reproducible(ctx, tables):
    committed = (REPORTS / report.SUMMARY_FILE).read_text(encoding="utf-8")
    assert report.render_summary(ctx, tables) == committed
