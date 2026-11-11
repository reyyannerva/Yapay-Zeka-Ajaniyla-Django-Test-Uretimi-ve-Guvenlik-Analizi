# H3-06 değerlendirme çıktıları (Issue #32)

* `evaluation_manifest.json` — dondurulmuş manifest (veri sürümü/özetleri, 18 senaryo, kapsam, kusurlar,
  dahil etme/dışlama ölçütleri, üretici/model/istem sürümleri, 48 artefakt özeti).
* `results/metrics.json`, `results/metrics.csv` — baseline başına metrikler (tam kesirler dahil).
* `results/per_scenario.csv` — 2 × 18 satır, senaryo düzeyi sonuç ve matris hücresi.
* `results/comparison.md` — karşılaştırma tablosu (otomatik üretilir).
* `results/{rule_based,llm}/results.json` — ham senaryo sonuçları.
* `results/{rule_based,llm}/logs/<senaryo>/` — çalıştırılan modül, gerçek pytest toplama/çalıştırma günlükleri
  ve probe kaydı (geçici yollar `<WORK>`, depo yolu `<REPO>` ile maskelenmiştir).

Üretmek için depo kökünden: `python -m agent.evaluation run`. Raporlar: [`docs/evaluation/h3-06/`](../../docs/evaluation/h3-06/README.md).
