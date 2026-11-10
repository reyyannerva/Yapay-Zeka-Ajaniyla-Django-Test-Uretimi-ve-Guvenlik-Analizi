#!/usr/bin/env python
"""Senaryo veri kümesi doğrulayıcısı — H3-01 / Issue #27.

İki katmanlı doğrulama:
  1) JSON Schema ile yapısal doğrulama (scenarios.schema.json).
  2) Tutarlılık kontrolleri: benzersiz ID, 5 HTTP metodunun ve 5 kategorinin temsili,
     pozitif/negatif denge, bilerek-hatalı senaryoların açıklamalı olması, durum kodu
     geçerliliği.

Kullanım:
    python scripts/validate_scenarios.py
Çıkış kodu 0 = geçti, 1 = hata.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("HATA: 'jsonschema' kurulu değil. 'pip install jsonschema' çalıştırın.")
    sys.exit(2)

BASE = Path(__file__).resolve().parent.parent
SCENARIOS = BASE / "scenarios" / "scenarios.json"
SCHEMA = BASE / "scenarios" / "scenarios.schema.json"

REQUIRED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
REQUIRED_CATEGORIES = {
    "AUTHENTICATION", "AUTHORIZATION", "INPUT_VALIDATION",
    "HTTP_BEHAVIOR", "SECURITY_CONFIGURATION",
}


def main() -> int:
    errors: list[str] = []
    data = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    # 1) Yapısal doğrulama
    validator = Draft202012Validator(schema)
    schema_errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    for e in schema_errors:
        loc = "/".join(str(p) for p in e.path) or "<root>"
        errors.append(f"[şema] {loc}: {e.message}")

    scenarios = data.get("scenarios", [])

    # 2) Tutarlılık kontrolleri
    ids = [s["id"] for s in scenarios]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        errors.append(f"[tutarlılık] Yinelenen ID'ler: {sorted(dupes)}")

    methods = {s["http_method"] for s in scenarios}
    missing_methods = REQUIRED_METHODS - methods
    if missing_methods:
        errors.append(f"[tutarlılık] Eksik HTTP metotları: {sorted(missing_methods)}")

    categories = {s["category"] for s in scenarios}
    missing_cats = REQUIRED_CATEGORIES - categories
    if missing_cats:
        errors.append(f"[tutarlılık] Eksik kategoriler: {sorted(missing_cats)}")

    labels = {s["label"] for s in scenarios}
    if labels != {"positive", "negative"}:
        errors.append(f"[tutarlılık] Hem pozitif hem negatif senaryo olmalı; bulunan: {labels}")

    flaws = [s for s in scenarios if s["is_intentional_flaw"]]
    if not flaws:
        errors.append("[tutarlılık] En az bir bilerek-hatalı senaryo bulunmalı.")
    for s in flaws:
        if not s.get("flaw_explanation", "").strip():
            errors.append(f"[tutarlılık] {s['id']}: flaw_explanation boş.")

    # Yetkisiz PUT/PATCH/DELETE kapsanmış mı?
    unauth_mutations = [
        s for s in scenarios
        if s["http_method"] in {"PUT", "PATCH", "DELETE"}
        and s["expected_http_status"] in {401, 403}
    ]
    if not unauth_mutations:
        errors.append("[tutarlılık] Yetkisiz PUT/PATCH/DELETE senaryosu bulunmalı.")

    # --- Özet ---
    print(f"Veri kümesi: {data.get('dataset')} v{data.get('version')}")
    print(f"Senaryo sayısı: {len(scenarios)}")
    print(f"Metot dağılımı: " + ", ".join(
        f"{m}={sum(1 for s in scenarios if s['http_method'] == m)}" for m in sorted(REQUIRED_METHODS)))
    print(f"Kategori dağılımı: " + ", ".join(
        f"{c}={sum(1 for s in scenarios if s['category'] == c)}" for c in sorted(REQUIRED_CATEGORIES)))
    print(f"Pozitif/Negatif: {sum(1 for s in scenarios if s['label']=='positive')}/"
          f"{sum(1 for s in scenarios if s['label']=='negative')}")
    print(f"Bilerek-hatalı senaryo: {len(flaws)}")

    if errors:
        print("\nDOĞRULAMA BAŞARISIZ:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("\nDOĞRULAMA BAŞARILI: tüm yapısal ve tutarlılık kontrolleri geçti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
