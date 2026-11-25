# H5-05 / #43 — Kabul kriteri ve iste izlenebilirliği

Durum değerleri: **Karşılandı** / **Kısmen** / **Karşılanmadı**. Hiçbir kriter kanıtı olmadan
"Karşılandı" olarak işaretlenmedi.

| # | Kabul kriteri | Durum | Kanıt | Açıklama |
|---|---|---|---|---|
| AC1 | Kural tabanlı ve Groq LLM üretimini birleştiren sınırlı hibrit yaklaşım geliştirilmiş ve denenmiştir | Karşılandı | `hybrid.py`, `normalize.py`, `results/hybrid_decisions.jsonl` | Katman A'da gerçek Groq çıktıları (H3-05 arşivi) ile birleştirildi ve çalıştırıldı. Not: 20/20 yinelenen; LLM'e özgü katkı oluşmadı. |
| AC2 | Üç yaklaşım aynı geliştirme senaryoları ve ortak koşullarda karşılaştırılmıştır | Karşılandı (Katman A) | `results/comparison_table.md`, `metrics_summary.json` → `layers.A.comparability` | Katman A: 20 aynı senaryo, aynı girdi özetleri, aynı değerlendirici. Katman B'de LLM eksik olduğu için karşılaştırma yapılamaz. |
| AC3 | GET, POST, PUT, PATCH, DELETE deneylerde temsil edilmektedir | **Kısmen** | `results/coverage_report.json` | Kural tabanlı ve hibritte beş metot da temsil edildi (Katman B). LLM'de PATCH hiçbir katmanda yok; Katman B LLM üretimi BLOCKED. |
| AC4 | Sözdizimi, teknik çalıştırılabilirlik ve yürütme sonuçları ayrı kaydedilmiştir | Karşılandı | `results/execution_results.csv` (`syntax_valid`, `collected`, `status`, `test_count`, `executable_tests`) | — |
| AC5 | TP/FP/FN ve P/R/F1 hesaplama yöntemi açıklanmıştır | Karşılandı | `experiment_report.md` §8, `metrics.py`, `results/ground_truth_matches.csv` | — |
| AC6 | İlk geçiş çalıştırılabilirlik oranının pay, payda ve yöntemi belirtilmiştir | Karşılandı | `experiment_report.md` §8, `comparison_table.*` (pay/payda sütunu) | — |
| AC7 | F1 ≥ 0.80 ve çalıştırılabilirlik ≥ %70 hedefleri gerçek sonuçlarla karşılaştırılmıştır | **Kısmen** | `experiment_report.md` §13 | Çalıştırılabilirlik hedefi üç yöntemde ölçülerek karşılaştırıldı (Katman A). F1 hedefi yalnızca kural tabanlı ve hibrit için ölçüldü (Katman B, n = 3 pozitif). LLM için F1 hiçbir katmanda ölçülemedi: Katman A'da pozitif yok, Katman B BLOCKED. |
| AC8 | Ölçülemeyen metrikler, başarısız örnekler ve sınırlılıklar raporlanmıştır | Karşılandı | `experiment_report.md` §12, §14; `failure_analysis.json` | — |
| AC9 | Kodlar, betikler, tablo ve rapor repoda mevcuttur | Karşılandı | Bu dizin (PR ile) | — |

**Sonuç:** 9 kriterden 7'si karşılandı; AC3 ve AC7 kısmen karşılandı. Bu nedenle PR `Closes #43` içermez
ve otomatik birleştirilmez.

**Kapanış için gereken:** Groq kimlik bilgisi ve ağ erişimi sağlanınca Katman B LLM üretimi yapılmalı
(`experiment_report.md` §15) ve `run` yeniden koşulmalı. Bu adım AC3'ü (LLM PATCH temsili) ve AC7'yi
(LLM F1 karşılaştırması) tamamlar.

## İst eşlemesi
| İst | H5-05'teki karşılığı |
|---|---|
| İST-03 | Kimlik doğrulama ve yetkilendirme senaryoları: anonim 401, sahip olmayan kullanıcı 403, yönetici, BOLA kusurları |
| İST-04 | Pytest test üretimi: kural tabanlı, LLM ve hibrit; üretilen testler `layer_b/generated` ve `results/logs` altında |
| İST-05 | Üretilen testlerin yalıtılmış çalıştırılması ve PASS/FAIL/ERROR/TIMEOUT/NOT_RUN sınıflandırması |
| İST-06 | Güvenlik açığı tespiti ve ground truth eşleştirmesi (TP/FP/FN, P/R/F1) |
| İST-13 | Hedeflerle karşılaştırma: F1 ≥ 0.80, çalıştırılabilirlik ≥ %70 |
| İST-15 | Raporlama: karşılaştırma tablosu, deney raporu, JSON/CSV çıktıları |
| İST-16 | Girdi doğrulama ve HTTP davranışı senaryoları (400, 404, 405) |

Not: İst metinleri issue'daki kodlardan eşlendi. Ayrıntılı tanımlar proje gereksinim belgesindedir.
