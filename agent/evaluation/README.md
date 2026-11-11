# agent.evaluation — H3-06 baseline değerlendiricisi (Issue #32)

İki Pytest üreticisinin (H3-04 kural tabanlı, H3-05 LLM) ilk geçiş çıktılarını H3-03 bağımsız test kümesi
üzerinde **aynı hatla** değerlendirir. Metodoloji: [`docs/evaluation/h3-06/methodology.md`](../../docs/evaluation/h3-06/methodology.md).

```bash
python -m agent.evaluation verify   # manifest ↔ veri ve artefakt özetleri
python -m agent.evaluation run      # doğrula, değerlendir, experiments/h3_06_baseline_evaluation/results/ yaz
python -m agent.evaluation freeze   # yalnızca bilinçli sürüm değişikliğinde
(cd agent/evaluation && pytest -q)  # 86 test
```

| Modül | Görev |
|---|---|
| `manifest.py` | Dondurulmuş manifest oluşturma/doğrulama, LF-normalleştirilmiş SHA-256, ground truth birleştirme |
| `artifacts.py` | Senaryo ↔ test eşleme (iki baseline için ortak yapı), sözdizimi ve güvenlik ön kontrolü |
| `execution.py` | Senaryo başına yalıtılmış `--collect-only` ve çalıştırma, zaman aşımı, sonuç sınıflandırma |
| `pytest_probe.py` | Aşama ve istisna türünü kaydeden gözlemci pytest eklentisi (test kodunu değiştirmez) |
| `metrics.py` | TP/FP/TN/FN (split.md §4.3), tam kesirli P/R/F1, "Ölçülemedi" kuralları, hedef karşılaştırması |
| `reporting.py` | Deterministik JSON / CSV / Markdown çıktıları |

Bağımlılıklar: `experiments/h3_04_rule_based_baseline/requirements.txt` (LiteLLM gerekmez; LLM'e istek gönderilmez).
