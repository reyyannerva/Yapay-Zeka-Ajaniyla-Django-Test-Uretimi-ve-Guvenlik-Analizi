"""Dondurulmuş değerlendirme manifesti — H3-06 / Issue #32.

Manifest; bağımsız test kümesinin sürümünü ve kanonik özetini, senaryo kimliklerini, kapsamı, bilinen
kusurları, dahil etme/dışlama ölçütlerini ve iki baseline'ın değerlendirilen artefaktlarının SHA-256
özetlerini sabitler. ``run`` komutu değerlendirmeden önce manifesti yeniden doğrular; herhangi bir
uyuşmazlıkta değerlendirme başlamaz (veri veya artefakt sonuca göre değiştirilmiş olabilir).

Özetler, H3-03 ``check_references.py`` ile aynı biçimde CRLF→LF normalleştirilmiş bayt üzerinden hesaplanır.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REF = REPO / "benchmarks" / "reference_cases"
TEST_SET = REF / "test_set.json"
GROUND_TRUTH = REF / "ground_truth.json"
INTEGRITY = REF / "INTEGRITY.txt"
H304 = REPO / "experiments" / "h3_04_rule_based_baseline"
H305 = REPO / "experiments" / "h3_05_llm_baseline"
OUT = REPO / "experiments" / "h3_06_baseline_evaluation"
MANIFEST = OUT / "evaluation_manifest.json"

MANIFEST_VERSION = "1.0.0"
EVALUATOR_VERSION = "1.0.0"
LLM_TEMPERATURE = 0.0
METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")


class IntegrityError(RuntimeError):
    """Sabitlenmiş veri veya artefakt beklenen özetle uyuşmuyor."""


def canonical_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(canonical_bytes(path)).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO).as_posix()


def integrity_records(path: Path = INTEGRITY) -> dict[str, str]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            name, digest = line.split()
            out[name] = digest
    return out


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_test_set(path: Path = TEST_SET) -> list[str]:
    data = load_json(path)
    ids = data["scenario_ids"]
    if len(ids) != len(set(ids)):
        raise IntegrityError("test_set.json yinelenen senaryo kimliği içeriyor")
    if data.get("count") is not None and data["count"] != len(ids):
        raise IntegrityError(f"test_set.json count={data['count']} fakat {len(ids)} kimlik var")
    return ids


def ground_truth_index(path: Path = GROUND_TRUTH) -> dict[str, dict]:
    data = load_json(path)
    recs = data["records"] if isinstance(data, dict) else data
    index: dict[str, dict] = {}
    for r in recs:
        if r["scenario_id"] in index:
            raise IntegrityError(f"ground_truth.json yinelenen kayıt: {r['scenario_id']}")
        index[r["scenario_id"]] = r
    return index


def evaluation_records(test_ids: list[str], gt: dict[str, dict]) -> list[dict]:
    """Değerlendirilecek senaryolar; ground truth'u olmayan senaryo değerlendirmeyi durdurur."""
    missing = [s for s in test_ids if s not in gt]
    if missing:
        raise IntegrityError(f"test kümesindeki senaryoların ground truth kaydı yok: {missing}")
    out = []
    for sid in test_ids:
        r = gt[sid]
        if not isinstance(r.get("is_known_flaw"), bool):
            raise IntegrityError(f"{sid}: is_known_flaw bool değil")
        sf = r.get("security_finding") or {}
        out.append({
            "scenario_id": sid,
            "http_method": r["http_method"],
            "user_role": r["user_role"],
            "secure_status": r["expected_result"]["secure_status"],
            "is_known_flaw": r["is_known_flaw"],
            "observed_flawed_status": sf.get("observed_flawed_status"),
            "deviation_kind": sf.get("deviation_kind"),
            "validation_status": r.get("validation_status"),
        })
    return out


def _artifact_files(baseline: str) -> list[Path]:
    if baseline == "rule_based":
        d = H304 / "generated_tests"
        files = [d / "conftest.py", d / "h304_support.py", *sorted(d.glob("test_*_generated.py")),
                 H304 / "reports" / "generation_report.json"]
    elif baseline == "llm":
        files = [H305 / "generated_tests" / "conftest.py", H305 / "reports" / "generation_report.json",
                 *sorted((H305 / "raw_responses").glob("*.txt"))]
    else:
        raise ValueError(baseline)
    return files


def coverage(records: list[dict]) -> dict:
    methods = Counter(r["http_method"] for r in records)
    statuses = Counter(str(r["secure_status"]) for r in records)
    return {
        "by_method": {m: methods.get(m, 0) for m in METHODS},
        "by_secure_status": dict(sorted(statuses.items())),
        "by_role": dict(sorted(Counter(r["user_role"] for r in records).items())),
        "missing_methods": [m for m in METHODS if methods.get(m, 0) == 0],
        "missing_statuses": [s for s in ("201", "405") if s not in statuses],
    }


