"""Katman B üretici girdilerini (etiket maskeli görünüm) hazırlar — H5-05 / Issue #43.

``layer_b/generator_inputs/`` altına yazılır:
* ``reference_requirements.json`` — ground truth'un etiket maskeli görünümü (``reference.reference_view``)
* ``scenarios.json`` — senaryoların maskeli görünümü (``reference.scenario_view``)

Her iki dosya da ``reference.assert_no_label_leak`` ile doğrulanır; donmuş ground truth'un özeti
``FROZEN.json`` ile karşılaştırılır (üretim öncesi dondurma kanıtı).
"""
from __future__ import annotations

import json

from agent.evaluation import manifest as mf

from . import reference
from .config import LAYER_B, LAYER_B_FILES, LAYER_B_INPUTS


def verify_frozen() -> list[str]:
    frozen = mf.load_json(LAYER_B_FILES["frozen"])
    problems = []
    for rel_path, digest in frozen["sha256"].items():
        p = LAYER_B / rel_path
        if not p.exists():
            problems.append(f"eksik: {rel_path}")
        elif mf.sha256(p) != digest:
            problems.append(f"değişmiş: {rel_path}")
    return problems


def prepare() -> dict:
    problems = verify_frozen()
    if problems:
        raise mf.IntegrityError("Katman B donmuş girdileri doğrulanamadı: " + "; ".join(problems))
    gt = mf.load_json(LAYER_B_FILES["ground_truth"])
    sc = mf.load_json(LAYER_B_FILES["scenarios"])
    ref_view = reference.reference_view(gt)
    sc_view = reference.scenario_view(sc, gt)
    reference.assert_no_label_leak(ref_view)
    reference.assert_no_label_leak(sc_view)
    LAYER_B_INPUTS.mkdir(parents=True, exist_ok=True)
    out = {"reference_requirements.json": ref_view, "scenarios.json": sc_view}
    for name, doc in out.items():
        (LAYER_B_INPUTS / name).write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                                           encoding="utf-8", newline="\n")
    return {name: mf.sha256(LAYER_B_INPUTS / name) for name in out}
