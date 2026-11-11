"""Dondurulmuş manifest, veri bütünlüğü ve sızıntı denetimi — H3-06 / Issue #32."""
import copy
import json

import pytest

from agent.evaluation import manifest as mf

ANSWER_KEY_TERMS = ("is_known_flaw", "observed_flawed_status", "security_finding", "deviation_kind",
                    "KNOWN_FLAW", "test_set", "split.json")


@pytest.fixture(scope="module")
def committed():
    return mf.load_json(mf.MANIFEST)


def test_committed_manifest_verifies(committed):
    assert mf.verify(committed) == []


def test_manifest_is_reproducible_from_repository(committed):
    assert mf.build() == committed


def test_manifest_matches_integrity_and_test_set(committed):
    ds = committed["dataset"]
    integ = mf.integrity_records()
    assert ds["test_set_sha256_lf"] == integ["test_set.json"]
    assert ds["ground_truth_sha256_lf"] == integ["ground_truth.json"]
    assert ds["scenario_ids"] == mf.load_test_set() and ds["scenario_count"] == 18


def test_known_flaws_and_coverage(committed):
    assert [f["scenario_id"] for f in committed["known_flaws"]] == ["SC-FLW-001", "SC-FLW-002", "SC-FLW-003"]
    cov = committed["coverage"]
    assert cov["by_method"] == {"GET": 1, "POST": 0, "PUT": 7, "PATCH": 4, "DELETE": 6}
    assert cov["missing_methods"] == ["POST"] and "405" in cov["missing_statuses"]
    assert committed["mutation_score"] == "Bu aşamada ölçülmedi"


def test_tampered_dataset_hash_detected(committed):
    bad = copy.deepcopy(committed)
    bad["dataset"]["test_set_sha256_lf"] = "0" * 64
    probs = mf.verify(bad)
    assert any("test_set.json" in p for p in probs)


def test_tampered_artifact_hash_detected(committed):
    bad = copy.deepcopy(committed)
    key = next(iter(bad["baselines"]["llm"]["artifacts_sha256_lf"]))
    bad["baselines"]["llm"]["artifacts_sha256_lf"][key] = "f" * 64
    assert any("artefakt değişmiş" in p for p in mf.verify(bad))


def test_missing_artifact_detected(committed):
    bad = copy.deepcopy(committed)
    bad["baselines"]["rule_based"]["artifacts_sha256_lf"]["experiments/yok.py"] = "0" * 64
    assert any("eksik artefakt" in p for p in mf.verify(bad))


def test_hash_is_line_ending_independent(tmp_path):
    raw = mf.TEST_SET.read_bytes().replace(b"\r\n", b"\n")
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_bytes(raw)
    b.write_bytes(raw.replace(b"\n", b"\r\n"))
    assert mf.sha256(a) == mf.sha256(b) == mf.integrity_records()["test_set.json"]


def test_test_set_with_duplicate_ids_rejected(tmp_path):
    p = tmp_path / "ts.json"
    p.write_text(json.dumps({"scenario_ids": ["A", "A"], "count": 2}), encoding="utf-8")
    with pytest.raises(mf.IntegrityError):
        mf.load_test_set(p)


def test_test_set_count_mismatch_rejected(tmp_path):
    p = tmp_path / "ts.json"
    p.write_text(json.dumps({"scenario_ids": ["A"], "count": 2}), encoding="utf-8")
    with pytest.raises(mf.IntegrityError):
        mf.load_test_set(p)


def test_scenario_without_ground_truth_rejected():
    with pytest.raises(mf.IntegrityError, match="ground truth"):
        mf.evaluation_records(["SC-YOK-999"], mf.ground_truth_index())


def test_label_field_is_not_part_of_evaluation_records(committed):
    for r in committed["scenarios"]:
        assert "label" not in r
    # SC-AUT-002 negatif etiketli ama kusursuzdur: gerçek sınıf is_known_flaw'dan gelir.
    rec = {r["scenario_id"]: r for r in committed["scenarios"]}["SC-AUT-002"]
    assert rec["is_known_flaw"] is False


def test_no_answer_key_leakage_into_llm_prompts():
    prompts = sorted((mf.H305 / "prompts_sent").glob("*.txt"))
    assert len(prompts) == 38
    for p in prompts:
        text = p.read_text(encoding="utf-8")
        assert not [t for t in ANSWER_KEY_TERMS if t in text], p.name


def test_llm_prompts_never_contain_flawed_observed_status_for_flaws(committed):
    for f in committed["known_flaws"]:
        text = (mf.H305 / "prompts_sent" / f"{f['scenario_id']}.txt").read_text(encoding="utf-8")
        assert f"BEKLENEN HTTP durum kodu: {f['secure_status']}" in text
        if f["observed_flawed_status"] != f["secure_status"]:
            assert f"durum kodu: {f['observed_flawed_status']}" not in text


def _content_digests(path):
    import hashlib
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    return {hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b"\n", b"\r\n")).hexdigest()}


def test_both_generators_used_identical_input_content(committed):
    """Aynı girdi koşulu: H3-04 ve H3-05'in kaydettiği girdi özetleri, depodaki aynı içeriğin LF veya CRLF
    kodlamasına karşılık gelir (H3-05 Windows'ta CRLF çalışma kopyasıyla çalıştırılmıştır)."""
    files = {"endpoint_summary.json": mf.H304 / "endpoint_summary.json",
             "ground_truth.json": mf.GROUND_TRUTH,
             "scenarios.json": mf.REPO / "benchmarks" / "drf_fixtures" / "scenarios" / "scenarios.json"}
    llm = committed["baselines"]["llm"]["input_sha256_recorded"]
    rule = committed["baselines"]["rule_based"]["input_sha256_recorded"]
    for name, path in files.items():
        assert llm[name] in _content_digests(path), name
        rule_key = next(k for k in rule if k.endswith(name))
        assert rule[rule_key] in _content_digests(path), name
