"""H5-04 dev deney orkestrasyonu testleri — Issue #42.

Ortam (env_ok) enjekte edilebilir; env_ok=False iken hiçbir test çalıştırılmaz, dolayısıyla bu
testler Django/sample_app gerektirmez (hızlı ve yan etkisiz).
"""
from experiments.h5_04_generation_experiment import experiment


def test_env_down_runs_nothing_and_is_reported(tmp_path):
    res = experiment.run_experiment(out=tmp_path, timeout=5, baselines=["rule_based"],
                                    keep_logs=False, env_ok=False)
    rows = res["results"]["rule_based"]
    assert rows, "dev senaryoları için satır üretilmeli"
    assert res["environment_check"]["ok"] is False
    # Ortam yokken hiçbir test çalışmaz: PASS/FAIL olmamalı (sahte sonuç yok)
    assert all(r["outcome"] not in ("PASS", "FAIL") for r in rows)
    # Gerçek artefaktı olan senaryolar üreticiye değil ortama yazılır:
    assert any(r["outcome"] == "ENVIRONMENT_ERROR" for r in rows)


def test_unsupported_scenario_is_no_artifact(tmp_path, monkeypatch):
    monkeypatch.setitem(experiment.ADAPTERS, "rule_based", lambda ids: {i: [] for i in ids})
    res = experiment.run_experiment(out=tmp_path, timeout=5, baselines=["rule_based"],
                                    keep_logs=False, env_ok=True)
    rows = res["results"]["rule_based"]
    assert rows and all(r["outcome"] == "NO_ARTIFACT" for r in rows)


def test_f1_not_measurable_on_dev(tmp_path):
    # Dev'de bilinen güvenlik açığı yok → güvenlik F1'i ölçülemez (betimleyici odak).
    res = experiment.run_experiment(out=tmp_path, timeout=5, baselines=["llm"],
                                    keep_logs=False, env_ok=False)
    assert res["metrics"]["llm"]["f1"]["display"] == "Ölçülemedi"


def test_results_cover_all_20_dev_scenarios(tmp_path):
    res = experiment.run_experiment(out=tmp_path, timeout=5, baselines=["rule_based"],
                                    keep_logs=False, env_ok=False)
    ids = [r["scenario_id"] for r in res["results"]["rule_based"]]
    assert len(ids) == 20 and len(set(ids)) == 20
