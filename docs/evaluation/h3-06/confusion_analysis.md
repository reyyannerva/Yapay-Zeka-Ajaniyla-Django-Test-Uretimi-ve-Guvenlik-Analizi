# H3-06 — TP / FP / TN / FN Tanımları ve Senaryo Düzeyi Analiz

Tanımlar `benchmarks/reference_cases/split.md` §4.3 ile aynıdır ve H3-06'da **değiştirilmemiştir**.
Kod: `agent/evaluation/metrics.py::confusion_cell`.

| Hücre | Koşul | Anlamı |
|---|---|---|
| **TP** | `is_known_flaw = true` ve test doğrulamada FAIL | Bilinen kusur yakalandı |
| **FN** | `is_known_flaw = true` ve test PASS, test yok veya teknik hata | Kusur yakalanmadı |
| **FP** | `is_known_flaw = false` ve test doğrulamada FAIL | Kusursuz davranış yanlışlıkla kusur sayıldı |
| **TN** | `is_known_flaw = false` ve test PASS | Güvenli davranış doğru doğrulandı |
| matris dışı | `is_known_flaw = false` ve teknik hata | FP sayılmaz; çalıştırılabilirlik metriğinde |

`label` alanı (izinli/engelli istek) güvenlik sınıfı değildir ve kullanılmaz (ör. SC-AUT-002 `negative`
etiketli ama kusursuzdur → TN).

## Sonuç matrisi (18 senaryo, 3 pozitif)

| | Baseline A — kural tabanlı | Baseline B — LLM |
|---|---|---|
| TP | 2 (SC-FLW-001, SC-FLW-002) | 2 (SC-FLW-001, SC-FLW-002) |
| FN | 1 (SC-FLW-003) | 1 (SC-FLW-003) |
| FP | 0 | 0 |
| TN | 15 | 15 |
| Matris dışı | 0 | 0 |

## Kusurlu senaryolar

| Senaryo | Güvenli beklenti | Gözlenen | A | B | Açıklama |
|---|---|---|---|---|---|
| SC-FLW-001 | PUT, 403 | 200 | TP | TP | BOLA: sahip olmayan kullanıcı güncelleyebiliyor; `assert … == 403` başarısız |
| SC-FLW-002 | DELETE, 403 | 204 | TP | TP | BOLA: sahip olmayan kullanıcı silebiliyor |
| SC-FLW-003 | GET, 200 (taslaklar gizli) | 200 (taslaklar ifşa) | FN | FN | İçerik düzeyi sapma; iki baseline da yalnızca durum kodunu doğrular |

SC-FLW-003 için FN, split.md §4.3 kural 3'ün öngördüğü sonuçtur: durum kodu güvenli ve kusurlu uçta aynıdır
(200), yanıt gövdesi doğrulanmadıkça kusur görünmez. H3-04 bunu üretim sırasında
`CONTENT_ASSERTION_UNSUPPORTED` uyarısıyla önceden belirtmiştir.

## Kusursuz senaryolar

15 kusursuz senaryonun tamamı her iki baseline'da PASS → TN. Hiçbir FP veya teknik hata gözlenmemiştir.
Senaryo düzeyi tablo: `experiments/h3_06_baseline_evaluation/results/comparison.md`,
makine-okunur: `results/per_scenario.csv`.
