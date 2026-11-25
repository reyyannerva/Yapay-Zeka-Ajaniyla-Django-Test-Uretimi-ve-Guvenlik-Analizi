"""H5-05 metrik motoru testleri (sentetik veri; çalıştırma yok)."""
from __future__ import annotations

from fractions import Fraction

import pytest

from experiments.h5_05_hybrid_experiment import metrics as M


def gt(sid, method="GET", flaw=False):
    rec = {"scenario_id": sid, "http_method": method, "is_known_flaw": flaw,
           "expected_result": {"secure_status": 403 if flaw else 200}}
    if flaw:
        rec["security_finding"] = {"type": "BOLA", "observed_flawed_status": 200}
    return rec


def row(sid, outcome, method="GET", **kw):
    return {"scenario_id": sid, "http_method": method, "outcome": outcome, "layer": "T",
            "generation_method": "x", "input_hash": kw.pop("input_hash", "h-" + sid),
            "test_count": kw.pop("test_count", 1),
            "executable_tests": kw.pop("executable_tests", 1 if outcome in ("PASS", "FAIL") else 0), **kw}


GT = {g["scenario_id"]: g for g in [gt("S1", flaw=True), gt("S2", flaw=True), gt("S3"), gt("S4"),
                                    gt("S5", "DELETE")]}


def mm(rows, gtx=GT, sealed=frozenset(), attempted=True):
    return M.method_metrics(rows, gtx, set(sealed), attempted)


def test_normal_case():
    r = mm([row("S1", "FAIL"), row("S2", "PASS"), row("S3", "FAIL"), row("S4", "PASS")])
    assert r["confusion"] == {"TP": 1, "FP": 1, "TN": 1, "FN": 1, "EXCLUDED": 0}
    assert r["precision"]["exact"] == "1/2" and r["recall"]["exact"] == "1/2" and r["f1"]["exact"] == "1/2"
    assert r["target_status"]["f1_gte_0_80"] == M.NOT_MET


def test_perfect_detection():
    r = mm([row("S1", "FAIL"), row("S2", "FAIL"), row("S3", "PASS"), row("S4", "PASS")])
    assert r["f1"]["exact"] == "1/1" and r["target_status"]["f1_gte_0_80"] == M.MET
    assert r["target_status"]["first_pass_executable_gte_0_70"] == M.MET


def test_false_positive_only():
    r = mm([row("S3", "FAIL"), row("S4", "PASS")])
    assert r["confusion"]["FP"] == 1
    assert r["precision"]["exact"] == "0/1" and r["precision"]["value"] == 0
    assert r["recall"]["display"] == M.NOT_MEASURABLE  # pozitif yok → payda 0


def test_false_negative():
    r = mm([row("S1", "PASS"), row("S2", "ERROR")])
    assert r["confusion"]["FN"] == 2 and r["recall"]["value"] == 0
    assert r["precision"]["display"] == M.NOT_MEASURABLE and r["f1"]["display"] == M.NOT_MEASURABLE


def test_zero_denominator_is_not_measurable_not_zero():
    r = mm([row("S3", "PASS"), row("S4", "PASS")])
    assert r["f1"]["value"] is None and r["f1"]["display"] == "Ölçülemedi"
    assert r["target_status"]["f1_gte_0_80"] == "Ölçülemedi"


def test_missing_ground_truth_excluded_with_reason():
    r = mm([row("S3", "PASS"), row("SX", "FAIL")])
    assert r["scenarios"] == 1
    assert r["excluded"] == [{"scenario_id": "SX", "reason": "MISSING_GROUND_TRUTH"}]


def test_ineligible_scenario_excluded():
    r = mm([row("S3", "PASS"), row("S4", "NO_ARTIFACT", evaluation_eligibility="ineligible",
                                   ineligibility_reason="BLOCKED")])
    assert r["scenarios"] == 1 and r["excluded"][0]["reason"] == "BLOCKED"


def test_duplicate_findings_counted_once_per_scenario():
    r = mm([row("S1", "FAIL", test_count=3, executable_tests=3, failing_tests=3)])
    assert r["confusion"]["TP"] == 1
    m = M.ground_truth_matches([row("S1", "FAIL", failing_tests=3)], GT)
    assert len(m) == 1 and m[0]["failing_tests_in_scenario"] == 3


