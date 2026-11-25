"""H5-05 metrik motoru — #32 tanımlarının üzerine doğrulama ve eşleşme kayıtları.

Temel karışıklık matrisi ve oranlar ``agent.evaluation.metrics`` (H3-06, değiştirilmeden) ile aynıdır:
senaryo düzeyi; FAIL+kusur=TP, FAIL+kusursuz=FP, PASS+kusur=FN, PASS+kusursuz=TN,
teknik sonuç+kusur=FN, teknik sonuç+kusursuz=EXCLUDED. Payda sıfır → ``None`` → "Ölçülemedi".

Bu modül ayrıca şunları garanti eder:

* Ground truth eşleşmesi ``(scenario_id, http_method)`` ikilisiyle yapılır; yöntem uyuşmazsa eşleşme yoktur
  ve satır reddedilir (yanlış yöntem eşleşmesi TP sayılmaz).
* Aynı senaryo bir yöntem için iki kez değerlendirilemez (``ValueError``); bir senaryodaki birden çok
  başarısız doğrulama tek bulgu sayılır (çift sayım yok, senaryo düzeyi birim).
* Ground truth kaydı olmayan veya ``evaluation_eligibility=ineligible`` satırlar matrise girmez,
  gerekçesiyle ``excluded`` listesine yazılır.
* Mühürlü test kümesindeki bir senaryo geliştirme deneyinde görünürse ``SplitViolation``.
* Yalnızca ilk geçiş çıktıları sayılır; ``corrected=True`` satır ilk geçiş metriğine giremez.
* Aynı senaryonun yöntemler arası ``input_hash``'i farklıysa karşılaştırma "Karşılaştırılamadı".
"""
from __future__ import annotations

import csv
import io
import json
from collections import Counter
from fractions import Fraction

from agent.evaluation.metrics import (ALL_OUTCOMES, EXECUTABLE_OUTCOMES, NOT_MEASURABLE, TARGET_EXECUTABILITY,
                                      TARGET_F1, Outcome, as_json, compute, confusion_cell, meets, ratio)

MET = "Karşılandı"
NOT_MET = "Karşılanmadı"
NOT_COMPARABLE = "Karşılaştırılamadı"
STATUS5 = ("PASS", "FAIL", "ERROR", "TIMEOUT", "NOT_RUN")
NOT_RUN_OUTCOMES = ("NO_ARTIFACT", "DUPLICATE_ARTIFACT", "SYNTAX_INVALID", "UNSAFE_BLOCKED")


class SplitViolation(ValueError):
    pass


def status5(outcome: str) -> str:
    """Ayrıntılı sonucu PASS / FAIL / ERROR / TIMEOUT / NOT_RUN'a indirger (TIMEOUT ayrı tutulur)."""
    if outcome in EXECUTABLE_OUTCOMES or outcome == "TIMEOUT":
        return outcome
    if outcome in NOT_RUN_OUTCOMES:
        return "NOT_RUN"
    if outcome in ALL_OUTCOMES:
        return "ERROR"
    raise ValueError(f"bilinmeyen sonuç: {outcome!r}")


def target_status(value: Fraction | None, target: Fraction, comparable: bool = True) -> str:
    if not comparable:
        return NOT_COMPARABLE
    m = meets(value, target)
    return NOT_MEASURABLE if m is None else (MET if m else NOT_MET)


def validate_rows(rows: list[dict], ground_truth: dict[str, dict], sealed_ids: set[str]) -> tuple[list[dict], list[dict]]:
    """Satırları doğrular; (değerlendirilebilir, hariç tutulan) döndürür. Hatalı veri istisna fırlatır."""
    seen: set[str] = set()
    eligible, excluded = [], []
    for r in rows:
        sid = r["scenario_id"]
        if sid in sealed_ids:
            raise SplitViolation(f"mühürlü test kümesi senaryosu geliştirme deneyinde: {sid}")
        if sid in seen:
            raise ValueError(f"senaryo birden fazla kez değerlendirildi: {sid}")
        seen.add(sid)
        if r.get("corrected"):
            raise ValueError(f"düzeltilmiş çıktı ilk geçiş metriğine giremez: {sid}")
        gt = ground_truth.get(sid)
        if gt is None:
            excluded.append({**r, "exclusion_reason": "MISSING_GROUND_TRUTH"})
            continue
        if gt["http_method"] != r["http_method"]:
            excluded.append({**r, "exclusion_reason":
                             f"HTTP_METHOD_MISMATCH: sonuç {r['http_method']} ≠ ground truth {gt['http_method']}"})
            continue
        if r.get("evaluation_eligibility", "eligible") != "eligible":
            excluded.append({**r, "exclusion_reason": r.get("ineligibility_reason") or "INELIGIBLE"})
            continue
        eligible.append(r)
    return eligible, excluded


def ground_truth_matches(rows: list[dict], ground_truth: dict[str, dict]) -> list[dict]:
    """Senaryo başına tek eşleşme kaydı (bulgu çift sayılmaz)."""
    out = []
    for r in rows:
        gt = ground_truth[r["scenario_id"]]
        flaw = bool(gt["is_known_flaw"])
        finding = gt.get("security_finding") or {}
        cell = confusion_cell(flaw, r["outcome"])
        out.append({
            "layer": r.get("layer"), "generation_method": r.get("generation_method"),
            "scenario_id": r["scenario_id"], "http_method": r["http_method"],
            "matched_on": ["scenario_id", "http_method"],
            "gt_is_known_flaw": flaw, "gt_finding_type": finding.get("type") if flaw else None,
            "gt_secure_status": gt["expected_result"]["secure_status"],
            "gt_observed_flawed_status": finding.get("observed_flawed_status") if flaw else None,
            "outcome": r["outcome"], "status": status5(r["outcome"]),
            "predicted_finding": r["outcome"] == "FAIL",
            "observed_status": r.get("observed_status"),
            "failing_tests_in_scenario": r.get("failing_tests", 0),
            "confusion_cell": cell,
        })
    return out


