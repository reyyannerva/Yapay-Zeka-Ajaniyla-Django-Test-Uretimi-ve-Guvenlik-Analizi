# H3-04 | Kural Tabanlı İlk Pytest Üretimi Baseline'ı (Issue #30)

LLM kullanmadan, Django/DRF endpoint özeti ve bağımsız referans gereksinimlerinden (H3-03) çalıştırılabilir
Pytest testleri üreten ilk baseline'ın girdileri, üretilmiş testleri ve çalıştırma kanıtları.
Kaynak kod: [`agent/test_generation/rule_based/`](../../agent/test_generation/rule_based/README.md).

İlgili isterler: İST-02, İST-03, İST-04, İST-06, İST-15, İST-16.

## Dizin yapısı

```
experiments/h3_04_rule_based_baseline/
├── endpoint_summary.json            Kontrollü fixture'ın endpoint özeti (giriş sözleşmesine uygun)
├── examples/unsupported_cases.json  SENTETİK desteklenmeyen/geçersiz girdi örnekleri
├── generated_tests/                 ÜRETİLMİŞ Pytest paketi (elle düzenlenmez)
│   ├── test_get_generated.py · test_post_generated.py · test_put_generated.py
│   ├── test_patch_generated.py · test_delete_generated.py
│   ├── conftest.py · h304_support.py · pytest.ini
├── reports/
│   ├── generation_report.{json,md}            Senaryo durumları, tanılar, izlenebilirlik, SHA-256
│   ├── execution_report.{json,md}             Pytest sonuçları, sınıflandırma, yalıtım kontrolü
│   └── unsupported_examples_report.{json,md}  Desteklenmeyen/geçersiz örneklerin tanı sonuçları
└── requirements.txt
```

## Kurulum

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r experiments/h3_04_rule_based_baseline/requirements.txt
```

## Çalıştırma (depo kökünden)

```bash
# 1) Yükle → doğrula → üret → sözdizimi/izlenebilirlik kontrolü → yaz → çalıştır → sınıflandır → raporla
python -m agent.test_generation.rule_based all

# Yalnızca üretim (çalıştırmadan)
python -m agent.test_generation.rule_based generate

# Yalıtım kontrolü olmadan (daha hızlı)
python -m agent.test_generation.rule_based all --no-isolation

# 2) Desteklenmeyen / geçersiz girdi örnekleri
python -m agent.test_generation.rule_based examples

# 3) Üretilmiş testleri doğrudan pytest ile çalıştırma
cd experiments/h3_04_rule_based_baseline/generated_tests && python -m pytest -q

