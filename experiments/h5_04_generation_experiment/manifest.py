"""Dondurulmuş dev deney manifesti — H5-04 / Issue #42.

#42, kural tabanlı (#30) ve LLM (#31) üreticilerini **geliştirme kümesinde** (split.json
'development', 20 senaryo) karşılaştırır. Mühürlü/bağımsız test kümesine (test_set.json, 18 senaryo)
**dokunulmaz** (sızıntı yasağı). 5 HTTP metodunun tamamı ve bilinen güvenlik açıkları mühürlü kümede
#32 (H3-06) ile değerlendirilir; bu deney onu tamamlar.

Manifest; dev senaryo kimliklerini, ground truth sürümü/özetini, kapsamı ve iki baseline'ın donmuş
artefakt özetlerini (SHA-256, LF-normalleştirilmiş) sabitler. ``agent.evaluation.manifest`` (#32)
yardımcıları **değiştirilmeden** yeniden kullanılır.
"""
from __future__ import annotations

import json
from pathlib import Path

from agent.evaluation import manifest as mf

OUT = mf.REPO / "experiments" / "h5_04_generation_experiment"
MANIFEST = OUT / "manifest.json"
SPLIT = mf.REPO / "benchmarks" / "reference_cases" / "split.json"

MANIFEST_VERSION = "1.0.0"


def DEV_IDS(path: Path = SPLIT) -> list[str]:
    """split.json'da ``scenario_split == "dev"`` olan senaryo kimlikleri (dosya sırasıyla)."""
    data = mf.load_json(path)
    return [sid for sid, grp in data["scenario_split"].items() if grp == "dev"]


def _baselines() -> dict:
    h304_rep = mf.load_json(mf.H304 / "reports" / "generation_report.json")
    h305_rep = mf.load_json(mf.H305 / "reports" / "generation_report.json")["summary"]
    return {
        "rule_based": {
            "issue": "#30 (H3-04)",
            "generator": h304_rep["generator"],
            "llm_used": False,
            "deterministic": True,
            "reused_from": "experiments/h3_04_rule_based_baseline (#30)",
            "input_sha256_recorded": h304_rep["inputs_sha256"],
            "artifacts_sha256_lf": {mf.rel(p): mf.sha256(p) for p in mf._artifact_files("rule_based")},
        },
        "llm": {
            "issue": "#31 (H3-05)",
            "generator": f"{h305_rep['generator']} v{h305_rep['version']}",
            "model": h305_rep["model"],
            "prompt_version": h305_rep["prompt_version"],
            "temperature_default": mf.LLM_TEMPERATURE,
            "first_pass_only": True,
            "llm_reused_from": "experiments/h3_05_llm_baseline (#31)",
            "reuse_note": "LLM çıktıları H3-05'ten yeniden kullanıldı; bu deneyde Groq'a yeni istek gönderilmedi.",
            "input_sha256_recorded": h305_rep.get("input_sha256"),
            "artifacts_sha256_lf": {mf.rel(p): mf.sha256(p) for p in mf._artifact_files("llm")},
        },
    }


