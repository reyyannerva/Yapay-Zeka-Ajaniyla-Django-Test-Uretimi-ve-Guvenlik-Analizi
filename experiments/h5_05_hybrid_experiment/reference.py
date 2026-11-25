"""Referans gereksinim ↔ değerlendirme etiketi ayrımı — H5-05 / Issue #43.

Projede H3-03 ``ground_truth.json`` iki rol taşır:

* **Referans gereksinim (üretim girdisi):** beklenen güvenli davranış — ``expected_result`` (+ yöntem, rol).
  H3-04/H3-05 üreticileri ve hibrit birleştirme politikası yalnızca bunu kullanır.
* **Değerlendirme etiketi (yalnızca değerlendirme):** ``is_known_flaw`` ve ``security_finding``.

``reference_view`` etiketleri maskeleyerek üreticiye verilecek görünümü üretir; ``is_known_flaw`` şema
gereği bulunması zorunlu olduğundan tüm kayıtlarda ``False`` yapılır (anlamı yoktur, maskedir).
Senaryo görünümünde de bilerek-hatalı uçta GÖZLENEN kod (``expected_http_status``), ``is_intentional_flaw``
ve ``flaw_explanation`` maskelenir. Bu, H3 baseline'larındaki girdiden daha katı bir sızıntı kontrolüdür.
"""
from __future__ import annotations

import copy

EVAL_ONLY_RECORD_FIELDS = ("is_known_flaw", "security_finding")
EVAL_ONLY_SCENARIO_FIELDS = ("is_intentional_flaw", "flaw_explanation")
MASK_NOTE = ("H5-05: değerlendirme etiketleri maskelenmiştir (is_known_flaw=False maskesi, security_finding yok); "
             "üretim yalnızca expected_result'u kullanır.")


def reference_view(ground_truth: dict) -> dict:
    doc = copy.deepcopy(ground_truth)
    for rec in doc["records"]:
        rec.pop("security_finding", None)
        rec["is_known_flaw"] = False
    doc["label_mask_note"] = MASK_NOTE
    return doc


def scenario_view(scenarios: dict, ground_truth: dict) -> dict:
    secure = {r["scenario_id"]: r for r in ground_truth["records"]}
    doc = copy.deepcopy(scenarios)
    for sc in doc["scenarios"]:
        ref = secure[sc["id"]]
        sc["is_intentional_flaw"] = False
        sc.pop("flaw_explanation", None)
        sc["expected_http_status"] = ref["expected_result"]["secure_status"]
        sc["label"] = ref["label"]
    doc["label_mask_note"] = MASK_NOTE
    return doc


def evaluation_labels(ground_truth: dict) -> dict[str, dict]:
    return {r["scenario_id"]: {"is_known_flaw": bool(r["is_known_flaw"]),
                               "security_finding": r.get("security_finding")} for r in ground_truth["records"]}


def assert_no_label_leak(view: dict) -> None:
    """Üreticiye giden görünümde değerlendirme etiketi kalmadığını doğrular (aksi hâlde ValueError)."""
    for rec in view.get("records", []):
        if rec.get("is_known_flaw") or "security_finding" in rec:
            raise ValueError(f"etiket sızıntısı: {rec['scenario_id']}")
    for sc in view.get("scenarios", []):
        if sc.get("is_intentional_flaw") or "flaw_explanation" in sc:
            raise ValueError(f"etiket sızıntısı: {sc['id']}")
