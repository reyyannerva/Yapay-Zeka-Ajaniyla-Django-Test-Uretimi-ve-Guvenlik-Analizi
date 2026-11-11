# H3-06 — Bütünlük ve Köken (Provenance) Kanıtı

Tüm kontroller otomatik testlerle tekrarlanabilir (`agent/evaluation/tests/test_manifest.py`,
`test_execution.py`). Özetler SHA-256, CRLF→LF normalleştirilmiş içerik üzerindendir.

## 1. Sabitlenmiş veri

| Dosya | Kanonik (LF) SHA-256 | Eski CRLF özeti (H3-03 ilk sabitleme) |
|---|---|---|
| `test_set.json` | `6e69549e388ed26762e09851d4e61c3c6b8db15a910966ef223ab103eed151b1` | `075d141d…` |
| `ground_truth.json` | `b5114e74c63d9a60f335bd4984d9896da98d423c41ea87d618f2cca268fd737c` | `3d271f96…` |

* `INTEGRITY.txt` ↔ manifest ↔ dosya içeriği eşleşir (`test_manifest_matches_integrity_and_test_set`).
* `python benchmarks/reference_cases/scripts/check_references.py` → geçti.
* H3-06 boyunca `benchmarks/` altında hiçbir dosya değiştirilmemiştir (PR diff'i bunu gösterir).

## 2. Dondurulmuş manifest

`experiments/h3_06_baseline_evaluation/evaluation_manifest.json` — sürüm 1.0.0, SHA-256
`4020a370c291128730a18d87dddd41cadf098bf3a1e3399702a8d8afec6850d6`.
Manifest veri özetlerine ek olarak değerlendirilen **tüm artefaktların** özetlerini içerir (H3-04: 5 test
modülü + conftest + h304_support + üretim raporu; H3-05: conftest + üretim raporu + 38 ham yanıt).
`run` komutu önce `verify` yapar; herhangi bir uyuşmazlıkta değerlendirme başlamaz (çıkış kodu 2).
Kurcalama testleri: veri özeti, artefakt özeti ve eksik artefakt senaryoları reddedilir.

## 3. Aynı girdi koşulu

| Girdi | H3-04 kayıtlı | H3-05 kayıtlı | Depo (LF / CRLF) | Sonuç |
|---|---|---|---|---|
| endpoint_summary.json | `47fa2ed2…` | `47fa2ed2…` | LF `47fa2ed2…` | aynı |
| ground_truth.json | LF `b5114e74…` | `3d271f96…` | CRLF `3d271f96…` | aynı içerik (CRLF kodlaması) |
| scenarios.json | `6970d02e…` | `dc8a856b…` | LF `6970d02e…` / CRLF `dc8a856b…` | aynı içerik (CRLF kodlaması) |

## 4. H3-05 LLM artefaktlarının kökeni

Canlı model erişimi bu ortamda **yoktur** (`GROQ_API_KEY` tanımlı değil; api.groq.com erişilemez). Bu
nedenle LLM üretimi yeniden yapılmamış, PR #83 ile depoya eklenmiş **özgün ilk geçiş çıktıları**
değerlendirilmiştir. Bu çıktılar şu kontrollerden geçmiştir:

| Kontrol | Sonuç |
|---|---|
| `generated_tests/test_*.py` gövdesi == `extract_code(raw_responses/*.txt)` | 38/38 |
| `generation_report.json` içindeki kod == `extract_code(ham yanıt)` | 38/38 |
| `prompts_sent/*.txt` == güncel kodla `render(case)` | 38/38 |
| İstemlerde cevap anahtarı terimi (`is_known_flaw`, `observed_flawed_status`, `security_finding`, `deviation_kind`, `split`, `test_set`, `KNOWN_FLAW`) | yok |
| Kusurlu senaryoların istemleri gözlenen kusurlu kodu (200/204) içermiyor | doğrulandı |
| Model / istem sürümü | `groq/openai/gpt-oss-120b`, `pytest_v1` |
| Sıcaklık | CLI varsayılanı 0.0; rapor alan içermediği için kullanılan değer **doğrulanamadı** |
| H3-05 birim testleri | 26/26 geçti |

Sentetik veya kural üretimi bir çıktı LLM çıktısı yerine kullanılmamıştır. Değerlendirici, H3-05'in
`generated_tests/` dosyalarını değil ham yanıtları esas alır; ikisi birebir aynıdır.

## 5. Kural tabanlı artefaktlar

H3-04 üretici deterministiktir (`regeneration_identical: true`); dosya özetleri H3-04
`generation_report.json` → `generated_files_sha256` ile ve H3-06 manifestiyle eşleşir.

## 6. Gizli bilgi

Depoda API anahtarı deseni (`gsk_…`, `sk-…`) ve `.env` dosyası yoktur. Değerlendirici `GROQ_*`, `OPENAI_*`,
`ANTHROPIC_*` ortam değişkenlerini test süreçlerine aktarmaz (`test_api_keys_not_passed_to_test_processes`).
