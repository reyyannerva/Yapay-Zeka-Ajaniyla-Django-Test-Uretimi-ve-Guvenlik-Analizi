# H3-06 — İlk Metrikler, Baseline Karşılaştırması ve Demo (Issue #32)

**Sonuç (18 senaryoluk bağımsız test kümesi):** iki baseline da sözdizimi 18/18, toplama 18/18, ilk geçişte
çalıştırılabilirlik **%100**, TP=2 / FP=0 / TN=15 / FN=1, Precision 1.00, Recall 0.67, **F1 = 0.80** (hedefe
tam eşit). Mutation score: **Bu aşamada ölçülmedi.**

| # | Teslim | Konum |
|---|---|---|
| 1 | Değerlendirme metodolojisi | [`methodology.md`](methodology.md) |
| 2 | Dondurulmuş, sürümlü manifest | [`experiments/h3_06_baseline_evaluation/evaluation_manifest.json`](../../../experiments/h3_06_baseline_evaluation/evaluation_manifest.json) |
| 3 | Bütünlük ve köken kanıtı | [`integrity_evidence.md`](integrity_evidence.md) |
| 4 | Değerlendirme çalıştırıcısı | [`agent/evaluation/`](../../../agent/evaluation/README.md) (`execution.py`, `artifacts.py`, `__main__.py`) |
| 5 | Metrik modülü | [`agent/evaluation/metrics.py`](../../../agent/evaluation/metrics.py) |
| 6 | Birim / entegrasyon testleri (86) | [`agent/evaluation/tests/`](../../../agent/evaluation/tests/) |
| 7 | Baseline A ham sonuçları | `experiments/h3_06_baseline_evaluation/results/rule_based/` |
| 8 | Baseline B ham sonuçları | `experiments/h3_06_baseline_evaluation/results/llm/` |
| 9 | JSON / CSV çıktılar | `results/metrics.json`, `results/metrics.csv`, `results/per_scenario.csv` |
| 10 | Karşılaştırma tablosu | [`results/comparison.md`](../../../experiments/h3_06_baseline_evaluation/results/comparison.md) |
| 11 | TP/FP/TN/FN tanımları ve analiz | [`confusion_analysis.md`](confusion_analysis.md) |
| 12 | Precision / Recall / F1 raporu | [`precision_recall_f1.md`](precision_recall_f1.md) |
| 13 | Çalıştırılabilirlik raporu | [`executability.md`](executability.md) |
| 14 | Örnek testler ve çıktılar | [`examples.md`](examples.md) |
| 15 | Gerçek çalıştırma günlükleri | `results/*/logs/<senaryo>/` (`collect.log`, `run.log`, `probe.json`, `test_module.py`) |
| 16 | Sınırlılıklar | [`limitations.md`](limitations.md) |
| 17 | Yeniden üretim talimatları | [`reproduction.md`](reproduction.md) |
| 18 | Hafta 3 özeti ve kabul denetimi | [`week3_summary.md`](week3_summary.md) |
| 19 | 5 dakikalık demo akışı, komutlar, yedek plan, S&C | [`demo/demo_script.md`](demo/demo_script.md), [`demo/demo_commands.sh`](demo/demo_commands.sh) |
| 20 | Sunum | [`presentation/h3-06_sunum.html`](presentation/h3-06_sunum.html) (çevrimdışı, ← → ile gezinme) |
