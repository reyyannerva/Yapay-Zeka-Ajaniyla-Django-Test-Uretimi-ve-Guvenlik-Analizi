# H3-06 — Değerlendirme Metodolojisi (Issue #32)

Bu belge, H3-04 kural tabanlı (Baseline A) ve H3-05 LLM tabanlı (Baseline B) Pytest üreticilerinin
**aynı bağımsız test kümesi ve aynı değerlendirme hattı** üzerinde nasıl karşılaştırıldığını tanımlar.
Uygulama: `agent/evaluation/`; çıktılar: `experiments/h3_06_baseline_evaluation/`.

## 1. Veri ayrımı ve değerlendirme kümesi

| Öğe | Değer |
|---|---|
| Değerlendirme kümesi | `benchmarks/reference_cases/test_set.json` (H3-03, sürüm 1.0.0), **18 senaryo** |
| Geliştirme kümesi | `split.json` → development, 20 senaryo — metriklere **katılmaz** |
| Ground truth | `benchmarks/reference_cases/ground_truth.json` (tüm kayıtlar `validation_status = verified`) |
| Bilinen kusurlar (pozitif sınıf) | 3: SC-FLW-001 (PUT, 403→200), SC-FLW-002 (DELETE, 403→204), SC-FLW-003 (GET, içerik sapması) |
| Sabitleme | `evaluation_manifest.json` (SHA-256, CRLF→LF normalleştirilmiş); `INTEGRITY.txt` ile çapraz doğrulanır |

Senaryo kimlikleri: SC-AUT-002, SC-AUT-003, SC-AUT-004, SC-AUZ-001, SC-AUZ-002, SC-AUZ-003, SC-DEL-001,
SC-DEL-002, SC-FLW-001, SC-FLW-002, SC-FLW-003, SC-INP-003, SC-NF-001, SC-NF-002, SC-UPD-001, SC-UPD-002,
SC-UPD-003, SC-UPD-004.

**Kapsam:** GET 1, POST 0, PUT 7, PATCH 4, DELETE 6. Güvenli durum kodları: 200×5, 204×2, 400×1, 401×3,
403×5, 404×2. Roller: anonim, kullanıcı, sahip, yönetici. **Eksik kapsam:** POST yöntemi, 201 ve 405 durum
kodları test kümesinde yoktur (H3-03 bölmesinin sonucu; `split.md` §4.3 kural 4 bunu önceden kayda geçirmiştir). Bu eksik **giderilmemiştir**; test
kümesini sonuçtan sonra değiştirmek bağımsızlığı bozacağından sınırlılık olarak raporlanır
(`limitations.md`). Demo, beş yöntemi göstermek için geliştirme kümesinden POST örneği kullanır ve bunu
metrik dışı olarak işaretler.

**Dahil etme:** test_set.json'daki her senaryo; ground truth kaydı doğrulanmış; her baseline'ın ilk geçiş
(onarımsız) çıktısı. **Dışlama:** hiçbir senaryo sonuca bakılarak çıkarılmaz; geliştirme kümesi; kusursuz
senaryodaki teknik hata yalnızca güvenlik matrisinden (split.md §4.3 kural 2) çıkarılır.

## 2. Aynı girdi koşulu

Her iki üretici de aynı üç girdiyle çalışmıştır: `endpoint_summary.json` (H3-04 sözleşmesi),
`ground_truth.json`, `scenarios.json`. H3-05 raporundaki girdi özetleri, depodaki aynı içeriğin CRLF
kodlamasına eşittir (H3-05 Windows çalışma kopyasında üretilmiştir); içerik bayt düzeyinde aynıdır
(`integrity_evidence.md` §3, test: `test_both_generators_used_identical_input_content`).

İki üreticiye de güvenli beklenti (`expected_result.secure_status`, `behavior`) verilir; **cevap anahtarı**
(`is_known_flaw`, `observed_flawed_status`, `deviation_kind`, `split`) LLM istemlerine girmez (38 istem
dosyası taranmıştır). Kural tabanlı üretici kusur bilgisini yalnızca test docstring'ine açıklama olarak yazar;
doğrulama ifadeleri (assert) kusurlu ve kusursuz senaryolarda aynı kalıptadır ve güvenli beklentiden üretilir.

