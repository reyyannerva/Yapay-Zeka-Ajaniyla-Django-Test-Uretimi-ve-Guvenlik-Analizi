#!/usr/bin/env python
"""Bağımsız test kümesi + ground truth doğrulayıcısı — H3-03 / Issue #29.

Kontroller:
  1) JSON Schema ile ground_truth yapısal doğrulaması.
  2) Eşleşme: her senaryonun tek ground truth kaydı; id kümeleri birebir.
  3) Ayrım bütünlüğü: dev ∪ test = tüm senaryolar, kesişim boş; her aile tek grupta
     (veri sızıntısı önlemi); test_set.json = test ayrımı.
  4) Sabitleme: test_set.json + ground_truth.json SHA-256 özetleri INTEGRITY.txt ile tutuyor.
  5) Kapsam: GET/POST/PUT/PATCH/DELETE için referans; yetkisiz PUT/PATCH/DELETE altın etiketli.
  6) Belirsiz (uncertain) kayıtlar ayrı raporlanır; bilinen hatalarda security_finding var.

Çıkış kodu 0 = geçti, 1 = hata.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("HATA: 'jsonschema' kurulu değil. 'pip install jsonschema' çalıştırın.")
    sys.exit(2)

BASE = Path(__file__).resolve().parent.parent
ROOT = BASE.parent.parent
SCEN = ROOT / "benchmarks/drf_fixtures/scenarios/scenarios.json"
GT = BASE / "ground_truth.json"
GT_SCHEMA = BASE / "ground_truth.schema.json"
SPLIT = BASE / "split.json"
TEST_SET = BASE / "test_set.json"
INTEGRITY = BASE / "INTEGRITY.txt"

METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    errors: list[str] = []
    scen = {s["id"] for s in json.loads(SCEN.read_text(encoding="utf-8"))["scenarios"]}
    gt = json.loads(GT.read_text(encoding="utf-8"))
    schema = json.loads(GT_SCHEMA.read_text(encoding="utf-8"))
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    test_set = json.loads(TEST_SET.read_text(encoding="utf-8"))

    # 1) Yapısal doğrulama
    for e in sorted(Draft202012Validator(schema).iter_errors(gt), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in e.path) or "<root>"
        errors.append(f"[şema] {loc}: {e.message}")

    records = gt["records"]
    gt_ids = [r["scenario_id"] for r in records]

    # 2) Eşleşme
    dup = {i for i in gt_ids if gt_ids.count(i) > 1}
    if dup:
        errors.append(f"[eşleşme] Yinelenen ground truth kaydı: {sorted(dup)}")
    if set(gt_ids) != scen:
        missing = scen - set(gt_ids)
        extra = set(gt_ids) - scen
        if missing:
            errors.append(f"[eşleşme] Ground truth'ta eksik senaryolar: {sorted(missing)}")
        if extra:
            errors.append(f"[eşleşme] Senaryolarda olmayan ground truth id'leri: {sorted(extra)}")

    # 3) Ayrım bütünlüğü
    scenario_split = split["scenario_split"]
    if set(scenario_split) != scen:
        errors.append("[ayrım] split.json senaryo kümesi scenarios.json ile birebir değil.")
    dev = {i for i, v in scenario_split.items() if v == "dev"}
    test = {i for i, v in scenario_split.items() if v == "test"}
    if dev & test:
        errors.append(f"[ayrım] dev ve test kesişiyor: {sorted(dev & test)}")
    if (dev | test) != scen:
        errors.append("[ayrım] dev ∪ test tüm senaryoları kapsamıyor.")
    # Aile bölünmemiş mi (sızıntı önlemi)
    for fam, info in split["families"].items():
        splits = {scenario_split[i] for i in info["scenario_ids"]}
        if len(splits) != 1:
            errors.append(f"[sızıntı] {fam} ailesi birden çok gruba bölünmüş: {splits}")
        if info["split"] not in splits:
            errors.append(f"[ayrım] {fam} 'split' alanı üyeleriyle tutarsız.")
    # test_set.json = test ayrımı
    if set(test_set["scenario_ids"]) != test:
        errors.append("[ayrım] test_set.json, split.json'daki test kümesiyle birebir değil.")

    # 4) Sabitleme (SHA-256)
    recorded = {}
    for line in INTEGRITY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, _, h = line.partition(" ")
        recorded[name] = h.strip()
    for name, path in [("test_set.json", TEST_SET), ("ground_truth.json", GT)]:
        actual = sha256(path)
        if recorded.get(name) != actual:
            errors.append(f"[sabitleme] {name} SHA-256 uyuşmuyor (INTEGRITY.txt güncel değil).")

    # 5) Kapsam
    by_method = {r["http_method"] for r in records}
    if METHODS - by_method:
        errors.append(f"[kapsam] Eksik HTTP metotları: {sorted(METHODS - by_method)}")
    unauth_mut = [
        r for r in records
        if r["http_method"] in {"PUT", "PATCH", "DELETE"}
        and r["expected_result"]["secure_status"] in {401, 403}
    ]
    if not unauth_mut:
        errors.append("[kapsam] Yetkisiz PUT/PATCH/DELETE altın etiketi bulunmalı.")

    # 6) Belirsizler + bilinen hatalar
    uncertain = [r["scenario_id"] for r in records if r["validation_status"] == "uncertain"]
    flaws = [r for r in records if r["is_known_flaw"]]
    for r in flaws:
        if "security_finding" not in r:
            errors.append(f"[güvenlik] {r['scenario_id']}: is_known_flaw ama security_finding yok.")

    # --- Özet ---
    print(f"Ground truth: {len(records)} kayıt ({GT.name})")
    print(f"Ayrım: dev={len(dev)}  test={len(test)}  (aile bazlı, bölünmemiş)")
    print(f"Bağımsız test kümesi: {test_set['count']} senaryo")
    print(f"Metot kapsamı: {', '.join(sorted(by_method))}")
    print(f"Pozitif/Negatif: "
          f"{sum(1 for r in records if r['label']=='positive')}/"
          f"{sum(1 for r in records if r['label']=='negative')}")
    print(f"Bilinen güvenlik hatası (security_finding): {len(flaws)}")
    print(f"Belirsiz (uncertain) kayıt: {len(uncertain)} {uncertain if uncertain else ''}")

    if errors:
        print("\nDOĞRULAMA BAŞARISIZ:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nDOĞRULAMA BAŞARILI: şema, eşleşme, ayrım, sızıntı ve sabitleme kontrolleri geçti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
