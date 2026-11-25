"""Deney yapılandırması ve yollar — H5-05 / Issue #43.

İki değerlendirme katmanı:

* **Katman A (ana karşılaştırma):** H5-04'ün (#42) değiştirilmemiş 20 geliştirme senaryosu
  (H3-03 ``split.json`` → ``dev``). Kural tabanlı ve LLM çıktıları H3-04/H3-05'in donmuş ilk-geçiş
  artefaktlarıdır; hibrit aynı senaryolarda bunları birleştirir.
* **Katman B (kontrollü ek geliştirme):** ayrı ``Task`` kaynağı üzerinde 17 senaryo (5 HTTP metodu,
  3 bağımsız etiketli kusur). Mühürlü H3-03 test kümesinden türetilmemiştir; ground truth üretimden
  önce dondurulmuştur (``layer_b/FROZEN.json``).
"""
from __future__ import annotations


from agent.evaluation import manifest as mf

REPO = mf.REPO
EXP = REPO / "experiments" / "h5_05_hybrid_experiment"
LAYER_B = EXP / "layer_b"
RESULTS = EXP / "results"
GENERATED = EXP / "generated_tests"
CHECKPOINTS = RESULTS / "checkpoints"
H504 = REPO / "experiments" / "h5_04_generation_experiment"
H504_MANIFEST = H504 / "manifest.json"
H504_PER_SCENARIO = H504 / "results" / "per_scenario.csv"
SAMPLE_APP = REPO / "benchmarks" / "drf_fixtures" / "sample_app"

EXPERIMENT_ID = "h5-05-hybrid-v1"
EXPERIMENT_VERSION = "1.0.0"
HYBRID_GENERATOR_ID = "experiments.h5_05_hybrid_experiment.hybrid"
HYBRID_VERSION = "1.0.0"
METHODS = ("rule_based", "llm", "hybrid")
LAYERS = ("A", "B")
HTTP_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")

#: Model bilgisi: H3-05 üretim raporundan doğrulanır (planlanan ↔ gerçekte kullanılan ayrımı).
PLANNED_MODEL = "Llama 3.3 70B (Issue #31 planı)"
LLM_PROVIDER = "groq"

LAYER_B_FILES = {
    "endpoints": LAYER_B / "endpoint_summary.json",
    "ground_truth": LAYER_B / "ground_truth.json",
    "ground_truth_schema": LAYER_B / "ground_truth.schema.json",
    "scenarios": LAYER_B / "scenarios.json",
    "scenarios_schema": LAYER_B / "scenarios.schema.json",
    "target_app": LAYER_B / "target_app",
    "frozen": LAYER_B / "FROZEN.json",
}
#: Katman B üretici girdileri (değerlendirme etiketleri maskelenmiş görünüm) ve üretim çıktıları.
LAYER_B_INPUTS = LAYER_B / "generator_inputs"
LAYER_B_RB = LAYER_B / "generated" / "rule_based"
LAYER_B_LLM = LAYER_B / "generated" / "llm"
