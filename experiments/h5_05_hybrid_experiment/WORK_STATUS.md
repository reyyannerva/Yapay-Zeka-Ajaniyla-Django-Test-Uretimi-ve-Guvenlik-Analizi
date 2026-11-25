# H5-05 / #43 — Çalışma durumu (checkpoint kaydı)

- Başlangıç main SHA: `55f3e6d0cf30476a565439804941366070d67057`
- Aktif branch: `feature/h5-05-hybrid-experiment-metrics`
- Teslim durumu: **KISMİ** (AC3, AC7 kısmen). PR `Closes #43` içermez ve birleştirilmez. H5-06 başlatılmadı.

## Tamamlanan aşamalar
1. Depo/issue denetimi: #43 orijinal metni okundu (13 yapılacak, 9 AC, İST-03/04/05/06/13/15/16).
2. H5-04 doğrulandı ve yeniden koşuldu: iki yöntem 20/20 PASS, `per_scenario.csv` ile birebir aynı.
3. Katman B hedef uygulama ve girdileri üretimden önce donduruldu (`layer_b/FROZEN.json`); çapraz kontrol 19/19.
4. Etiket maskeli üretici girdileri hazırlandı; Katman B kural tabanlı üretim 17/17 GENERATED.
5. Katman B LLM istemleri çevrimdışı kaydedildi (17). Groq çağrısı yapılamadı → BLOCKED.
6. Hibrit üretici (normalize + birleştirme), yürütücü (atomik checkpoint, `--resume`), metrik motoru ve raporlama yazıldı.
7. Deney koşuldu: Katman A üç yöntem 20/20; Katman B kural tabanlı ve hibrit 17/17, TP=3 FP=0 FN=0.
8. 35 birim testi (metrik motoru, hibrit politika, Katman B bütünlüğü) geçiyor.
9. Rapor, AC izlenebilirliği, karşılaştırma tablosu ve H5-06 devir paketi yazıldı.

## Bilinen engel
- Groq erişimi yok (anahtar yok, `api.groq.com` engelli). Katman B LLM üretimi ve LLM için PATCH/F1 ölçümü bekliyor.
  Komut: `reports/experiment_report.md` §15.

## Sonraki komut
`python -m experiments.h5_05_hybrid_experiment run --resume` (Groq üretimi yapıldıktan sonra)
