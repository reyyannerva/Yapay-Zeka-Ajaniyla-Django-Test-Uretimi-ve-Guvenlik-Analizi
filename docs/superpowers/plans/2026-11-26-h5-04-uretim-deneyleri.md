# H5-04 (#42) — Üretim Deneyleri Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Kural tabanlı (#30) ve LLM (#31) Pytest üreticilerini **geliştirme kümesinde** (20 senaryo) karşılaştırmalı çalıştırıp sözdizimi/toplanma/çalıştırılabilirlik ve PASS/FAIL/ERROR/TIMEOUT sonuçlarını tekrarlanabilir JSON/CSV/MD olarak üreten bağımsız bir deney paketi.

**Architecture:** `experiments/h5_04_generation_experiment/` altında, `agent.evaluation` (#32) ve üreticilerin modüllerini **salt-okunur kütüphane** olarak kullanan ince bir orkestrasyon paketi. Dev manifesti, çalıştırma orkestrasyonu ve dev'e özgü raporlama #42 tarafında yazılır; sınıflandırma (`execution.evaluate_baseline`), metrik (`metrics.compute`), senaryo↔artefakt eşleme (`artifacts.ADAPTERS`) ve manifest yardımcıları (`manifest.*`) #32'den import edilir.

**Tech Stack:** Python 3.11, stdlib (argparse, json, csv, hashlib, pathlib), pytest; çalıştırma için mevcut `agent.evaluation` + `benchmarks/drf_fixtures/sample_app` (Django/DRF test istemcisi). Ortam: `uv` + Python 3.11.

**Spec:** `docs/superpowers/specs/2026-11-25-h5-04-uretim-deneyleri-tasarim.md`

## Global Constraints

- **Ekip sınırı:** `agent/evaluation/**` (#32) ve `agent/test_generation/rule_based/**` (#30) **değiştirilmez**; yalnızca import edilir. `agent/test_generation/llm/**` (#31) Merve'nin — bu deneyde yalnızca donmuş çıktısı kullanılır.
- **Yalnızca geliştirme kümesi:** `split.json` `scenario_split == "dev"` olan 20 senaryo. Test kümesi (18) bu deneye **girmez** (sızıntı yasağı).
- **LLM yeniden üretimi YOK:** donmuş h3_05 çıktıları (model `groq/openai/gpt-oss-120b`, prompt `pytest_v1`, temperature 0.0) yeniden kullanılır; Groq'a istek gönderilmez.
- **Kanonik enum:** sonuç özetleri `TestExecution` ile uyumlu (PASS/FAIL/ERROR/TIMEOUT; ERROR ≠ TIMEOUT); testin çalıştırılabilirliği ile uygulamanın geçmesi ayrı tutulur.
- **Determinizm & biçim:** JSON `json.dumps(..., ensure_ascii=False, indent=2) + "\n"`, LF satır sonu, UTF-8; CSV satırları senaryo kimliğine göre sıralı; geçici yollar `<WORK>`/`<REPO>` ile maskeli (execution zaten yapıyor).
- **Sır yok:** `.env`/anahtarlar koda/log/rapora yazılmaz (execution ortamı zaten `GROQ_`/`OPENAI_`/`ANTHROPIC_` değişkenlerini siliyor).
- **Uydurma yok:** çalıştırılmamış test "başarılı" raporlanmaz; ortam hatası üretici hatasından ayrı (`ENVIRONMENT_ERROR`).
- **Git:** branch `feat/h5-04-uretim-deneyleri`, güncel `main`'den; Türkçe conventional-commit; **AI/Claude imzası YOK**; commit/push/PR yalnızca kullanıcı onayıyla.

## Review Focus

- **Rule-based desteklemeyen dev senaryosu** (ör. bazı GET/POST/MNA): adapter `NO_ARTIFACT` döner → çökme değil, satırda `NO_ARTIFACT` + rapora "üretilmedi" yansır. (Task 2 testi.)
- **Ortam yüklenemezse** (sample_app bağımlılıkları yok): tüm satırlar `ENVIRONMENT_ERROR`, koşu tamamlanır, rapor bunu açıkça gösterir, sahte PASS yok. (Task 2 testi.)
- **Dev senaryosunun ground_truth kaydı yoksa:** manifest `build` `IntegrityError` ile durur (değerlendirme başlamaz). (Task 1 testi.)
- **Determinizm:** aynı girdiyle ikinci `run` birebir aynı `results.json`/CSV üretir. (Task 3 testi.)
- **Sızıntı koruması:** dev ∩ test = ∅; test kümesi kimlikleri dev koşusuna asla girmez. (Task 1 testi.)

---

### Task 1: Dev deney manifesti (freeze/verify)

**Files:**
- Create: `experiments/h5_04_generation_experiment/__init__.py`
- Create: `experiments/h5_04_generation_experiment/manifest.py`
- Create: `experiments/__init__.py` (yoksa; boş — `python -m experiments.h5_04_generation_experiment` için)
- Test: `experiments/h5_04_generation_experiment/tests/__init__.py`, `.../tests/test_manifest.py`

**Interfaces:**
- Consumes (from `agent.evaluation.manifest` as `mf`): `mf.REPO`, `mf.sha256(path)`, `mf.rel(path)`, `mf.load_json(path)`, `mf.ground_truth_index(path=GROUND_TRUTH)`, `mf.evaluation_records(ids, gt)`, `mf.coverage(records)`, `mf._artifact_files(baseline)`, `mf.IntegrityError`; `split.json` → dev kimlikleri.
- Produces:
  - `DEV_IDS() -> list[str]` — `split.json` `scenario_split` değeri `"dev"` olan senaryo kimlikleri, kaynak dosyadaki sırayla.
  - `build() -> dict` — dev manifesti (aşağıdaki alanlar).
  - `write(path=MANIFEST) -> dict`, `verify(manifest) -> list[str]`.
  - Modül sabitleri: `MANIFEST = experiments/h5_04_generation_experiment/manifest.json`, `OUT = experiments/h5_04_generation_experiment`, `SPLIT = benchmarks/reference_cases/split.json`, `MANIFEST_VERSION = "1.0.0"`.

- [ ] **Step 1: Write the failing test**

```python
def test_dev_ids_are_the_20_development_scenarios():
    ids = manifest.DEV_IDS()
    assert len(ids) == 20
    split = json.loads((REPO/"benchmarks/reference_cases/split.json").read_text(encoding="utf-8"))
    assert all(split["scenario_split"][i] == "dev" for i in ids)
    test_ids = set(json.loads((REPO/"benchmarks/reference_cases/test_set.json").read_text())["scenario_ids"])
    assert set(ids).isdisjoint(test_ids)  # sızıntı yok

def test_build_manifest_has_dev_records_and_provenance():
    m = manifest.build()
    assert m["dataset"]["scenario_count"] == 20
    assert m["dataset"]["split"] == "development"
    assert m["baselines"]["llm"]["model"] == "groq/openai/gpt-oss-120b"
    assert m["baselines"]["rule_based"]["deterministic"] is True
    assert "llm_reused_from" in m["baselines"]["llm"]  # H3-05 yeniden kullanım notu
    assert m["cross_reference"]["issue"] == "#32"  # 5-metot/güvenlik atfı

def test_verify_round_trips_clean():
    m = manifest.build()
    assert manifest.verify(m) == []

def test_build_raises_if_dev_scenario_missing_ground_truth(monkeypatch):
    # ground_truth_index'i eksik bir kayıt döndürecek şekilde yamalayıp IntegrityError beklenir
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest experiments/h5_04_generation_experiment/tests/test_manifest.py -v`
Expected: FAIL (module/fonksiyon yok).

- [ ] **Step 3: Implement `manifest.py`**

`DEV_IDS()`: `split.json` yükle; `scenario_split` sözlüğünden değeri `"dev"` olanları, `scenarios.json`'daki görülme sırasıyla (veya split.json'daki anahtar sırasıyla) döndür. `build()`: `mf.ground_truth_index()` + `mf.evaluation_records(DEV_IDS(), gt)` ile kayıtlar; `mf.coverage(records)`; baseline provenance'ı `mf._artifact_files` SHA'larıyla (#32 ile aynı), `llm` için ek `"llm_reused_from": "experiments/h3_05_llm_baseline (#31)"` ve `"first_pass_only": True`; `dataset.split = "development"`, `cross_reference = {"issue": "#32", "evaluation": "experiments/h3_06_baseline_evaluation", "note": "PUT/PATCH/DELETE ve bilinen güvenlik açıkları mühürlü test kümesinde #32'de değerlendirilir"}`. `write()`/`verify()` #32 desenine birebir (SHA uyuşmazlığı → problem listesi). Donmuş test kümesinin INTEGRITY.txt kontrolü dev için gereksiz; yalnızca `ground_truth.json` + artefakt SHA'ları doğrulanır.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest experiments/h5_04_generation_experiment/tests/test_manifest.py -v`
Expected: PASS.

- [ ] **Step 5: Freeze the manifest and eyeball it**

Run: `python -c "from experiments.h5_04_generation_experiment import manifest as m; m.write()"` → `experiments/h5_04_generation_experiment/manifest.json` yazılır; 20 senaryo, metot kapsamı (GET/POST + method-not-allowed), `missing_methods` PUT/PATCH/DELETE içermeli.

- [ ] **Step 6: Commit**

```bash
git add experiments/__init__.py experiments/h5_04_generation_experiment/__init__.py \
  experiments/h5_04_generation_experiment/manifest.py experiments/h5_04_generation_experiment/manifest.json \
  experiments/h5_04_generation_experiment/tests/
git commit -m "feat(h5-04): geliştirme kümesi deney manifesti (dev 20 senaryo, #32 atfı)"
```

---

### Task 2: Deney orkestrasyonu (koşu + sınıflandırma + metrik)

**Files:**
- Create: `experiments/h5_04_generation_experiment/experiment.py`
- Test: `.../tests/test_experiment.py`

**Interfaces:**
- Consumes: `manifest.build/DEV_IDS` (Task 1); `agent.evaluation.artifacts.ADAPTERS`; `agent.evaluation.execution.evaluate_baseline(records, artifacts, log_dir, timeout, env_ok)`, `execution.check_environment()`; `agent.evaluation.metrics.compute(Iterable[Outcome])`, `metrics.Outcome`.
- Produces:
  - `run_experiment(out: Path, timeout: int, baselines: list[str], keep_logs: bool, env_ok: bool | None = None) -> dict` — döndürür `{"results": {baseline: [row,...]}, "metrics": {baseline: compute(...)}, "manifest": {...}, "environment_check": {...}}`. `results` satırları `evaluate_baseline` çıktısıdır (scenario_id, http_method, outcome, syntax_valid, collected, exc_type, pytest_summary, ...).

- [ ] **Step 1: Write the failing test** — ortam ve adapter'ler enjekte edilebilir olmalı ki birim testi Django gerektirmesin.

```python
def test_env_down_marks_all_environment_error(monkeypatch):
    # evaluate_baseline'ı env_ok=False ile çağırınca tüm satırlar ENVIRONMENT_ERROR
    res = experiment.run_experiment(out=tmp, timeout=5, baselines=["rule_based"], keep_logs=False, env_ok=False)
    rows = res["results"]["rule_based"]
    assert rows and all(r["outcome"] == "ENVIRONMENT_ERROR" for r in rows)

def test_unsupported_scenario_is_no_artifact(monkeypatch):
    # ADAPTERS['rule_based'] bazı dev senaryoları için [] dönerse outcome NO_ARTIFACT
    ...

def test_metrics_f1_not_measurable_on_dev():
    res = experiment.run_experiment(out=tmp, timeout=5, baselines=["llm"], keep_logs=False, env_ok=False)
    assert res["metrics"]["llm"]["f1"]["display"] == "Ölçülemedi"  # dev'de pozitif yok
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest experiments/h5_04_generation_experiment/tests/test_experiment.py -v` → FAIL.

- [ ] **Step 3: Implement `experiment.py`**

`run_experiment`: manifesti yükle/doğrula (yoksa hata), `records = m["scenarios"]`, `ids = [r["scenario_id"] ...]`; `env_ok` verilmemişse `check_environment()`; her baseline için `arts = ADAPTERS[b](ids)`, `rows = evaluate_baseline(records, arts, log_dir, timeout, env_ok)`, `metrics = compute(Outcome(r["scenario_id"], r["http_method"], r["is_known_flaw"], r["outcome"]) for r in rows)`. Sözlüğü döndür. (Determinizm için senaryo sırası manifestten gelir.)

- [ ] **Step 4: Run tests to verify they pass** → PASS.

- [ ] **Step 5: Commit**

```bash
git add experiments/h5_04_generation_experiment/experiment.py experiments/h5_04_generation_experiment/tests/test_experiment.py
git commit -m "feat(h5-04): dev kümesi koşu orkestrasyonu (sınıflandırma + metrik, #32 modülleri yeniden kullanımı)"
```

---

### Task 3: Raporlama (JSON/CSV/MD + #32 atfı)

**Files:**
- Create: `experiments/h5_04_generation_experiment/reporting.py`
- Test: `.../tests/test_reporting.py`

**Interfaces:**
- Consumes: Task 2 `run_experiment` çıktı sözlüğü; `agent.evaluation.reporting.environment` (varsa ortam özeti için) — yoksa kendi küçük `environment()`'ımız.
- Produces:
  - `write_all(out: Path, summary: dict) -> None` — yazar:
    - `results/results.json` — ham satırlar + baseline başına metrik + manifest özeti + ortam + `cross_reference`.
    - `results/per_scenario.csv` — her (baseline × senaryo) satırı: scenario_id, baseline, http_method, outcome, pytest_summary, syntax_valid, collected, collected_count, exc_type, evidence(kısaltılmış).
    - `results/metrics.csv` — baseline başına: scenarios, syntax_valid oranı, collected oranı, first_pass_executable oranı, outcome sayıları.
    - `results/comparison.md` — okunur karşılaştırma tablosu + "HTTP metot kapsamı (dev)" + "5 metot ve güvenlik açıkları için bkz. #32 (mühürlü test kümesi)" bölümü.

- [ ] **Step 1: Write the failing test**

```python
def test_write_all_is_deterministic(tmp_path):
    summary = _fixture_summary()           # sentetik run_experiment çıktısı
    reporting.write_all(tmp_path, summary)
    first = (tmp_path/"results/results.json").read_bytes()
    reporting.write_all(tmp_path, summary)
    assert (tmp_path/"results/results.json").read_bytes() == first  # determinizm

def test_comparison_md_cites_issue_32(tmp_path):
    reporting.write_all(tmp_path, _fixture_summary())
    md = (tmp_path/"results/comparison.md").read_text(encoding="utf-8")
    assert "#32" in md and "mühürlü" in md.lower()

def test_per_scenario_csv_sorted_and_complete(tmp_path):
    reporting.write_all(tmp_path, _fixture_summary())
    rows = list(csv.DictReader((tmp_path/"results/per_scenario.csv").open(encoding="utf-8")))
    assert [r["scenario_id"] for r in rows if r["baseline"]=="llm"] == sorted(...)
```

- [ ] **Step 2: Run tests to verify they fail** → FAIL.

- [ ] **Step 3: Implement `reporting.py`** — deterministik yazım (LF, UTF-8, `ensure_ascii=False, indent=2`); CSV `csv` modülüyle, satırlar senaryo kimliğine göre sıralı; MD tablosu Task 2 metriklerinden; `cross_reference` bölümü sabit metinle.

- [ ] **Step 4: Run tests to verify they pass** → PASS.

- [ ] **Step 5: Commit**

```bash
git add experiments/h5_04_generation_experiment/reporting.py experiments/h5_04_generation_experiment/tests/test_reporting.py
git commit -m "feat(h5-04): deney raporlaması (JSON/CSV/MD, #32 atıflı karşılaştırma)"
```

---

### Task 4: CLI + uçtan uca gerçek koşu + README

**Files:**
- Create: `experiments/h5_04_generation_experiment/__main__.py`
- Create: `experiments/h5_04_generation_experiment/README.md`
- Create (koşu çıktısı): `experiments/h5_04_generation_experiment/results/**`
- Test: `.../tests/test_cli.py`

**Interfaces:**
- Consumes: `manifest.write/verify`, `experiment.run_experiment`, `reporting.write_all`.
- Produces: CLI `freeze | verify | run` (argümanlar: `--timeout` [vars. 120], `--baselines` [vars. rule_based llm], `--out`, `--no-logs`). Çıkış kodu: 0 başarı; 2 ortam/manifest sorunu.

- [ ] **Step 1: Write the failing test** — CLI `verify`'ın temiz manifest için 0 döndürmesi; `run --baselines rule_based` için (env_ok monkeypatch/enjekte) çıktı dosyalarının oluşması.

- [ ] **Step 2: Run tests to verify they fail** → FAIL.

- [ ] **Step 3: Implement `__main__.py`** — argparse; `freeze`→`manifest.write`; `verify`→`manifest.verify`; `run`→`experiment.run_experiment` + `reporting.write_all`; özet satırları stdout'a.

- [ ] **Step 4: Run unit tests** → PASS.

- [ ] **Step 5: Ortamı hazırla ve GERÇEK uçtan uca koşuyu çalıştır**

Ortam (sample_app + agent.evaluation bağımlılıkları) `uv`/py3.11 ile kurulu olmalı. Çalıştır:
`python -m agent.evaluation verify` benzeri bir ortam ön kontrolü + `python -m experiments.h5_04_generation_experiment run`.
Gerçek çıktı (`results/`) üretilir; stdout ve `comparison.md` **bu plana değil, gerçek sonuca** göre raporlanır. Ortam kurulamazsa satırlar `ENVIRONMENT_ERROR` olur; bu dürüstçe raporlanır ve kullanıcıya bildirilir (sahte sonuç yok).

- [ ] **Step 6: README yaz** — amaç, çalıştırma komutları, ortam/sürümler, sınırlılıklar ("LLM çıktısı H3-05'ten yeniden kullanıldı; H5'te yeniden üretilmedi", "PUT/PATCH/DELETE ve güvenlik açıkları mühürlü kümede #32'de"), #43'e girdi alan şeması.

- [ ] **Step 7: Tüm paket testlerini çalıştır**

Run: `python -m pytest experiments/h5_04_generation_experiment/tests/ -v` → tümü PASS (çıktı kullanıcıyla paylaşılır).

- [ ] **Step 8: Commit**

```bash
git add experiments/h5_04_generation_experiment/__main__.py experiments/h5_04_generation_experiment/README.md \
  experiments/h5_04_generation_experiment/results/ experiments/h5_04_generation_experiment/tests/test_cli.py
git commit -m "feat(h5-04): CLI, uçtan uca koşu ve README (dev kümesi üretim deneyi)"
```

---

### Task 5 (kod dışı, ayrı onay): Issue #42 metni + GitHub atama takası

Kod değil, dış işler — **kullanıcı onayıyla** yapılır, PR'dan ayrı:
- #42 issue metnini §2/§9'a göre düzelt (model adı `gpt-oss-120b`; çelişki çözümü: dev kümesi + #32 atfı).
- GitHub atamalarını takasla (#42 → Merve, #41 → Reyyan) — yalnızca kullanıcı isterse.

Bu task PR kapsamına girmez; tamamlanma için gerekli değildir.