# 4) Üreticinin kendi testleri
cd agent/test_generation/rule_based && python -m pytest -q
```

Girdi yolları `--endpoints`, `--ground-truth`, `--scenarios`, `--out`, `--reports` seçenekleriyle
değiştirilebilir. Çıkış kodu: `0` = üretim hatası ve beklenmeyen uygulama uyuşmazlığı yok (bilinen kusuru
tespit eden başarısız testler beklenen sonuçtur), `1` = üretim hatası veya uygulama uyuşmazlığı var,
`2` = toplanan test sayısı planlanandan farklı, `3` = girdi kullanılamaz. Hedef uygulama yüklenemezse
(ön kontrol) testler `ENVIRONMENT_ERROR` olarak sınıflandırılır ve çıkış kodu `1` olur.

## Sonuçlar (kontrollü fixture: `benchmarks/drf_fixtures/sample_app`)

Ayrıntı ve tüm senaryo satırları: [`reports/execution_report.md`](reports/execution_report.md).

- 38 referans senaryosunun 38'i `GENERATED`; `UNSUPPORTED`/`INVALID_INPUT`/`MISSING_REFERENCE`/`GENERATION_ERROR` = 0.
- Üretilen testler: GET 10, POST 9, PUT 8, PATCH 4, DELETE 7. Pytest 38/38 testi topladı.
- Pytest sonucu: **36 geçti, 2 başarısız**.
  - `PASSED` 35 · `KNOWN_FLAW_DETECTED` 2 (SC-FLW-001 PUT, SC-FLW-002 DELETE — BOLA/IDOR; güvenli beklenti
    403, gözlenen 200/204) · `KNOWN_FLAW_NOT_DETECTED` 1 (SC-FLW-003 — içerik düzeyi taslak ifşası; durum
    kodu 200 doğru, içerik beklentisi makine-okunur değil) · `APPLICATION_MISMATCH` 0 · `GENERATION_ERROR` 0.
- Yalıtım: 38 testin her biri tek başına ve paket ters sırayla çalıştırıldı; sonuçlar tam paketle aynı.
- Beklenen kodlar (referanstan): 200 ×12, 201 ×2, 204 ×2, 400 ×4, 401 ×5, 403 ×6, 404 ×5, 405 ×2.
- Desteklenmeyen/geçersiz girdi örnekleri: 21/21 beklenen durum ve tanı koduyla sonuçlandı.

## Issue #30 kabul kriterleri izlenebilirliği

| # | Kabul kriteri | Uygulama | Kanıt |
|---|---|---|---|
| K1 | En az bir kontrollü fixture üzerinde kural tabanlı üretim | `generator.generate`, `endpoint_summary.json` | `generated_tests/`, `generation_report.md` (38 GENERATED) |
| K2 | Beş metodun her biri için en az bir geçerli test | Metot başına modül | `execution_report.md` metot tablosu; `test_each_method_has_a_passing_generated_test` |
| K3 | Durum kodu, kimlik doğrulama, yetkilendirme, girdi doğrulama referanstan | `loaders.join_references`, `planner.plan_case` | `test_expected_status_comes_from_ground_truth_not_scenarios`, `test_expected_status_is_never_inferred_from_role_or_method` |
| K4 | PUT/PATCH/DELETE güncelleme, silme, sahiplik/yetkilendirme | Yan etki kuralları, fixture'dan sahiplik | `test_each_method_plans_correct_action_and_side_effect`, `test_ownership_uses_fixture_owner_field_not_username`, `test_patch_checks_partial_semantics_and_put_full` |
| K5 | Geçerli Python, fixture ortamında pytest ile çalışır | `validation.py`, `runner.collect/run` | `test_each_method_module_is_valid_python`, `test_every_generated_test_is_collected`, `execution_report.md` |
| K6 | Eksik referans ve desteklenmeyen yapılar gerekçeli bildirilir | `contracts.Code`, `examples.py` | `unsupported_examples_report.md` (21/21), `test_invalid_inputs_are_reported_not_skipped` |
| K7 | Üretim hataları ile bilinen kusur kaynaklı başarısızlıklar ayrılır | `runner.classify`, `runner.check_environment` | `test_classification_rules`, `test_tampered_route_is_classified_as_generation_error`, `test_known_status_flaws_are_detected_and_still_failed`, `test_broken_target_app_is_environment_error_not_generator_error`, `test_generated_suite_detects_injected_faults` |
| K8 | Kaynak kod, örnek testler, çıktılar ve talimatlar repoda | Bu dizin + `agent/test_generation/rule_based/` | Bu README, raporlar, üretilmiş testler |

## Bilinen kısıtlar

- **AST entegrasyonu yok:** `endpoint_summary.json`, AST çıktısının üreteceği sözleşmeye uygun biçimde
  kontrollü fixture kaynak kodundan elle hazırlanmıştır (`source.ast_integration: false`).
- **İçerik düzeyi kusur:** SC-FLW-003 yalnızca durum koduyla doğrulanır; bu baseline taslak ifşasını tespit
  etmez (`CONTENT_ASSERTION_UNSUPPORTED`).
- **`custom_action`:** yayınlama ucunda (`/publish/`) yan etki doğrulanmaz, yalnızca durum kodu.
- **Kapsam:** yalnızca GET/POST/PUT/PATCH/DELETE ve DRF tabanlı view'lar. Kontrollü fixture'da sorgu
  parametresi veya dosya yükleme senaryosu bulunmadığından bu yapılar desteklenmez.
