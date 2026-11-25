# H5-05 — Test ve regresyon kanıtı (koşu 2, 2026-11-25, Linux, Python 3.13.18)

| Paket | Komut (depo kökünden) | Sonuç |
|---|---|---|
| H5-05 birim testleri | `python -m pytest -p no:cacheprovider experiments/h5_05_hybrid_experiment/tests` | 44 passed |
| Bağımsız metrik çapraz kontrolü | `python experiments/h5_05_hybrid_experiment/verify_metrics.py` | UYUŞUYOR |
| Katman B fixture ↔ ground truth | `cd experiments/h5_05_hybrid_experiment/layer_b/target_app && python -m pytest -p no:cacheprovider` | 19 passed |
| Katman B dondurma | `python -m experiments.h5_05_hybrid_experiment verify` | OK |
| H3-04 kural tabanlı | `cd agent/test_generation/rule_based && python -m pytest -p no:cacheprovider` | 132 passed |
| H3-05 LLM | `cd agent/test_generation/llm && python -m pytest -p no:cacheprovider` | 26 passed |
| H3-06 değerlendirme hattı | `cd agent/evaluation && python -m pytest -p no:cacheprovider` | 86 passed |
| H5-04 | `python -m pytest -p no:cacheprovider experiments/h5_04_generation_experiment/tests` | 17 passed |
| H3-02 EDA | `cd experiments/h3_02_eda && python -m pytest -p no:cacheprovider` | 67 passed |
| Backend | `cd backend && python -m pytest` | 471 passed |
| Frontend | `npx vitest run` / `npx tsc -b --noEmit` / `npm run build` | 255 passed / 0 hata / başarılı |

Not: H5-04 testleri kendi dizininden çalıştırılırsa `results/logs` altındaki üretilmiş test modülleri de
toplanır ve 44 toplama hatası oluşur. Bu davranış H5-04 değişmeden önce de vardı; H5-04 dosyalarına
dokunulmadı. H5-05'te aynı sorun `pytest.ini` (`testpaths = tests`) ile önlendi.
