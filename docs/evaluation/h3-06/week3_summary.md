# Hafta 3 Özeti ve Kabul Denetimi — "Hafta 3 - Veri ve AI Baseline"

Denetim tarihi: 2026-11-11 · Temel: `main` @ `93a8844` + H3-06 dalı. Durum anahtarı: **PASS** (tüm kabul
ölçütleri kanıtla karşılandı), **PARTIAL** (bir veya daha fazla ölçüt belgelenmiş sapmayla karşılanmadı),
**BLOCKED** (doğrulanamadı).

## 1. Ön koşul denetimi (H3-06 girdileri)

| İş | Kanıt (bu oturumda yeniden çalıştırıldı) | Durum |
|---|---|---|
| #27 H3-01 fixture + senaryo veri kümesi | `sample_app` testleri 69/69; `validate_scenarios.py` başarılı; CSV dışa aktarımı bayt düzeyinde aynı | PASS |
| #28 H3-02 EDA ve veri kalitesi | `experiments/h3_02_eda` testleri 67/67 (Colab'da fiilen çalıştırma zorunlu tutulmadı, PR #79 kararı) | PASS |
| #29 H3-03 bağımsız test kümesi + ground truth | `reference_cases` testleri 48/48; `check_references.py` başarılı; LF/CRLF bağımsız sabitleme (PR #81) | PASS |
| #30 H3-04 kural tabanlı baseline | birim testleri 122/122; üretilen paket 36 geçti / 2 kusur tespiti | PASS |
| #31 H3-05 LLM baseline | birim testleri 26/26; köken 38/38; üretilen paket 36 / 2; sır yok. **Llama 3.3 70B yerine gpt-oss-120b** | PARTIAL |
| PR #81 veri bütünlüğü düzeltmesi | birleştirildi (`399e8d0`); `test_integrity.py` geçti | PASS |
| PR #82 kanonik veritabanı dokümantasyonu | birleştirildi (`7e09d1d`); `docs/database/` revizyon 3 | PASS |

## 2. H3-06 (#32) kabul ölçütleri

| Ölçüt | Kanıt | Durum |
|---|---|---|
| İki yöntem aynı senaryolarda karşılaştırıldı | manifest (18 kimlik), `per_scenario.csv` (2×18 satır), aynı hat | PASS |
| Senaryo sayıları, HTTP yöntemleri, veri ayrımı belirtildi | `methodology.md` §1, manifest `coverage` | PASS |
| Sözdizimi, çalıştırılabilirlik ve PASS/FAIL ayrıldı | `executability.md`; sonuç sınıfları ayrı alanlar | PASS |
| TP/FP/FN belgelendi; P/R/F1 doğru hesaplandı | `confusion_analysis.md`, `metrics.py` + 18 metrik testi, tam kesir | PASS |
| İlk geçişte çalıştırılabilirlik iki yöntem için hesaplandı | %100 / %100 | PASS |
| Hedeflerle karşılaştırma ve açıklama | F1 = 0.80 (sınırda), çalıştırılabilirlik %100; `precision_recall_f1.md` | PASS |
| Ölçülemeyen metrikler, küçük örneklem, desteklenmeyen senaryolar | `limitations.md`; mutation score "Bu aşamada ölçülmedi" | PASS |
| Geliştirme/test verisi karışmadı; test kümesi değiştirilmedi | manifest + `INTEGRITY.txt`; `benchmarks/` diff'i boş | PASS |
| Rapor, metrik kodu ve ~5 dk demo/sunum depoda | `docs/evaluation/h3-06/`, `agent/evaluation/`, `demo/`, `presentation/` | PASS |

## 3. Sonuç tablosu

| | Baseline A — kural tabanlı | Baseline B — LLM |
|---|---|---|
| Senaryo | 18 | 18 |
| Sözdizimi geçerli | 18/18 | 18/18 |
| Toplanan | 18/18 | 18/18 |
| İlk geçişte çalıştırılabilir | %100 | %100 |
| PASS / FAIL / ERROR | 16 / 2 / 0 | 16 / 2 / 0 |
| TP / FP / TN / FN | 2 / 0 / 15 / 1 | 2 / 0 / 15 / 1 |
| Precision / Recall / F1 | 1.00 / 0.67 / 0.80 | 1.00 / 0.67 / 0.80 |
| F1 ≥ 0.80 | Karşılandı (tam sınırda) | Karşılandı (tam sınırda) |
| Çalıştırılabilirlik ≥ %70 | Karşılandı | Karşılandı |
| Mutation score | Bu aşamada ölçülmedi | Bu aşamada ölçülmedi |

## 4. Kilometre taşı kararı

H3-06 tamamlanmıştır. Ancak #31'in kabul ölçütü "Groq üzerinden **Llama 3.3 70B** modeliyle …" ifadesini
içerir ve H3-05 belgelenmiş bir gerekçeyle (`model_not_found`) farklı bir modelle yapılmıştır. Bu sapma
ekip/danışman tarafından kabul edilmeden Hafta 3 kilometre taşının **tamamen doğrulandığı söylenemez**;
bu nedenle kilometre taşı H3-06 kapsamında kapatılmamıştır. Öneri: sapmanın Issue #31'de onaylanması
veya Llama 3.3 70B erişimi sağlandığında H3-05'in yeni manifest sürümüyle yinelenmesi.
