# H5-05 / #43 — Çalışma durumu (checkpoint kaydı)

- Başlangıç main SHA: `55f3e6d0cf30476a565439804941366070d67057`
- Aktif branch: `feature/h5-05-hybrid-experiment-metrics`

## Tamamlanan aşamalar
1. Depo/issue denetimi: #43 orijinal metni okundu (12 yapılacak, 9 AC, İST-03/04/05/06/13/15/16).
2. H5-04 doğrulandı: `verify` geçerli, 17 test geçti, deney bu ortamda yeniden koşuldu — iki yöntem 20/20 PASS,
   `per_scenario.csv` ile birebir aynı (model `groq/openai/gpt-oss-120b`, prompt `pytest_v1`, LLM çıktıları H3-05'ten).
3. Katman B kontrollü hedef uygulama + girdiler yazıldı ve **üretimden önce donduruldu** (`layer_b/FROZEN.json`);
   fixture ↔ ground truth çapraz kontrolü 19/19 geçti.

## Devam eden aşama
- Hibrit üretici + deney yürütücüsü (Katman A ve B).

## Bilinen sorunlar / engeller
- Groq erişimi yok (anahtar yok, `api.groq.com` ağ politikasıyla engelli): Katman B'de yeni LLM üretimi yapılamaz.
  İstemler çevrimdışı kaydedilecek; LLM adımı BLOCKED olarak raporlanacak.

## Sonraki komut
`python -m experiments.h5_05_hybrid_experiment run --resume`
