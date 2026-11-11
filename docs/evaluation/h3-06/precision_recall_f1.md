# H3-06 — Precision / Recall / F1 Raporu

Kaynak: `experiments/h3_06_baseline_evaluation/results/metrics.json` (tam kesirler `exact` alanında).

| Metrik | Baseline A — kural tabanlı (H3-04) | Baseline B — LLM (H3-05) | Hedef |
|---|---|---|---|
| TP / FP / FN | 2 / 0 / 1 | 2 / 0 / 1 | — |
| Precision | 1.0000 (2/2) | 1.0000 (2/2) | — |
| Recall | 0.6667 (2/3) | 0.6667 (2/3) | — |
| F1 | **0.8000 (4/5)** | **0.8000 (4/5)** | ≥ 0.80 |
| F1 hedefi | Karşılandı (sınırda, tam eşit) | Karşılandı (sınırda, tam eşit) | |

## Yorum

* F1 = 4/5, hedefe **tam eşittir**; karşılaştırma tam kesirle yapıldığından kayan nokta yuvarlamasından
  etkilenmez. Hedefin üzerinde bir pay yoktur: tek bir ek FN veya FP hedefi kaçırtır
  (ör. TP=1, FN=2 → F1 = 0.50; TP=2, FP=1, FN=1 → F1 ≈ 0.667).
* Recall'u sınırlayan tek neden SC-FLW-003'tür (içerik düzeyi kusur). Durum kodu dışında yanıt gövdesi
  doğrulaması yapılmadıkça bu sınıf kusurlar yakalanamaz.
* Precision = 1.0 güçlü bir sonuç gibi görünse de yalnızca 2 pozitif tahmine dayanır.
* **Güven aralığı:** 3 pozitif senaryo ile recall için Wilson %95 aralığı yaklaşık [0.21, 0.94]'tür;
  F1 değerinin istatistiksel genellenebilirliği yoktur. Sonuç "kontrollü fixture üzerinde ilk ölçüm"
  olarak yorumlanmalıdır.
* İki baseline'ın senaryo düzeyinde sonuçları birebir aynıdır; bu test kümesi iki yöntemi **ayırt
  edemez** (bkz. `limitations.md` §3).

## Ölçülemeyen / ölçülmeyen metrikler

| Metrik | Durum |
|---|---|
| Mutation score | **Bu aşamada ölçülmedi** |
| POST, 201, 405 alt kümesi P/R/F1 | Ölçülemedi — test kümesinde senaryo yok |
| Yöntem bazında P/R/F1 (GET/PUT/DELETE dışı) | Ölçülemedi — PATCH'te pozitif sınıf yok (recall paydası 0) |
| İstatistiksel anlamlılık (A vs B) | Ölçülemedi — sonuçlar özdeş, örneklem 18 |