def method_metrics(rows: list[dict], ground_truth: dict[str, dict], sealed_ids: set[str],
                   attempted: bool = True) -> dict:
    """Bir katman × yöntem için metrikler. ``attempted=False`` → üretim denenemedi; tüm oranlar Ölçülemedi."""
    eligible, excluded = validate_rows(rows, ground_truth, sealed_ids)
    if not attempted or not eligible:
        base = compute([])
        base["first_pass_executable"] = {"count": 0, "of": 0, **as_json(None)}
        base["test_level"] = {"tests": 0, "executable": 0, **as_json(None)}
    else:
        base = compute(Outcome(r["scenario_id"], r["http_method"], bool(ground_truth[r["scenario_id"]]["is_known_flaw"]),
                               r["outcome"]) for r in eligible)
        tests = sum(r.get("test_count", 0) for r in eligible)
        execu = sum(r.get("executable_tests", 0) for r in eligible)
        base["test_level"] = {"tests": tests, "executable": execu, **as_json(ratio(execu, tests))}
    f1v = _frac(base["f1"])
    exv = _frac(base["first_pass_executable"])
    base["attempted"] = attempted
    base["excluded"] = [{"scenario_id": e["scenario_id"], "reason": e["exclusion_reason"]} for e in excluded]
    base["status5"] = dict(Counter(status5(r["outcome"]) for r in eligible))
    base["not_run_reasons"] = {r["scenario_id"]: r.get("not_run_reason") for r in eligible
                               if status5(r["outcome"]) == "NOT_RUN"}
    base["target_status"] = {
        "f1_gte_0_80": target_status(f1v, TARGET_F1, attempted),
        "first_pass_executable_gte_0_70": target_status(exv, TARGET_EXECUTABILITY, attempted),
    }
    return base


def _frac(j: dict) -> Fraction | None:
    return None if j.get("exact") is None else Fraction(j["exact"])


def comparability(rows_by_method: dict[str, list[dict]]) -> dict:
    """Yöntemler arası aynı senaryo kümesi ve aynı girdi özeti var mı?"""
    if not rows_by_method or any(not v for v in rows_by_method.values()):
        missing = sorted(k for k, v in rows_by_method.items() if not v)
        return {"comparable": False, "reason": f"yöntem sonucu eksik: {missing}"}
    sets = {m: {r["scenario_id"]: r.get("input_hash") for r in rows} for m, rows in rows_by_method.items()}
    ids = {frozenset(s) for s in sets.values()}
    if len(ids) != 1:
        return {"comparable": False, "reason": "yöntemlerin senaryo kümeleri farklı"}
    diffs = sorted(sid for sid in next(iter(sets.values()))
                   if len({s[sid] for s in sets.values()}) != 1)
    if diffs:
        return {"comparable": False, "reason": f"girdi özeti farklı: {diffs}"}
    return {"comparable": True, "reason": "aynı senaryolar ve aynı girdi özetleri"}


CSV_FIELDS = ("layer", "method", "attempted", "scenarios", "TP", "FP", "TN", "FN", "EXCLUDED", "precision",
              "recall", "f1", "first_pass_executable", "first_pass_executable_exact", "test_level_executable",
              "f1_target", "executability_target")


def comparison_rows(summary: dict) -> list[dict]:
    rows = []
    for layer, methods in summary["layers"].items():
        for m, mm in methods["methods"].items():
            c = mm["confusion"]
            rows.append({
                "layer": layer, "method": m, "attempted": mm["attempted"], "scenarios": mm["scenarios"],
                "TP": c["TP"], "FP": c["FP"], "TN": c["TN"], "FN": c["FN"], "EXCLUDED": c["EXCLUDED"],
                "precision": mm["precision"]["display"], "recall": mm["recall"]["display"],
                "f1": mm["f1"]["display"], "first_pass_executable": mm["first_pass_executable"]["display"],
                "first_pass_executable_exact": f"{mm['first_pass_executable']['count']}/{mm['first_pass_executable']['of']}",
                "test_level_executable": f"{mm['test_level']['executable']}/{mm['test_level']['tests']}",
                "f1_target": mm["target_status"]["f1_gte_0_80"],
                "executability_target": mm["target_status"]["first_pass_executable_gte_0_70"],
            })
    return rows


def to_csv(rows: list[dict], fields) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(fields), lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else (json.dumps(r[k], ensure_ascii=False)
                                                    if isinstance(r.get(k), (dict, list)) else r[k]))
                    for k in fields})
    return buf.getvalue()


def csv_matches_json(csv_text: str, rows: list[dict], fields) -> bool:
    back = list(csv.DictReader(io.StringIO(csv_text)))
    return len(back) == len(rows) and all(
        str("" if r.get(k) is None else r[k]) == b[k] for r, b in zip(rows, back) for k in fields
        if not isinstance(r.get(k), (dict, list)))
