# H3-06 — Yeniden Üretim Talimatları

Depo kök dizininde, Python 3.11+ ile:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r experiments/h3_04_rule_based_baseline/requirements.txt
```

H3-05 ayıklama işlevi için LiteLLM gerekmez; yalnızca H3-05 birim testleri için:
`pip install -r experiments/h3_05_llm_baseline/requirements.txt`.

## 1. Veri ve manifest doğrulama

```bash
python benchmarks/reference_cases/scripts/check_references.py
python -m agent.evaluation verify
```

## 2. Değerlendirmeyi çalıştırma (≈1 dk, ağ erişimi gerekmez)

```bash
python -m agent.evaluation run
```

Çıktılar `experiments/h3_06_baseline_evaluation/results/` altına yazılır. Belirlenimcilik kontrolü:

```bash
git diff --exit-code -- experiments/h3_06_baseline_evaluation/results/metrics.json experiments/h3_06_baseline_evaluation/results/per_scenario.csv experiments/h3_06_baseline_evaluation/results/rule_based/results.json experiments/h3_06_baseline_evaluation/results/llm/results.json
```

## 3. Değerlendirici testleri

```bash
cd agent/evaluation && python -m pytest -q
```

## 4. Manifesti yeniden dondurma

`python -m agent.evaluation freeze` yalnızca bilinçli bir sürüm değişikliğinde (yeni test kümesi veya
yeni baseline çıktısı) çalıştırılmalı, `manifest_version` artırılmalı ve gerekçesi kaydedilmelidir.
Sonuca bakarak manifesti yeniden dondurmak bağımsız değerlendirmeyi geçersiz kılar.

## 5. LLM çıktısını yeniden üretmek (isteğe bağlı, API anahtarı gerekir)

`experiments/h3_05_llm_baseline/.env.example` → `.env`; `python -m agent.test_generation.llm all`.
Yeni çıktı yeni bir manifest sürümü gerektirir; H3-06 sonuçları PR #83 artefaktlarına aittir.