def test_same_scenario_twice_rejected():
    with pytest.raises(ValueError, match="birden fazla"):
        mm([row("S1", "FAIL"), row("S1", "PASS")])


def test_pass_is_not_tp_and_fail_is_not_fn():
    assert mm([row("S1", "PASS")])["confusion"]["TP"] == 0
    assert mm([row("S1", "PASS")])["confusion"]["FN"] == 1
    r = mm([row("S1", "FAIL")])
    assert r["confusion"]["FN"] == 0 and r["confusion"]["TP"] == 1


def test_error_vs_timeout_kept_separate():
    assert M.status5("ERROR") == "ERROR" and M.status5("TIMEOUT") == "TIMEOUT"
    assert M.status5("COLLECTION_ERROR") == "ERROR" and M.status5("NO_ARTIFACT") == "NOT_RUN"
    r = mm([row("S3", "ERROR"), row("S4", "TIMEOUT")])
    assert r["status5"] == {"ERROR": 1, "TIMEOUT": 1}
    assert (r["first_pass_executable"]["count"], r["first_pass_executable"]["of"]) == (0, 2)


def test_first_pass_only_corrected_rejected():
    with pytest.raises(ValueError, match="düzeltilmiş"):
        mm([row("S3", "PASS", corrected=True)])


def test_zero_test_attempt_not_measurable():
    r = mm([], attempted=True)
    assert r["first_pass_executable"]["display"] == M.NOT_MEASURABLE
    assert r["target_status"]["first_pass_executable_gte_0_70"] == M.NOT_MEASURABLE


def test_not_attempted_method_is_not_comparable():
    r = mm([row("S3", "NO_ARTIFACT", evaluation_eligibility="ineligible", ineligibility_reason="BLOCKED")],
           attempted=False)
    assert r["target_status"] == {"f1_gte_0_80": M.NOT_COMPARABLE, "first_pass_executable_gte_0_70": M.NOT_COMPARABLE}


def test_missing_method_result_not_comparable():
    c = M.comparability({"rule_based": [row("S3", "PASS")], "llm": []})
    assert c["comparable"] is False and "eksik" in c["reason"]


def test_differing_input_hashes_not_comparable():
    c = M.comparability({"a": [row("S3", "PASS", input_hash="1")], "b": [row("S3", "PASS", input_hash="2")]})
    assert c["comparable"] is False and "S3" in c["reason"]
    assert M.comparability({"a": [row("S3", "PASS")], "b": [row("S3", "FAIL")]})["comparable"] is True


def test_split_violation():
    with pytest.raises(M.SplitViolation):
        mm([row("S3", "PASS")], sealed={"S3"})


def test_wrong_http_method_not_matched():
    r = mm([row("S1", "FAIL", method="POST")])
    assert r["confusion"]["TP"] == 0 and r["excluded"][0]["reason"].startswith("HTTP_METHOD_MISMATCH")


def test_not_run_reason_required_in_output():
    r = mm([row("S3", "NO_ARTIFACT", not_run_reason="NO_ARTIFACT: üretilmedi")])
    assert r["not_run_reasons"] == {"S3": "NO_ARTIFACT: üretilmedi"}


def test_executability_numerator_denominator():
    r = mm([row("S1", "FAIL"), row("S3", "PASS"), row("S4", "SYNTAX_INVALID"), row("S5", "ERROR", method="DELETE")])
    fp = r["first_pass_executable"]
    assert (fp["count"], fp["of"], fp["exact"]) == (2, 4, "1/2")
    assert r["target_status"]["first_pass_executable_gte_0_70"] == M.NOT_MET
    assert Fraction(fp["exact"]) < Fraction(7, 10)


def test_json_csv_consistency():
    summary = {"layers": {"A": {"methods": {"rule_based": mm([row("S1", "FAIL"), row("S3", "PASS")])}}}}
    rows = M.comparison_rows(summary)
    text = M.to_csv(rows, M.CSV_FIELDS)
    assert M.csv_matches_json(text, rows, M.CSV_FIELDS)
    assert not M.csv_matches_json(text.replace("1.0000", "0.9000"), rows, M.CSV_FIELDS)
