"""Metrik tanımları ve sınır durumları — H3-06 / Issue #32 (split.md §4.3)."""
from fractions import Fraction

import pytest

from agent.evaluation import metrics as M
from agent.evaluation.metrics import Outcome, compute


def rows(spec):
    return [Outcome(f"S-{i}", "PUT", flaw, out) for i, (flaw, out) in enumerate(spec)]


@pytest.mark.parametrize("flaw,outcome,cell", [
    (True, "FAIL", "TP"), (True, "PASS", "FN"), (False, "FAIL", "FP"), (False, "PASS", "TN"),
    (True, "NO_ARTIFACT", "FN"), (True, "SYNTAX_INVALID", "FN"), (True, "ERROR", "FN"), (True, "TIMEOUT", "FN"),
    (True, "COLLECTION_ERROR", "FN"), (True, "ENVIRONMENT_ERROR", "FN"), (True, "UNSAFE_BLOCKED", "FN"),
    (True, "DUPLICATE_ARTIFACT", "FN"),
    (False, "NO_ARTIFACT", "EXCLUDED"), (False, "SYNTAX_INVALID", "EXCLUDED"), (False, "ERROR", "EXCLUDED"),
    (False, "TIMEOUT", "EXCLUDED"), (False, "COLLECTION_ERROR", "EXCLUDED"), (False, "ENVIRONMENT_ERROR", "EXCLUDED"),
])
def test_confusion_cell_follows_split_md_4_3(flaw, outcome, cell):
    assert M.confusion_cell(flaw, outcome) == cell


def test_technical_error_on_clean_scenario_is_never_false_positive():
    m = compute(rows([(False, "ERROR"), (False, "SYNTAX_INVALID"), (True, "FAIL")]))
    assert m["confusion"] == {"TP": 1, "FP": 0, "TN": 0, "FN": 0, "EXCLUDED": 2}
    assert m["first_pass_executable"]["exact"] == "1/3"


def test_unknown_outcome_and_non_bool_flaw_rejected():
    with pytest.raises(ValueError):
        M.confusion_cell(True, "WEIRD")
    with pytest.raises(TypeError):
        M.confusion_cell("true", "PASS")  # label/dize kabul edilmez; yalnızca is_known_flaw bool


def test_duplicate_scenario_rejected():
    with pytest.raises(ValueError, match="birden fazla"):
        compute([Outcome("S-1", "GET", True, "FAIL"), Outcome("S-1", "GET", True, "PASS")])


def test_precision_not_measurable_when_no_positive_prediction():
    m = compute(rows([(True, "PASS"), (False, "PASS")]))
    assert m["precision"] == {"value": None, "exact": None, "display": "Ölçülemedi"}
    assert m["recall"]["exact"] == "0/1"
    assert m["f1"]["display"] == "Ölçülemedi"
    assert m["targets"]["f1_gte_0_80"] is None


def test_recall_not_measurable_without_positive_class():
    m = compute(rows([(False, "PASS"), (False, "FAIL")]))
    assert m["recall"]["display"] == "Ölçülemedi"
    assert m["precision"]["value"] == 0.0
    assert m["f1"]["display"] == "Ölçülemedi"


def test_f1_not_measurable_when_precision_and_recall_zero():
    m = compute(rows([(True, "PASS"), (False, "FAIL")]))
    assert m["precision"]["value"] == 0.0 and m["recall"]["value"] == 0.0
    assert m["f1"]["display"] == "Ölçülemedi"


def test_empty_evaluation_is_not_measurable_not_zero():
    m = compute([])
    for k in ("precision", "recall", "f1"):
        assert m[k]["value"] is None
    assert m["first_pass_executable"]["display"] == "Ölçülemedi"
    assert m["targets"] == {"f1_gte_0_80": None, "first_pass_executable_gte_0_70": None}


def test_perfect_detection():
    m = compute(rows([(True, "FAIL"), (True, "FAIL"), (False, "PASS")]))
    assert (m["precision"]["exact"], m["recall"]["exact"], m["f1"]["exact"]) == ("1/1", "1/1", "1/1")


def test_f1_threshold_compared_exactly_not_by_float():
    # TP=2, FP=0, FN=1 → P=1, R=2/3, F1=4/5 tam olarak hedefe eşittir.
    m = compute(rows([(True, "FAIL"), (True, "FAIL"), (True, "PASS")] + [(False, "PASS")] * 15))
    assert m["f1"]["exact"] == "4/5"
    assert m["targets"]["f1_gte_0_80"] is True
    assert M.meets(Fraction(4, 5) - Fraction(1, 10**9), M.TARGET_F1) is False


def test_executability_threshold_boundary():
    seven = rows([(False, "PASS")] * 7 + [(False, "ERROR")] * 3)
    assert compute(seven)["targets"]["first_pass_executable_gte_0_70"] is True
    six = rows([(False, "PASS")] * 6 + [(False, "ERROR")] * 4)
    assert compute(six)["targets"]["first_pass_executable_gte_0_70"] is False


def test_syntax_and_collection_rates():
    m = compute(rows([(False, "PASS"), (False, "SYNTAX_INVALID"), (False, "COLLECTION_ERROR"),
                      (False, "NO_ARTIFACT"), (False, "ERROR")]))
    assert (m["syntax_valid"]["count"], m["syntax_valid"]["of"]) == (3, 4)  # artefaktı olmayan payda dışı
    assert m["collected"]["count"] == 2 and m["first_pass_executable"]["count"] == 1
    assert m["pytest_summary"] == {"PASS": 1, "NOT_RUN": 2, "ERROR": 2}


def test_by_method_breakdown():
    m = compute([Outcome("A", "PUT", True, "FAIL"), Outcome("B", "GET", True, "PASS"),
                 Outcome("C", "GET", False, "PASS")])
    assert m["by_method"]["GET"]["FN"] == 1 and m["by_method"]["GET"]["TN"] == 1
    assert m["by_method"]["PUT"]["TP"] == 1


def test_negative_counts_rejected():
    with pytest.raises(ValueError):
        M.ratio(-1, 2)
