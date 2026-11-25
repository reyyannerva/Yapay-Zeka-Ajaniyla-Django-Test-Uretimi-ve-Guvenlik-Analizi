# H5-04 — Kural tabanlı ve LLM tabanlı test üretimi deneyi (geliştirme kümesi) · Issue #42

Kural tabanlı (H3-04/#30) ve Groq LLM tabanlı (H3-05/#31) Pytest üreticilerinin **ilk geçiş
(onarımsız)** çıktılarını, H3-03 **geliştirme kümesinde** (20 senaryo) aynı hatla karşılaştırır.
Ölçülen: üretim kalitesi (sözdizimi geçerliliği, pytest toplanabilirliği) ve **çalıştırılabilirlik**
(PASS / FAIL / ERROR / TIMEOUT, ayrı ayrı). Değerlendirme hattı `agent.evaluation` (#32)
modüllerinden **değiştirilmeden** yeniden kullanılır.

## Kapsam ve #32 ile ilişki

- **Yalnızca geliştirme kümesi** (`split.json` `development`, 20 senaryo). Bağımsız/mühürlü test
  kümesine (`test_set.json`, 18 senaryo) **dokunulmaz** (veri sızıntısı yasağı, bkz.
  `benchmarks/reference_cases/split.md`).
- Geliştirme kümesinde **bilinen güvenlik açığı yoktur**; bu nedenle güvenlik tespiti metriği
  (TP/FP/TN/FN, F1) bu deneyde **"Ölçülemedi"** olur. Bu beklenen ve dürüst sonuçtur; odak
  çalıştırılabilirliktir.
- Dev metot kapsamı: **GET 9, POST 9, PUT 1 (405), DELETE 1 (405), PATCH 0.** Tek PUT/DELETE
  method-not-allowed (405) senaryolarıdır. **Gerçek güncelleme/silme (PUT/PATCH/DELETE, 2xx/4xx)
  işlemleri ve 3 bilinen güvenlik açığı mühürlü test kümesindedir ve #32 (H3-06) ile
  değerlendirilir.** Bu deney #32'yi tamamlar.

## Üretim çıktıları nasıl elde edildi (tekrarlanabilirlik)

- **Kural tabanlı:** deterministik; `experiments/h3_04_rule_based_baseline` donmuş çıktıları
  (#30) yeniden kullanıldı.
- **LLM:** `experiments/h3_05_llm_baseline` donmuş çıktıları (#31) yeniden kullanıldı
  (model `groq/openai/gpt-oss-120b`, prompt `pytest_v1`, temperature 0.0). **Bu deneyde Groq'a
  yeni istek gönderilmedi** — tekrarlanabilirlik ve maliyet için ham/donmuş ilk-geçiş yanıtları
  kullanıldı. İz kaydı (model/prompt/girdi SHA'ları) `manifest.json` içindedir.

Manifest (`manifest.json`), dev senaryo kimliklerini, ground truth sürüm/özetini, metot kapsamını
ve iki baseline'ın donmuş artefakt SHA-256'larını sabitler; `run` öncesi yeniden doğrulanır.

## Çalıştırma

Depo kökünden (ortam: Python 3.11 + `Django`, `djangorestframework`, `pytest`, `pytest-django`,
`jsonschema` — ör. `backend/bvenv` veya `experiments/h3_04_rule_based_baseline/requirements.txt`):

```bash
python -m experiments.h5_04_generation_experiment freeze   # manifesti (yeniden) dondur
python -m experiments.h5_04_generation_experiment verify   # manifest ↔ veri/artefakt özetleri
python -m experiments.h5_04_generation_experiment run      # dev kümesinde değerlendir + results/ yaz
(python -m pytest experiments/h5_04_generation_experiment/tests -q)   # birim testleri
```

Testler yalnızca Django test istemcisiyle kontrollü `benchmarks/drf_fixtures/sample_app`'e karşı,
geçici test veritabanında çalışır; dış hedef veya ağ kullanılmaz (güvenlik ön kontrolü
`agent.evaluation`'dan gelir). Ortam yüklenemezse sonuçlar `ENVIRONMENT_ERROR` olarak **dürüstçe**
raporlanır (sahte PASS yok).

## Çıktılar (`results/`) ve #43 için şema

- `results.json` — ham satırlar + baseline başına metrik + manifest özeti + ortam + `cross_reference`.
- `per_scenario.csv` — her (baseline × senaryo): `scenario_id, baseline, http_method, user_role,
  secure_status, outcome, pytest_summary, syntax_valid, collected, collected_count, exc_type,
  observed_status, evidence`.
- `metrics.csv` — baseline başına özet (sözdizimi/toplanma/çalıştırılabilirlik oranları, PASS/FAIL/
  ERROR/NOT_RUN sayıları).
- `comparison.md` — okunur karşılaştırma tablosu + dev metot kapsamı + #32 atıf bölümü.
- `results/<baseline>/logs/<senaryo>/` — çalıştırılan modül, pytest toplama/çalıştırma günlükleri ve
  probe kaydı (geçici yollar `<WORK>`, depo yolu `<REPO>` ile maskeli).

**H5-05 (#43)** metrik analizi/karşılaştırma tablosu bu alanları doğrudan kullanabilir.

## Son koşu özeti (kanıt)

2026-11-26 koşusunda (ortam yüklendi): her iki baseline için **20/20 sözdizimi geçerli, 20/20
toplanabilir, ilk geçişte çalıştırılabilir 1.0000, 20/20 PASS**, güvenlik F1 "Ölçülemedi" (dev'de
açık yok). Ayrıntı: `results/comparison.md`.