## 3. Değerlendirme hattı (her iki baseline için aynı)

1. **Artefakt eşleme:** Senaryo başına tam bir test. H3-04: yöntem modülünden senaryo fonksiyonu ve modül
   başlığı (importlar) **değiştirilmeden** kopyalanır. H3-05: ham model yanıtından (`raw_responses/`)
   H3-05'in kendi `extract_code` işleviyle ilk kod bloğu alınır — ilk geçiş çıktısı, onarım yok.
   Yok → `NO_ARTIFACT`; birden fazla → `DUPLICATE_ARTIFACT`.
2. **Sözdizimi:** `ast.parse` → `SYNTAX_INVALID`.
3. **Güvenlik ön kontrolü:** dış ağ/süreç modülleri (`requests`, `urllib`, `socket`, `subprocess`…),
   `testserver`/`localhost` dışı URL veya `os.system` → `UNSAFE_BLOCKED` (test çalıştırılmaz).
4. **Ortam ön kontrolü:** `django.setup()` + URLconf yüklenemezse `ENVIRONMENT_ERROR` (üreticiye yüklenmez).
5. **Toplama:** geçici, senaryoya özel dizinde `pytest --collect-only` → `COLLECTION_ERROR`.
6. **Çalıştırma:** ayrı pytest süreci, zaman aşımı 120 sn (`TIMEOUT`); `pytest_probe` eklentisi her aşamanın
   sonucunu ve istisna türünü kaydeder.
   * çağrı aşamasında `AssertionError` → **FAIL** (pozitif tahmin);
   * kurulum/teardown hatası, doğrulama dışı istisna (ör. `NoReverseMatch`), atlama/xfail → **ERROR**;
   * H3-04'ün `check=route` işaretli doğrulaması (yanlış URL üretimi) → **ERROR** (üretici hatası);
   * başarı → **PASS**.
7. Testler yalnızca Django test istemcisiyle kontrollü `sample_app`'e, pytest-django'nun geçici test
   veritabanında çalışır. API anahtarı ortam değişkenleri test süreçlerine aktarılmaz.

PASS / FAIL / ERROR özeti: `PASS`, `FAIL`, `ERROR` (toplama, zaman aşımı, ortam, çalışma hatası) ve
`NOT_RUN` (artefakt yok, sözdizimi geçersiz, güvenlik nedeniyle engellendi).

## 4. Metrik tanımları (split.md §4.3)

* **Değerlendirme birimi:** test kümesindeki senaryo için üretilen test.
* **Gerçek sınıf:** `is_known_flaw`. `label` alanı **kullanılmaz**.

| | Kusur var | Kusur yok |
|---|---|---|
| FAIL (doğrulama) | TP | FP |
| PASS | FN | TN |
| Test yok / teknik hata | FN | matris dışı (çalıştırılabilirlikte raporlanır) |

* Precision = TP/(TP+FP); Recall = TP/(TP+FN); F1 = 2PR/(P+R).
* Payda sıfırsa (veya P+R = 0) değer **"Ölçülemedi"** olarak raporlanır; 0 veya 1 ile doldurulmaz.
* **Sözdizimi geçerlilik oranı** = geçerli / artefaktı olan senaryo.
* **Toplanabilirlik** = pytest tarafından toplanan / 18.
* **İlk geçişte çalıştırılabilir test oranı** = (PASS + FAIL) / 18 — otomatik düzeltme öncesi ilk çıktı.
  FAIL çalıştırılabilir sayılır: bilinen kusuru yakalayan geçerli bir test üretim hatası değildir.
* Hedefler: F1 ≥ 0.80, çalıştırılabilirlik ≥ %70. Karşılaştırma `fractions.Fraction` ile tam yapılır.
* **Mutation score: Bu aşamada ölçülmedi.**

## 5. Belirlenimcilik

Sonuç dosyaları (`results.json`, `metrics.json`, CSV, `comparison.md`) zaman damgası, süre veya geçici yol
içermez; iki ardışık çalıştırma bayt düzeyinde aynı çıktıyı üretmiştir. Günlüklerde (`logs/`) yalnızca
pytest süre satırları değişir; geçici yollar `<WORK>`, depo yolu `<REPO>` ile maskelenir.
