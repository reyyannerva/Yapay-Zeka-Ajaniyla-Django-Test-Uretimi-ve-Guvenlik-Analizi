"""Güvenlik tespiti ve çalıştırılabilirlik metrikleri — H3-06 / Issue #32.

Tanımlar ``benchmarks/reference_cases/split.md`` §4.3'e birebir uyar:

* Değerlendirme birimi: bağımsız test kümesindeki (``test_set.json``) her senaryo.
* Gerçek pozitif sınıf: ``is_known_flaw = true``. ``label`` alanı KULLANILMAZ.
* Pozitif tahmin: çalıştırılabilir test, doğrulamasında (assert) BAŞARISIZ oldu.

| Sonuç                      | Kusur var | Kusur yok                          |
|----------------------------|-----------|------------------------------------|
| FAIL (doğrulama)           | TP        | FP                                 |
| PASS                       | FN        | TN                                 |
| Test yok / teknik hata     | FN        | matrise katılmaz (EXCLUDED)        |

Oranlar ``fractions.Fraction`` ile tam hesaplanır; payda sıfırsa değer ``None`` olur ve raporda
"Ölçülemedi" yazılır (0 veya 1 ile doldurulmaz). Eşik karşılaştırmaları da tam kesirle yapılır
(ör. F1 = 4/5 ≥ 0.80 kayan nokta yuvarlamasına bağlı değildir).
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable

NOT_MEASURABLE = "Ölçülemedi"

#: Çalıştırma sonucu → pytest düzeyi özet (PASS / FAIL / ERROR)
EXECUTABLE_OUTCOMES = ("PASS", "FAIL")
TECHNICAL_OUTCOMES = (
    "NO_ARTIFACT",        # senaryo için test üretilmemiş / bulunamadı
    "DUPLICATE_ARTIFACT",  # aynı senaryo için birden fazla test (belirsiz eşleme)
    "SYNTAX_INVALID",     # Python sözdizimi geçersiz
    "UNSAFE_BLOCKED",     # dış ağ / süreç erişimi içerdiği için çalıştırılmadı
    "COLLECTION_ERROR",   # pytest testi toplayamadı
    "TIMEOUT",            # zaman aşımı
    "ERROR",              # kurulum hatası veya doğrulama dışı istisna
    "ENVIRONMENT_ERROR",  # hedef uygulama yüklenemedi (üreticiye yüklenmez)
)
ALL_OUTCOMES = EXECUTABLE_OUTCOMES + TECHNICAL_OUTCOMES

TARGET_F1 = Fraction(4, 5)
TARGET_EXECUTABILITY = Fraction(7, 10)


def pytest_summary(outcome: str) -> str:
    """Ayrıntılı sonucu PASS / FAIL / ERROR / NOT_RUN özetine indirger."""
    if outcome in EXECUTABLE_OUTCOMES:
        return outcome
    if outcome in ("NO_ARTIFACT", "DUPLICATE_ARTIFACT", "SYNTAX_INVALID", "UNSAFE_BLOCKED"):
        return "NOT_RUN"
    if outcome in TECHNICAL_OUTCOMES:
        return "ERROR"
    raise ValueError(f"bilinmeyen sonuç: {outcome!r}")


def confusion_cell(is_known_flaw: bool, outcome: str) -> str:
    """Tek senaryonun matris hücresi: TP / FP / TN / FN / EXCLUDED."""
    if outcome not in ALL_OUTCOMES:
        raise ValueError(f"bilinmeyen sonuç: {outcome!r}")
    if not isinstance(is_known_flaw, bool):
        raise TypeError("is_known_flaw bool olmalı")
    if outcome == "FAIL":
        return "TP" if is_known_flaw else "FP"
    if outcome == "PASS":
        return "FN" if is_known_flaw else "TN"
    return "FN" if is_known_flaw else "EXCLUDED"


def ratio(num: int, den: int) -> Fraction | None:
    if num < 0 or den < 0:
        raise ValueError("negatif sayım")
    return None if den == 0 else Fraction(num, den)


def f1(precision: Fraction | None, recall: Fraction | None) -> Fraction | None:
    """F1 = 2PR/(P+R). P veya R ölçülemiyorsa F1 de ölçülemez; P+R=0 ise F1 ölçülemez."""
    if precision is None or recall is None:
        return None
    if precision + recall == 0:
        return None
    return 2 * precision * recall / (precision + recall)


def fmt(value: Fraction | None, digits: int = 4) -> str:
    return NOT_MEASURABLE if value is None else f"{float(value):.{digits}f}"


def as_json(value: Fraction | None, digits: int = 4) -> dict:
    if value is None:
        return {"value": None, "exact": None, "display": NOT_MEASURABLE}
    return {"value": round(float(value), digits), "exact": f"{value.numerator}/{value.denominator}",
            "display": fmt(value, digits)}


def meets(value: Fraction | None, target: Fraction) -> bool | None:
    """Hedef karşılandı mı? Ölçülemeyen değer için ``None`` (ne geçti ne kaldı)."""
    return None if value is None else value >= target


@dataclass(frozen=True)
class Outcome:
    scenario_id: str
    http_method: str
    is_known_flaw: bool
    outcome: str


def compute(rows: Iterable[Outcome]) -> dict:
    """Bir baseline'ın tüm senaryo sonuçlarından metrikleri hesaplar."""
    rows = list(rows)
    ids = [r.scenario_id for r in rows]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise ValueError(f"senaryo birden fazla kez değerlendirildi: {dup}")
    cells = Counter(confusion_cell(r.is_known_flaw, r.outcome) for r in rows)
    tp, fp, tn, fn = (cells.get(k, 0) for k in ("TP", "FP", "TN", "FN"))
    outcomes = Counter(r.outcome for r in rows)
    total = len(rows)
    syntax_checked = [r for r in rows if r.outcome not in ("NO_ARTIFACT", "DUPLICATE_ARTIFACT")]
    syntax_valid = sum(1 for r in syntax_checked if r.outcome != "SYNTAX_INVALID")
    collected = sum(1 for r in rows if r.outcome in ("PASS", "FAIL", "ERROR", "TIMEOUT"))
    executable = sum(1 for r in rows if r.outcome in EXECUTABLE_OUTCOMES)
    precision, recall = ratio(tp, tp + fp), ratio(tp, tp + fn)
    f1_value = f1(precision, recall)
    execut = ratio(executable, total)
    by_method: dict[str, dict] = {}
    for r in rows:
        m = by_method.setdefault(r.http_method, Counter())
        m["scenarios"] += 1
        m[r.outcome] += 1
        m[confusion_cell(r.is_known_flaw, r.outcome)] += 1
    return {
        "scenarios": total,
        "positives": sum(1 for r in rows if r.is_known_flaw),
        "negatives": sum(1 for r in rows if not r.is_known_flaw),
        "confusion": {"TP": tp, "FP": fp, "TN": tn, "FN": fn, "EXCLUDED": cells.get("EXCLUDED", 0)},
        "outcomes": {k: outcomes.get(k, 0) for k in ALL_OUTCOMES},
        "pytest_summary": dict(Counter(pytest_summary(r.outcome) for r in rows)),
        "syntax_valid": {"count": syntax_valid, "of": len(syntax_checked),
                         **as_json(ratio(syntax_valid, len(syntax_checked)))},
        "collected": {"count": collected, "of": total, **as_json(ratio(collected, total))},
        "first_pass_executable": {"count": executable, "of": total, **as_json(execut)},
        "precision": as_json(precision),
        "recall": as_json(recall),
        "f1": as_json(f1_value),
        "targets": {
            "f1_gte_0_80": meets(f1_value, TARGET_F1),
            "first_pass_executable_gte_0_70": meets(execut, TARGET_EXECUTABILITY),
        },
        "by_method": {k: dict(sorted(v.items())) for k, v in sorted(by_method.items())},
    }
