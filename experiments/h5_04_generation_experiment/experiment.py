"""Dev kümesi koşu orkestrasyonu — H5-04 / Issue #42.

İki üreticinin (kural tabanlı #30, LLM #31) donmuş ilk-geçiş testlerini geliştirme kümesinde
``agent.evaluation`` (#32) hattıyla çalıştırır: senaryo↔artefakt eşleme, sözdizimi/güvenlik ön
kontrolü, yalıtılmış toplama + çalıştırma, PASS/FAIL/ERROR/TIMEOUT sınıflandırması ve metrik özeti.
``agent.evaluation`` modülleri **değiştirilmeden** yeniden kullanılır.

Dev kümesinde bilinen güvenlik açığı yoktur; bu nedenle güvenlik F1'i "Ölçülemedi" olur. Odak:
üretim kalitesi (sözdizimi/toplanma) ve çalıştırılabilirlik.
"""
from __future__ import annotations

from pathlib import Path

from agent.evaluation import manifest as mf
from agent.evaluation.artifacts import ADAPTERS
from agent.evaluation.execution import DEFAULT_TIMEOUT, check_environment, evaluate_baseline
from agent.evaluation.metrics import Outcome, compute

from . import manifest as dev_manifest


def run_experiment(out: Path, timeout: int = DEFAULT_TIMEOUT,
                   baselines: list[str] = ("rule_based", "llm"), keep_logs: bool = True,
                   env_ok: bool | None = None, manifest_path: Path = dev_manifest.MANIFEST) -> dict:
    """Dev manifestini doğrulayıp her baseline'ı değerlendirir; sonuç/metrik sözlüğü döndürür."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest yok; önce 'freeze' çalıştırın: {manifest_path}")
    manifest = mf.load_json(manifest_path)
    problems = dev_manifest.verify(manifest)
    if problems:
        raise mf.IntegrityError("dev manifesti doğrulanamadı: " + "; ".join(problems))

    records = manifest["scenarios"]
    ids = [r["scenario_id"] for r in records]
    if env_ok is None:
        env_ok, env_msg = check_environment()
    else:
        env_msg = "ok" if env_ok else "ortam enjekte edildi: env_ok=False (test çalıştırılmadı)"

    results: dict[str, list[dict]] = {}
    metrics: dict[str, dict] = {}
    for b in baselines:
        arts = ADAPTERS[b](ids)
        log_dir = (out / "results" / b / "logs") if keep_logs else None
        rows = evaluate_baseline(records, arts, log_dir=log_dir, timeout=timeout, env_ok=env_ok)
        results[b] = rows
        metrics[b] = compute(
            Outcome(r["scenario_id"], r["http_method"], r["is_known_flaw"], r["outcome"]) for r in rows)

    return {
        "results": results,
        "metrics": metrics,
        "manifest": manifest,
        "environment_check": {"ok": env_ok, "message": env_msg if not env_ok else "ok"},
    }