def build() -> dict:
    integ = integrity_records()
    for name, path in (("test_set.json", TEST_SET), ("ground_truth.json", GROUND_TRUTH)):
        if integ.get(name) != sha256(path):
            raise IntegrityError(f"{name} INTEGRITY.txt ile uyuşmuyor; manifest dondurulmaz")
    test_set = load_json(TEST_SET)
    records = evaluation_records(load_test_set(), ground_truth_index())
    flaws = [{k: r[k] for k in ("scenario_id", "http_method", "secure_status", "observed_flawed_status",
                                "deviation_kind")} for r in records if r["is_known_flaw"]]
    h304_rep = load_json(H304 / "reports" / "generation_report.json")
    h305_rep = load_json(H305 / "reports" / "generation_report.json")["summary"]
    return {
        "manifest": "H3-06 dondurulmuş değerlendirme manifesti",
        "manifest_version": MANIFEST_VERSION,
        "evaluator_version": EVALUATOR_VERSION,
        "issue": "#32",
        "dataset": {
            "test_set": rel(TEST_SET),
            "test_set_version": test_set["version"],
            "test_set_sha256_lf": sha256(TEST_SET),
            "ground_truth": rel(GROUND_TRUTH),
            "ground_truth_sha256_lf": sha256(GROUND_TRUTH),
            "integrity_reference": rel(INTEGRITY),
            "hash_method": "SHA-256, CRLF→LF normalleştirilmiş içerik (check_references.py ile aynı)",
            "scenario_count": len(records),
            "scenario_ids": [r["scenario_id"] for r in records],
        },
        "inclusion_criteria": [
            "Yalnızca test_set.json'daki 18 senaryo değerlendirilir (H3-03 bağımsız küme).",
            "Her senaryonun ground_truth.json'da validation_status=verified kaydı bulunmalıdır.",
            "Her baseline için senaryoya ait ilk geçiş (onarımsız) test artefaktı kullanılır.",
        ],
        "exclusion_criteria": [
            "Geliştirme kümesi (split.json 'development', 20 senaryo) metriklere katılmaz.",
            "Kusursuz senaryodaki teknik hata güvenlik matrisine katılmaz (split.md §4.3); "
            "çalıştırılabilirlik metriğinde raporlanır.",
            "Hiçbir senaryo sonuca bakılarak çıkarılmaz; veri kümesi değiştirilmez.",
        ],
        "scenarios": records,
        "coverage": coverage(records),
        "known_flaws": flaws,
        "baselines": {
            "rule_based": {
                "issue": "#30 (H3-04)",
                "generator": h304_rep["generator"],
                "llm_used": False,
                "deterministic": True,
                "input_sha256_recorded": h304_rep["inputs_sha256"],
                "artifacts_sha256_lf": {rel(p): sha256(p) for p in _artifact_files("rule_based")},
            },
            "llm": {
                "issue": "#31 (H3-05)",
                "generator": f"{h305_rep['generator']} v{h305_rep['version']}",
                "model": h305_rep["model"],
                "prompt_version": h305_rep["prompt_version"],
                "temperature_default": LLM_TEMPERATURE,
                "temperature_recorded": None,
                "temperature_note": ("Kayıtlı rapor sıcaklık alanı içermez; CLI varsayılanı 0.0'dır (--temperature / "
                                     "LLM_TEMPERATURE ile değiştirilebilir). Kullanılan değer bu nedenle doğrulanamadı."),
                "first_pass_only": True,
                "input_sha256_recorded": h305_rep.get("input_sha256"),
                "artifacts_sha256_lf": {rel(p): sha256(p) for p in _artifact_files("llm")},
            },
        },
        "contamination_note": (
            "Her iki üretici de 38 senaryonun tamamı için (test kümesi dahil) test üretmiştir; bu bir eğitim "
            "değil, girdi olarak kullanımdır. Kural tabanlı üretici öğrenme/ayar içermez. LLM istemi ground "
            "truth'un yalnızca güvenli beklentisini (secure_status, behavior) içerir; is_known_flaw ve "
            "observed_flawed_status istemlere girmez (prompts_sent taramasıyla doğrulandı). İstem şablonu veri "
            "kümesi bilinerek tasarlanmıştır; bu sınırlılık raporlanır."
        ),
        "mutation_score": "Bu aşamada ölçülmedi",
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
    for key, path in (("test_set_sha256_lf", REPO / ds["test_set"]), ("ground_truth_sha256_lf",
                                                                     REPO / ds["ground_truth"])):
        if not path.exists():
            problems.append(f"eksik veri dosyası: {rel(path)}")
        elif sha256(path) != ds[key]:
            problems.append(f"veri değişmiş: {rel(path)}")
    try:
        integ = integrity_records(REPO / ds["integrity_reference"])
        if integ.get("test_set.json") != ds["test_set_sha256_lf"] or \
                integ.get("ground_truth.json") != ds["ground_truth_sha256_lf"]:
            problems.append("manifest özetleri INTEGRITY.txt ile uyuşmuyor")
    except (OSError, ValueError) as exc:
        problems.append(f"INTEGRITY.txt okunamadı: {exc}")
    if not problems:
        current = [r["scenario_id"] for r in evaluation_records(load_test_set(REPO / ds["test_set"]),
                                                                ground_truth_index(REPO / ds["ground_truth"]))]
        if current != ds["scenario_ids"]:
            problems.append("senaryo kimlikleri manifestle uyuşmuyor")
    for name, b in manifest["baselines"].items():
        for p, digest in b["artifacts_sha256_lf"].items():
            path = REPO / p
            if not path.exists():
                problems.append(f"{name}: eksik artefakt {p}")
            elif sha256(path) != digest:
                problems.append(f"{name}: artefakt değişmiş {p}")
    return problems
