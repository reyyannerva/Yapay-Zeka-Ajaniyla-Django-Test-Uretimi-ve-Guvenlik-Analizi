# H3-06 — 5 Dakikalık Sunum ve Demo Akışı

Sunum dosyası: `docs/evaluation/h3-06/presentation/h3-06_sunum.html` (tarayıcıda açılır, ← → ile gezinilir,
çevrimdışı çalışır). Komutlar: `demo/demo_commands.sh`.

| Süre | Slayt / eylem | Söylenecek ana noktalar |
|---|---|---|
| 0:00–0:30 | 1 — Amaç | Kural tabanlı ve LLM tabanlı Pytest üretimini aynı bağımsız test kümesinde ilk kez ölçüyoruz. |
| 0:30–1:15 | 2 — Veri ve sabitleme | 18 senaryo, 3 bilinen kusur; SHA-256 manifest; POST/405 yok (kapsam sınırı). |
| 1:15–2:00 | 3 — Adil hat | Aynı girdiler, onarımsız ilk çıktı, senaryo başına yalıtılmış pytest; FAIL ≠ üretim hatası. |
| 2:00–3:15 | **Canlı demo** | `python -m agent.evaluation verify` → `run`; konsolda iki satır sonuç; `comparison.md`'yi göster. |
| 3:15–4:00 | 4 — Örnekler (5 yöntem) | PUT SC-FLW-001: `assert 200 == 403` → TP. GET SC-FLW-003: 200 = 200 → FN (içerik kusuru). POST yalnızca geliştirme kümesinden gösterim. |
| 4:00–4:40 | 5 — Sonuçlar ve hedefler | İki yöntem de F1 = 0.80 (tam sınırda), çalıştırılabilirlik %100. |
| 4:40–5:00 | 6 — Sınırlılıklar ve sonraki adım | 3 pozitif → geniş güven aralığı; model sapması; mutation score ölçülmedi; içerik doğrulaması eklenecek. |

## Canlı demo komutları

```bash
python -m agent.evaluation verify
python -m agent.evaluation run
sed -n '1,22p' experiments/h3_06_baseline_evaluation/results/comparison.md
cat experiments/h3_06_baseline_evaluation/results/llm/logs/SC-FLW-001/run.log | tail -5
```

## Yedek plan (canlı demo çalışmazsa)

1. Önceden üretilmiş `results/comparison.md` ve `results/metrics.csv` dosyalarını göster (depoda kayıtlı).
2. Gerçek günlükler: `results/rule_based/logs/SC-FLW-001/run.log`, `results/llm/logs/SC-FLW-001/probe.json`.
3. Sunum dosyasının 5. slaytında aynı tablo statik olarak bulunur.
LLM'e canlı istek **gönderilmez**; demo ağ erişimi veya API anahtarı gerektirmez.

## Olası sorular ve yanıtlar

* **Neden iki yöntem aynı sonucu verdi?** Test kümesindeki 3 kusurun 2'si durum kodu, 1'i içerik sapmasıdır;
  iki yöntem de durum kodunu doğru kurduğunda aynı hücrelere düşer. Kural tabanlı testler ek olarak yan
  etki doğrular; bu kümede fark yaratmadı.
* **F1 = 0.80 hedefi gerçekten karşılandı mı?** Tam eşittir (4/5); tek ek hata hedefi kaçırtır. Küçük
  örneklem nedeniyle güçlü bir iddia değildir.
* **LLM'e cevap verildi mi?** İstemlerde güvenli beklenen kod vardır (gereksinim); kusur bilgisi ve
  gözlenen kusurlu kod yoktur — 38 istem tarandı.
* **Neden Llama 3.3 70B değil?** Groq'ta `model_not_found`; H3-05'te gpt-oss-120b kullanıldı ve belgelendi.
* **LLM çıktısını yeniden ürettiniz mi?** Hayır; bu ortamda API erişimi yok. PR #83'ün özgün çıktıları köken
  kontrolünden (ham yanıt ↔ test dosyası ↔ istem) geçirildi.
* **Mutation score?** Bu aşamada ölçülmedi.
