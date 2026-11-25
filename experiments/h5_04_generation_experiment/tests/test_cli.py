"""H5-04 CLI testleri — Issue #42."""
from experiments.h5_04_generation_experiment import __main__ as cli
from experiments.h5_04_generation_experiment import experiment


def test_verify_clean_returns_0(capsys):
    assert cli.main(["verify"]) == 0


def test_run_writes_reports_even_when_env_down(tmp_path, monkeypatch):
    monkeypatch.setattr(experiment, "check_environment", lambda *a, **k: (False, "ortam yok"))
    rc = cli.main(["run", "--baselines", "rule_based", "--out", str(tmp_path), "--no-logs"])
    assert rc == 0
    for name in ("results.json", "per_scenario.csv", "metrics.csv", "comparison.md"):
        assert (tmp_path / "results" / name).exists()


def test_run_returns_2_when_manifest_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(cli.manifest, "MANIFEST", tmp_path / "yok.json")
    rc = cli.main(["run", "--baselines", "rule_based", "--out", str(tmp_path), "--no-logs"])
    assert rc == 2
