# H5-05 / #43 — Çalışma durumu (checkpoint kaydı)

- Başlangıç main SHA: `55f3e6d0cf30476a565439804941366070d67057`
- Aktif branch: `feature/h5-05-hybrid-experiment-metrics` · PR #97
- Teslim durumu: **TAMAM** — 13/13 yapılacak, 9/9 AC (`reports/ac_traceability.md`)

## Aşamalar
1. Denetim: #43 orijinal metni (13 yapılacak, 9 AC). H5-04 doğrulandı ve yeniden koşuldu (20/20 PASS ×2).
2. Katman B üretimden önce donduruldu (`c513958`, `FROZEN.json`); çapraz kontrol 19/19.
3. Koşu 1 (geçersiz kılındı, `results/history/run1_...`): Groq erişimi yoktu; LLM BLOCKED.
4. Groq erişimi: anahtar oturumun ağ proxy'sine `api.groq.com` secret'ı olarak kaydedildi (dosya/log/commit'te yok);
   `openai/gpt-oss-120b` erişilebilir (HTTP 200).
5. Katman B gerçek LLM üretimi: 17/17 GENERATED, 0 hata, 15 714 token.
6. Düzeltmeler: (a) dedup ek LLM doğrulamasını düşürüyordu → `merged` kararı; (b) normalizer gövde kontrolünü
   tanımıyordu; (c) H3-05 conftest Katman B fixture uyarlaması; (d) checkpoint özeti destek dosyalarını kapsıyor.
7. Koşu 2 (güncel): A — 3 yöntem 20/20, F1 Ölçülemedi; B — 3 yöntem 17/17, TP=3 FP=0 FN=0, F1=1.00.
8. Bağımsız metrik çapraz kontrolü UYUŞUYOR; 44 H5-05 testi + tüm regresyon geçti (`reports/test_results.md`).

## Sonraki adım
PR #97 → ready, `Closes #43`, merge; ardından H5-06 (#44).
