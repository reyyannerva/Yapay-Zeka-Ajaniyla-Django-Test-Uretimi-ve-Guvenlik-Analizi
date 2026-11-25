# H5-05 / #43 — Yapılacaklar, kabul kriterleri ve iste izlenebilirliği

Kaynak: Issue #43'ün orijinal metni. Issue'da **13** yapılacak madde ve **9** kabul kriteri vardır.

## Yapılacaklar (13)
| # | Madde | Durum | Kanıt |
|---|---|---|---|
| 1 | H3-04 ve H3-05 üreticilerini kullanan sınırlı hibrit yaklaşımı tanımlamak | Tamam | `hybrid.py`, rapor §6 |
| 2 | AST/endpoint özeti, referans JSON ve kural tabanlı kontrollerin LLM ile birleşimi; tekrar ve çelişki ele alımı | Tamam | `normalize.py`, `hybrid.py`, rapor §6 |
| 3 | H5-04 ile aynı geliştirme alt kümesinde çalıştırmak; beş metodu kapsamak | Tamam | Katman A = H5-04'ün 20 senaryosu. Beş metot, H5-04'te PATCH olmadığı için Katman B ile tamamlandı (rapor §2, §11) |
| 4 | Sözdizimi, toplama, çalıştırılabilirlik; başarısız örnekler ve nedenleri | Tamam | `execution_results.csv`, `failure_analysis.json` |
| 5 | Üç yaklaşım için ortak değerlendirme veri kümesi; senaryo kimlikleri ve koşulların eşlenmesi | Tamam | `scenario_manifest.json` (`input_hash`, `reference_json_hash`, `ast_summary_hash`), `comparability` |
| 6 | Bağımsız ground truth ile TP/FP/FN; Precision/Recall/F1 | Tamam | `ground_truth_matches.*`, `metrics_summary.json`, `verify_metrics.py` |
| 7 | Sözdizimi, ilk geçiş ve PASS/FAIL/ERROR/TIMEOUT'u ayrı ölçütler olarak değerlendirmek | Tamam | `comparison_table.*` |
| 8 | İlk geçiş oranı: düzeltmesiz; pay ve payda açık | Tamam | Rapor §8; tabloda pay/payda sütunu |
| 9 | Üç yöntem için ortak karşılaştırma tablosu | Tamam | `results/comparison_table.md/csv` |
| 10 | F1 ≥ 0.80 ve çalıştırılabilirlik ≥ %70 ile gerçek sonuçları karşılaştırmak | Tamam | Rapor §14 |
| 11 | Başarılı/başarısız örnekler, güçlü yönler, hata türleri, sınırlılıklar, ölçülemeyenler | Tamam | Rapor §12, §13, §15 |
| 12 | Dev sonuçlarını nihai performans olarak sunmamak; bağımsız değerlendirme yapısını korumak | Tamam | Rapor başlığı ve §15; mühürlü küme açılmadı; `SplitViolation` denetimi |
| 13 | Kod, yapılandırma, betikler, tablo ve rapor repoda | Tamam | PR #97 |

## Kabul kriterleri (9)
| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| AC1 | Kural tabanlı ve Groq LLM üretimini birleştiren sınırlı hibrit yaklaşım geliştirilmiş ve denenmiştir | **Karşılandı** | İki katmanda 37 senaryonun hepsinde iki aday değerlendirildi (`hybrid_candidates.jsonl`: 37 kural tabanlı + 37 LLM). Katman A SC-LST-001'de iki üreticinin testleri birleştirildi. |
| AC2 | Üç yaklaşım aynı geliştirme senaryoları ve ortak koşullarda karşılaştırılmıştır | **Karşılandı** | `metrics_summary.json` → `layers.{A,B}.comparability = true`: aynı senaryolar, aynı girdi özetleri, aynı değerlendirici. |
| AC3 | GET, POST, PUT, PATCH, DELETE deneylerde temsil edilmektedir | **Karşılandı** | `coverage_report.json` → `union_http_methods_per_generation_method`: üç yöntemde de 5/5. Katman B: GET 3, POST 2, PUT 3, PATCH 6, DELETE 3; üç yöntem için de gerçek koşu. |
| AC4 | Sözdizimi, teknik çalıştırılabilirlik ve yürütme sonuçları ayrı kaydedilmiştir | **Karşılandı** | `execution_results.csv`: `syntax_valid`, `collected`, `outcome`/`status`, `test_count`, `executable_tests`. |
| AC5 | TP/FP/FN ve P/R/F1 hesaplama yöntemi açıklanmıştır | **Karşılandı** | Rapor §8; `metrics.py`; bağımsız çapraz kontrol UYUŞUYOR. |
| AC6 | İlk geçiş çalıştırılabilirlik oranının pay, payda ve yöntemi belirtilmiştir | **Karşılandı** | Rapor §8; tabloda senaryo düzeyi (20/20, 17/17) ve test düzeyi (21/21, 17/17). |
| AC7 | F1 ≥ 0.80 ve çalıştırılabilirlik ≥ %70 hedefleri gerçek deney sonuçlarıyla karşılaştırılmıştır | **Karşılandı** | Rapor §14. Çalıştırılabilirlik iki katmanda üç yöntem için ölçüldü. F1 Katman B'de üç yöntem için ölçüldü (1.00); Katman A'da pozitif olmadığı için Ölçülemedi olarak raporlandı. F1, 3 pozitifli kontrollü bir kümeye aittir (sınırlılık §15). |
| AC8 | Ölçülemeyen metrikler, başarısız örnekler ve sınırlılıklar raporlanmıştır | **Karşılandı** | Rapor §13 ve §15; `failure_analysis.json`; geçmiş koşu 1 ve düzeltilen politika hatası belgelendi. |
| AC9 | Kodlar, betikler, tablo ve rapor repoda mevcuttur | **Karşılandı** | `experiments/h5_05_hybrid_experiment/` (PR #97). |

## İst eşlemesi
| İst | H5-05'teki karşılığı |
|---|---|
| İST-03 | Kimlik doğrulama/yetkilendirme senaryoları: anonim 401, sahip olmayan 403, yönetici, BOLA kusurları |
| İST-04 | Pytest test üretimi: kural tabanlı, LLM (Groq gpt-oss-120b) ve hibrit |
| İST-05 | Üretilen testlerin yalıtılmış çalıştırılması; PASS/FAIL/ERROR/TIMEOUT/NOT_RUN |
| İST-06 | Güvenlik açığı tespiti ve ground truth eşleştirmesi (TP/FP/FN, P/R/F1) |
| İST-13 | Hedeflerle karşılaştırma: F1 ≥ 0.80, çalıştırılabilirlik ≥ %70 |
| İST-15 | Raporlama: karşılaştırma tablosu, deney raporu, JSON/CSV |
| İST-16 | Girdi doğrulama ve HTTP davranışı senaryoları (400, 404, 405) |