def build() -> dict:
    """Dev deney manifestini üretir; ground truth kaydı olmayan dev senaryosu değerlendirmeyi durdurur."""
    integ = mf.integrity_records()
    if integ.get("ground_truth.json") != mf.sha256(mf.GROUND_TRUTH):
        raise mf.IntegrityError("ground_truth.json INTEGRITY.txt ile uyuşmuyor; manifest dondurulmaz")
    ids = DEV_IDS()
    records = mf.evaluation_records(ids, mf.ground_truth_index())
    return {
        "manifest": "H5-04 dondurulmuş dev deney manifesti",
        "manifest_version": MANIFEST_VERSION,
        "evaluator_version": mf.EVALUATOR_VERSION,
        "issue": "#42",
        "dataset": {
            "split": "development",
            "split_source": mf.rel(SPLIT),
            "ground_truth": mf.rel(mf.GROUND_TRUTH),
            "ground_truth_sha256_lf": mf.sha256(mf.GROUND_TRUTH),
            "integrity_reference": mf.rel(mf.INTEGRITY),
            "hash_method": "SHA-256, CRLF→LF normalleştirilmiş içerik (check_references.py ile aynı)",
            "scenario_count": len(records),
            "scenario_ids": [r["scenario_id"] for r in records],
        },
        "inclusion_criteria": [
            "Yalnızca split.json 'development' kümesindeki 20 senaryo değerlendirilir (H3-03).",
            "Her senaryonun ground_truth.json'da kaydı bulunmalıdır.",
            "Her baseline için senaryoya ait ilk geçiş (onarımsız) donmuş test artefaktı kullanılır.",
        ],
        "exclusion_criteria": [
            "Bağımsız/mühürlü test kümesi (test_set.json, 18 senaryo) bu deneye girmez (sızıntı yasağı).",
            "Bilinen güvenlik açıkları ve PUT/PATCH/DELETE senaryoları mühürlü kümededir; #32'de değerlendirilir.",
            "Hiçbir senaryo sonuca bakılarak çıkarılmaz; veri kümesi değiştirilmez.",
        ],
        "scenarios": records,
        "coverage": mf.coverage(records),
        "baselines": _baselines(),
        "cross_reference": {
            "issue": "#32",
            "evaluation": "experiments/h3_06_baseline_evaluation",
            "note": ("Gerçek güncelleme/silme işlemleri (PUT/PATCH/DELETE, 2xx/4xx) ve bilinen güvenlik "
                     "açıkları mühürlü test kümesinde #32 (H3-06) ile değerlendirilir. Dev kümesinde PUT/DELETE "
                     "yalnızca 405 (method-not-allowed) senaryolarında bulunur, PATCH ise yoktur; bu deney "
                     "(dev kümesi, üretim + çalıştırılabilirlik) #32'yi tamamlar."),
        },
        "contamination_note": (
            "LLM çıktıları H3-05'ten (#31) yeniden kullanıldı; bu deneyde Groq'a yeni istek gönderilmedi. "
            "Kural tabanlı üretici öğrenme/ayar içermez (deterministik). LLM istemi ground truth'un yalnızca "
            "güvenli beklentisini içerir; is_known_flaw istemlere girmez."
        ),
        "focus_note": (
            "Bu deney güvenlik tespiti metriği (TP/FP/TN/FN, F1) ÜRETMEZ: geliştirme kümesinde bilinen açık "
            "yoktur. Odak üretim kalitesi (sözdizimi/toplanma) ve çalıştırılabilirliktir (PASS/FAIL/ERROR/TIMEOUT)."
        ),
    }


def write(path: Path = MANIFEST) -> dict:
    data = build()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return data


def verify(manifest: dict) -> list[str]:
    """Manifesti depodaki güncel dosyalarla karşılaştırır; uyuşmazlık listesi döndürür (boş = geçerli)."""
    problems: list[str] = []
    ds = manifest["dataset"]
    gt_path = mf.REPO / ds["ground_truth"]
    if not gt_path.exists():
        problems.append(f"eksik veri dosyası: {ds['ground_truth']}")
    elif mf.sha256(gt_path) != ds["ground_truth_sha256_lf"]:
        problems.append(f"veri değişmiş: {ds['ground_truth']}")
    try:
        integ = mf.integrity_records(mf.REPO / ds["integrity_reference"])
        if integ.get("ground_truth.json") != ds["ground_truth_sha256_lf"]:
            problems.append("manifest özeti INTEGRITY.txt ile uyuşmuyor")
    except (OSError, ValueError) as exc:
        problems.append(f"INTEGRITY.txt okunamadı: {exc}")
    if not problems:
        current = [r["scenario_id"] for r in mf.evaluation_records(DEV_IDS(), mf.ground_truth_index())]
        if current != ds["scenario_ids"]:
            problems.append("senaryo kimlikleri manifestle uyuşmuyor")
    for name, b in manifest["baselines"].items():
        for p, digest in b["artifacts_sha256_lf"].items():
            path = mf.REPO / p
            if not path.exists():
                problems.append(f"{name}: eksik artefakt {p}")
            elif mf.sha256(path) != digest:
                problems.append(f"{name}: artefakt değişmiş {p}")
    return problems
