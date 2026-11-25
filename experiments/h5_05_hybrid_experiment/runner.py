"""Deney yürütücüsü (manifest → aday → hibrit → çalıştırma → metrik) — H5-05 / Issue #43.

* Çalıştırma ``agent.evaluation.execution.evaluate_scenario`` (#32) ile yapılır; modül değiştirilmez.
  Katman B için hedef uygulama yolu (``execution.SAMPLE_APP``) koşu süresince geçici olarak değiştirilir
  ve ``finally`` ile geri alınır.
* Her (katman, yöntem, senaryo) sonucu ``results/checkpoints/`` altına atomik yazılır. ``--resume``
  yalnızca artefakt özeti aynı olan kontrol noktalarını yeniden kullanır; değişmişse yeniden çalıştırır.
* Test düzeyi sonuçlar senaryonun ``probe.json`` kaydından okunur (birden çok test fonksiyonu olabilir).
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from agent.evaluation import execution
from agent.evaluation import manifest as mf
from agent.evaluation.artifacts import Artifact, llm_artifacts, rule_based_artifacts

from . import config as C
from . import hybrid, layer_b_inputs, reference
from .normalize import routes_from_endpoint_summary

LLM_BLOCKED_REASON = ("LLM_GENERATION_BLOCKED: Katman B için LLM üretimi yapılamadı — oturumda Groq API "
                      "kimlik bilgisi yok ve api.groq.com ağ politikasınca erişilemez. İstemler etiketsiz "
                      "olarak kaydedildi (layer_b/generated/llm/prompts_sent); arşiv çıktısı yeni koşu gibi "
                      "sunulmaz ve sessiz model değişimi yapılmaz.")


def _canon(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _h(obj) -> str:
    return hashlib.sha256(_canon(obj).encode("utf-8")).hexdigest()


def sealed_ids() -> set[str]:
    split = mf.load_json(mf.REF / "split.json")
    return {sid for sid, part in split["scenario_split"].items() if part == "test"}


# --------------------------------------------------------------------------- katman tanımları

def _layer_a() -> dict:
    from experiments.h5_04_generation_experiment import manifest as h504
    man = mf.load_json(C.H504_MANIFEST)
    problems = h504.verify(man)
    if problems:
        raise mf.IntegrityError("H5-04 manifesti doğrulanamadı: " + "; ".join(problems))
    ids = [r["scenario_id"] for r in man["scenarios"]]
    gt = {r["scenario_id"]: r for r in mf.load_json(mf.GROUND_TRUTH)["records"] if r["scenario_id"] in ids}
    scen_path = mf.REPO / "benchmarks" / "drf_fixtures" / "scenarios" / "scenarios.json"
    scen = {s["id"]: s for s in mf.load_json(scen_path)["scenarios"] if s["id"] in ids}
    ep_path = C.REPO / "experiments" / "h3_04_rule_based_baseline" / "endpoint_summary.json"
    h305 = mf.load_json(mf.H305 / "reports" / "generation_report.json")["summary"]
    return {
        "layer": "A", "dataset_version": f"h3-03 ground_truth sha256:{mf.sha256(mf.GROUND_TRUTH)[:12]} / split dev",
        "split_name": "dev", "ids": ids, "ground_truth": gt, "scenarios": scen,
        "endpoint_summary_path": ep_path, "target_app": C.SAMPLE_APP,
        "candidates": {"rule_based": rule_based_artifacts(ids), "llm": llm_artifacts(ids)},
        "llm": {"status": "ARCHIVED_FIRST_PASS", "model_id": h305["model"], "prompt_version": h305["prompt_version"],
                "source": mf.rel(mf.H305 / "raw_responses"),
                "note": "H3-05 (#31) ilk geçiş ham yanıtları; H5-05'te yeniden üretilmedi (arşiv)."},
        "rule_based_source": mf.rel(mf.H304 / "generated_tests"),
    }


def _layer_b() -> dict:
    layer_b_inputs.prepare()
    gt_doc = mf.load_json(C.LAYER_B_FILES["ground_truth"])
    ids = [r["scenario_id"] for r in gt_doc["records"]]
    gt = {r["scenario_id"]: r for r in gt_doc["records"]}
    scen = {s["id"]: s for s in mf.load_json(C.LAYER_B_INPUTS / "scenarios.json")["scenarios"]}
    llm_report = C.LAYER_B_LLM / "reports" / "generation_report.json"
    if llm_report.exists():  # gerçek Groq üretimi yapıldıysa (bkz. rapor §15) — arşiv değil, bu katmanın yeni koşusu
        summ = mf.load_json(llm_report)["summary"]
        llm_cands = llm_artifacts(ids, base=C.LAYER_B_LLM)
        llm_info = {"status": "GENERATED", "model_id": summ["model"], "prompt_version": summ["prompt_version"],
                    "source": mf.rel(C.LAYER_B_LLM / "raw_responses"), "note": "H5-05 Katman B için yeni Groq koşusu."}
    else:
        llm_cands = {i: [] for i in ids}
        llm_info = {"status": "BLOCKED", "model_id": None, "prompt_version": "pytest_v1",
                    "source": mf.rel(C.LAYER_B_LLM / "prompts_sent"), "note": LLM_BLOCKED_REASON}
    return {
        "layer": "B", "dataset_version": f"{gt_doc.get('dataset', 'h5-05-layer-b-controlled')} "
                                         f"sha256:{mf.sha256(C.LAYER_B_FILES['ground_truth'])[:12]}",
        "split_name": "dev-controlled-extension", "ids": ids, "ground_truth": gt, "scenarios": scen,
        "endpoint_summary_path": C.LAYER_B_FILES["endpoints"], "target_app": C.LAYER_B_FILES["target_app"],
        "candidates": {"rule_based": rule_based_artifacts(ids, base=C.LAYER_B_RB), "llm": llm_cands},
        "llm": llm_info,
        "rule_based_source": mf.rel(C.LAYER_B_RB / "generated_tests"),
    }


def load_layer(name: str) -> dict:
    return _layer_a() if name == "A" else _layer_b()


def reference_for(layer: dict, sid: str) -> hybrid.Reference:
    gt, sc = layer["ground_truth"][sid], layer["scenarios"][sid]
    return hybrid.Reference(sid, gt["http_method"], sc["endpoint"], gt["user_role"],
                            (sc.get("fixture_ref") or {}).get("user"), gt["expected_result"]["secure_status"],
                            f"{sid}:expected_result")


# --------------------------------------------------------------------------- manifest

def manifest_rows(layer: dict, method: str, artifacts: dict[str, list[Artifact]]) -> list[dict]:
    ep_hash = mf.sha256(layer["endpoint_summary_path"])
    ref_view = {r["scenario_id"]: r for r in reference.reference_view(
        {"records": list(layer["ground_truth"].values())})["records"]}
    rows = []
    llm = layer["llm"]
    for sid in layer["ids"]:
        gt, sc = layer["ground_truth"][sid], layer["scenarios"][sid]
        ref_rec = ref_view[sid]
        arts = artifacts.get(sid, [])
        params, model, prompt, gen_version = {}, None, None, None
        if method == "rule_based":
            gen_version, src = "agent.test_generation.rule_based (H3-04)", layer["rule_based_source"]
        elif method == "llm":
            gen_version, model, prompt, src = "agent.test_generation.llm (H3-05)", llm["model_id"], llm["prompt_version"], llm["source"]
            params = {"temperature": mf.LLM_TEMPERATURE, "provider": C.LLM_PROVIDER}
        else:
            gen_version, src = f"{C.HYBRID_GENERATOR_ID} v{C.HYBRID_VERSION}", "hybrid_decisions.jsonl"
            params = {"policy": "reference-consistency → duplicate(rule) → richer-assertions → rule tie-break"}
        blocked = method == "llm" and llm["status"] == "BLOCKED"
        rows.append({
            "experiment_id": C.EXPERIMENT_ID, "layer": layer["layer"], "dataset_version": layer["dataset_version"],
            "split_name": layer["split_name"], "scenario_id": sid, "scenario_group": sid.rsplit("-", 1)[0],
            "endpoint": sc["endpoint"], "http_method": gt["http_method"],
            "auth_requirement": "anonymous" if gt["user_role"] == "anonymous" else "authenticated",
            "role_requirement": gt["user_role"], "input_validation_category": sc.get("category"),
            "reference_requirement_id": f"{sid}:expected_result",
            "input_hash": _h({"scenario": {k: sc[k] for k in ("id", "http_method", "endpoint", "user_role",
                                                                "request_input", "fixture_ref")},
                              "reference": ref_rec}),
            "ast_summary_hash": ep_hash, "reference_json_hash": _h(ref_rec),
            "generation_method": method, "generator_version": gen_version, "model_id": model,
            "prompt_version": prompt, "generation_parameters": params,
            "source_artifact": arts[0].origin if arts else (llm["source"] if blocked else src),
            "artifact_count": len(arts),
            "evaluation_eligibility": "ineligible" if blocked else "eligible",
            "ineligibility_reason": LLM_BLOCKED_REASON if blocked else None,
        })
    return rows


# --------------------------------------------------------------------------- çalıştırma

def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, path)


def _test_level(log_dir: Path, sid: str) -> dict:
    probe = log_dir / sid / "probe.json"
    if not probe.exists():
        return {"test_count": 0, "executable_tests": 0, "failing_tests": 0, "tests": []}
    recs = json.loads(probe.read_text(encoding="utf-8"))["records"]
    tests = {}
    for r in recs:
        if r["when"] == "collect":
            continue
        t = tests.setdefault(r["nodeid"], {"nodeid": r["nodeid"], "status": "PASS", "exc_type": None})
        if r["outcome"] == "failed":
            if r["when"] == "call" and r["exc_type"] == "AssertionError":
                t["status"] = "FAIL" if t["status"] == "PASS" else t["status"]
            else:
                t["status"], t["exc_type"] = "ERROR", r["exc_type"]
        elif r["outcome"] == "skipped":
            t["status"] = "ERROR"
            t["exc_type"] = t["exc_type"] or "Skipped"
    vals = list(tests.values())
    return {"test_count": len(vals), "executable_tests": sum(1 for t in vals if t["status"] in ("PASS", "FAIL")),
            "failing_tests": sum(1 for t in vals if t["status"] == "FAIL"), "tests": vals}


def execute(layer: dict, method: str, artifacts: dict[str, list[Artifact]], manifest: list[dict],
            out: Path, timeout: int, resume: bool) -> list[dict]:
    from .metrics import status5
    ck_dir = out / "checkpoints" / layer["layer"] / method
    log_dir = out / "logs" / layer["layer"] / method
    by_sid = {m["scenario_id"]: m for m in manifest}
    saved_app = execution.SAMPLE_APP
    execution.SAMPLE_APP = layer["target_app"]
    try:
        env_ok, env_msg = execution.check_environment()
        rows = []
        with tempfile.TemporaryDirectory(prefix="h505_") as tmp:
            for sid in layer["ids"]:
                arts = artifacts.get(sid, [])
                art_hash = _h([a.source for a in arts])
                ck = ck_dir / f"{sid}.json"
                if resume and ck.exists():
                    prev = json.loads(ck.read_text(encoding="utf-8"))
                    if prev.get("artifacts_hash") == art_hash and prev.get("input_hash") == by_sid[sid]["input_hash"]:
                        rows.append(prev)
                        continue
                gt = layer["ground_truth"][sid]
                rec = {"scenario_id": sid, "http_method": gt["http_method"], "user_role": gt["user_role"],
                       "secure_status": gt["expected_result"]["secure_status"],
                       "is_known_flaw": bool(gt["is_known_flaw"]),
                       "deviation_kind": (gt.get("security_finding") or {}).get("deviation_kind")}
                if by_sid[sid]["evaluation_eligibility"] != "eligible":
                    res = execution.evaluate_scenario(rec, [], Path(tmp), None, timeout, env_ok)
                    res["evidence"] = by_sid[sid]["ineligibility_reason"]
                    tl = {"test_count": 0, "executable_tests": 0, "failing_tests": 0, "tests": []}
                else:
                    shutil.rmtree(log_dir / sid, ignore_errors=True)  # bayat probe kaydı okunmasın
                    res = execution.evaluate_scenario(rec, arts, Path(tmp), log_dir, timeout, env_ok)
                    tl = _test_level(log_dir, sid)
                st = status5(res["outcome"])
                row = {**{k: by_sid[sid][k] for k in ("layer", "generation_method", "input_hash",
                                                       "evaluation_eligibility", "ineligibility_reason")},
                       **res, **tl, "status": st, "artifacts_hash": art_hash, "corrected": False,
                       "not_run_reason": (f"{res['outcome']}: {res.get('evidence') or ''}".strip() if st == "NOT_RUN"
                                          else None)}
                _atomic_write(ck, json.dumps(row, ensure_ascii=False, indent=1) + "\n")
                rows.append(row)
    finally:
        execution.SAMPLE_APP = saved_app
    return rows, {"ok": env_ok, "message": "ok" if env_ok else env_msg}


def run_layer(name: str, out: Path, timeout: int = execution.DEFAULT_TIMEOUT, resume: bool = False) -> dict:
    layer = load_layer(name)
    routes = routes_from_endpoint_summary(mf.load_json(layer["endpoint_summary_path"]))
    hybrid_arts, decisions, cands = {}, [], []
    for sid in layer["ids"]:
        art, dec, cs = hybrid.merge(name, reference_for(layer, sid), layer["candidates"]["rule_based"].get(sid, []),
                                    layer["candidates"]["llm"].get(sid, []), routes)
        hybrid_arts[sid] = [art] if art else []
        decisions.append(dec)
        cands.extend(cs)
    arts_by_method = {**layer["candidates"], "hybrid": hybrid_arts}
    gen_dir = C.GENERATED / name
    shutil.rmtree(gen_dir, ignore_errors=True)
    for sid, arts in hybrid_arts.items():  # hibrit nihai test modülleri (inceleme için; çalıştırma yalıtılmış dizinde)
        for a in arts:
            _atomic_write(gen_dir / f"test_{sid.lower().replace('-', '_')}.py",
                          f'"""Hibrit nihai test — H5-05 / #43. Kaynak: {a.origin}. ELLE DÜZENLEMEYİN."""\n' + a.source)
    manifests, results, envs = {}, {}, {}
    for method in C.METHODS:
        manifests[method] = manifest_rows(layer, method, arts_by_method[method])
        results[method], envs[method] = execute(layer, method, arts_by_method[method], manifests[method], out,
                                                timeout, resume)
    return {"layer": layer, "decisions": decisions, "candidates": cands,
            "hybrid_summary": hybrid.summarize(decisions, cands), "manifests": manifests, "results": results,
            "environment": envs}


def environment_info() -> dict:
    import django
    import pytest
    return {"python": platform.python_version(), "django": django.get_version(), "pytest": pytest.__version__,
            "platform": platform.system(), "executable_isolation": "senaryo başına geçici dizin + ayrı pytest süreci",
            "timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat()}
