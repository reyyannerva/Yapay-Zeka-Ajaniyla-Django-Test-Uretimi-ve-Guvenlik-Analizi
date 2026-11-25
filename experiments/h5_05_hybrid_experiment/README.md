# H5-05 / Issue #43 — Sınırlı hibrit test üretimi ve üç yöntem karşılaştırması

Kural tabanlı (H3-04), Groq LLM (H3-05) ve hibrit test üretimini aynı geliştirme senaryolarında ve aynı
değerlendirme hattıyla (#32 `agent.evaluation`, değiştirilmeden) karşılaştırır.

- Rapor: `reports/experiment_report.md`
- Kabul kriteri izlenebilirliği: `reports/ac_traceability.md`
- Karşılaştırma tablosu: `results/comparison_table.md`

> Üç yöntem iki katmanda gerçek koşularla karşılaştırıldı (Katman B LLM: yeni Groq `gpt-oss-120b` koşusu).
> Sonuçlar geliştirme kümelerine aittir; nihai performans değildir.

## Komutlar
```bash
python -m experiments.h5_05_hybrid_experiment verify                    # Katman B dondurma kontrolü
python -m experiments.h5_05_hybrid_experiment run [--layer A|B] [--resume]
python experiments/h5_05_hybrid_experiment/verify_metrics.py
python -m pytest -p no:cacheprovider experiments/h5_05_hybrid_experiment/tests
cd experiments/h5_05_hybrid_experiment/layer_b/target_app && python -m pytest -p no:cacheprovider   # fixture ↔ ground truth
```

## Yapı
| Yol | Görev |
|---|---|
| `config.py` | Yollar, deney kimliği, yöntemler |
| `reference.py` | Referans gereksinim ↔ değerlendirme etiketi ayrımı (etiket maskeleme + sızıntı kontrolü) |
| `normalize.py` | Adayın AST tabanlı anlamsal imzası |
| `hybrid.py` | Deterministik birleştirme politikası, kaynak (provenance) kayıtları |
| `layer_b_inputs.py` | Katman B dondurma doğrulaması ve etiket maskeli üretici girdileri |
| `runner.py` | Manifest, hibrit, yalıtılmış çalıştırma, atomik kontrol noktaları (`--resume`) |
| `metrics.py` | TP/FP/FN, P/R/F1, ilk geçiş çalıştırılabilirliği, doğrulamalar |
| `verify_metrics.py` | Metrik motorundan bağımsız çapraz kontrol (yalnızca CSV + ground truth) |
| `reporting.py` | JSON/CSV/MD/JSONL çıktıları |
| `layer_b/` | Kontrollü hedef uygulama, donmuş ground truth (`FROZEN.json`), üretici girdileri ve çıktıları |
| `generated_tests/{A,B}/` | Hibritin nihai test modülleri |
| `results/` | `scenario_manifest.json`, `experiment_config.json`, `hybrid_candidates.jsonl`, `hybrid_decisions.jsonl`, `raw_generation_results.json`, `execution_results.json/csv`, `ground_truth_matches.json/csv`, `metrics_summary.json`, `comparison_table.csv/md`, `coverage_report.json`, `failure_analysis.json`, `logs/` |
| `reports/` | Deney raporu, AC izlenebilirliği, test kanıtı, H5-06 devir paketi |
| `results/history/` | Geçersiz kılınmış önceki koşular (deney geçmişi) |
| `tests/` | Metrik motoru, hibrit politika ve Katman B bütünlük testleri |
