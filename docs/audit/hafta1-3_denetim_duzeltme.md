# Hafta 1–3 Denetimi — Bulgu ve Düzeltme Kaydı

Bağımsız Hafta 1–3 denetiminin (2026-11-11) bulguları, ilgili issue'ları, kök nedenleri ve düzeltme durumu.
Denetim yalnızca depodaki kanıta dayanır. Doğrulanamayan konular **doğrulanamadı** olarak bırakılmıştır.

- **Düzeltme PR 1** (Hafta 3 veri bütünlüğü): #81 — D-02, D-03, D-04.
- **Düzeltme PR 2** (Hafta 2 dokümantasyon tutarlılığı): D-01, D-05 ve D-06'nın uygun maddeleri.

## 1. Düzeltme matrisi

| Bulgu | Hafta | İlgili issue | Etkilenen dosyalar | Önem | Tür | Kök neden | Düzeltme | Otonom mu? | Gereken kullanıcı girdisi | Sonraki işlere etkisi | Doğrulama kanıtı | Durum |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D-01 | 2 | H2-02 #24, H2-04 #26 | `docs/database/*`, `docs/diagrams/er-diagrams/*`, `docs/architecture/technology_stack.md` | HIGH | Doğrulanmış kusur (dokümantasyon tutarsızlığı) | Revizyon 3 (`9a4324b`, 9 tablo) "(1)" ekli kopyalar olarak yüklendi; `docs/database/` revizyon 1'de (6 tablo) kaldı; teknoloji belgesi eskiyi "kanonik" gösteriyordu | Revizyon 3, içeriği değiştirilmeden `docs/database/` altına taşındı; ER dosya adları düzeltildi; referanslar ve durum listesi güncellendi; `docs/database/README.md` eklendi | Evet | Yok (revizyon kanıtla belirlendi, bkz. `docs/database/README.md`) | H4-01 #33'ü engelliyordu | Alan düzeyinde karşılaştırma; dosyalar `9a4324b` blob'larıyla bayt düzeyinde aynı; Django `check` / `makemigrations --dry-run` | PR 2'de düzeltildi |
| D-02 | 3 | H3-03 #29 | `benchmarks/reference_cases/{INTEGRITY.txt, scripts/check_references.py}` | MEDIUM | Doğrulanmış kusur | Özetler CRLF çalışma kopyasında hesaplanmış; git LF saklıyor; `.gitattributes` yoktu | Kanonik (LF normalize) özet; `INTEGRITY.txt` güncellendi, eski özetler korundu; `.gitattributes` | Evet | Yok | H3-06 #32'yi engelliyordu | `tests/test_integrity.py` (10 test); LF, `autocrlf=true` ve zorla CRLF klonlarında başarılı | PR 1'de (#81) düzeltildi |
| D-03 | 3 | H3-01 #27, H3-03 #29 | `export_scenarios_csv.py`, `export_ground_truth_csv.py` | LOW | Doğrulanmış kusur (tekrarlanabilirlik) | `csv` modülü varsayılan CRLF yazıyordu | `lineterminator="\n"`; `.gitattributes` | Evet | Yok | Yok | Dışa aktarım depodaki CSV'leri bayt düzeyinde üretiyor (2 + 1 test) | PR 1'de (#81) düzeltildi |
| D-04 | 3 | H3-01 #27, H3-03 #29; H3-06 #32'yi etkiler | `benchmarks/reference_cases/split.md`, `benchmarks/drf_fixtures/README.md` | LOW | Dokümantasyon sorunu | `label` iki veri kümesinde farklı anlam taşıyor (SC-FLW-003) | Anlamlar, SC-FLW-003 ve H3-06 TP/FP/TN/FN tanımı belgelendi; veri yeniden etiketlenmedi | Evet | Yok | H3-06 metrik tanımı | `split.md` §4.1–4.3 | PR 1'de (#81) düzeltildi |
| D-05a | 2 | H2-01 #23, H2-03 #25, H2-04 #26 | `docs/mockup/README.md` | LOW | Dokümantasyon sorunu | Figma bağlantısı bozuk Markdown (`[...]https://...`); bir diyagram bağlantısı var olmayan `.md` dosyasını gösteriyordu | Bağlantı sözdizimi düzeltildi; mevcut olmayan `akis-docker-guvenlik-raporlama.md` bağlantısı gerçek `.svg` dosyasına yönlendirildi | Evet | Yok | Yok | Markdown; 31 ekran görüntüsü ve diyagram bağlantılarının tamamı mevcut dosyalara çözülüyor | PR 2'de düzeltildi |
| D-05b | 2 | H2-04 #26 | Issue #26 yorumları, `technology_stack.md` | LOW | Eksik kanıt / eski yol | Yorumlar `docs/diagrams/er/` ve `docs/technology_stack.md` yollarını gösteriyor; gerçek yollar farklı | Depo belgelerindeki yollar düzeltildi; doğru yollar aşağıda (§3). Issue yorumları değiştirilmedi | Kısmen | İsteğe bağlı: issue yorumlarının yazar tarafından güncellenmesi | Yok | §3 | Belgeler düzeltildi |
| D-05c | 2 | H2-04 #26 | `docs/presentations/` (yok) | LOW | Eksik kanıt | 5 dakikalık sunum materyali depoya eklenmemiş | **Düzeltilmedi**: sunum dosyası uydurulamaz. Beklenen konum `docs/presentations/` (teknoloji belgesinde tanımlı) | Hayır | Sunum dosyasının (PDF/PPTX) eklenmesi | Yok | — | **Açık** |
| D-05d | 2 | H2-01 #23, H2-03 #25, H2-04 #26 | Figma prototipi | — | Doğrulanamadı | Figma'ya bu ortamdan erişilemedi (HTTP 000) | — | Hayır | Prototipin bir ekip üyesi tarafından açılıp doğrulanması | Yok | — | **Doğrulanamadı** |
| D-06a | 1–3 | — (depo bakımı) | `README.md` | LOW | Dokümantasyon sorunu | Durum "Planning"; tamamlanan çıktılara gezinme yoktu | Durum, çıktı bağlantıları ve doğrulama komutları eklendi | Evet | Yok | Yok | Komutlar depo kökünden çalıştırılıp doğrulandı | PR 2'de düzeltildi |
| D-06b | 1–3 | #17–#19, #21, #22, #24, #27–#30 | Issue kontrol listeleri | LOW | Dokümantasyon sorunu | Kapanmış issue'larda işaretlenmemiş maddeler | Kanıta göre değerlendirildi (§2); issue'lar düzenlenmedi | Kısmen | Kanıtı olan maddelerin issue sahiplerince işaretlenmesi | Yok | §2 | Değerlendirildi |
| D-06c | 1–3 | — | `.github/workflows/` (yok) | LOW | Öneri | CI olmadığından D-02 birleştirmede fark edilmedi | Minimal iş akışı önerildi (§4); otomatik olarak eklenmedi | Hayır | Ekleme kararı ve GitHub Actions izinleri | Yok | — | **Öneri** |
| D-06d | 3 | H3-04 #30 | `experiments/h3_04_rule_based_baseline/endpoint_summary.json` | LOW | Gözlem | `pk` tipi `int`; DRF router `[^/.]+` kabul ediyor | Değişiklik gerekmiyor; AST entegrasyonunda (H6-07 #76) ele alınmalı | — | Yok | H6-07 | — | FUTURE |

Planlanmış gelecek işler (kusur değildir): AST endpoint çıkarımı (H6-07 #76); SC-FLW-003 içerik düzeyi
doğrulaması; H3-04 sınıflarının `test_executions` alanlarına eşlenmesi (H6-03 #47); referans gereksinim
kategorilerinin eşlenmesi (H4-04 #36); Colab doğrulaması (H3-02, isteğe bağlı).

## 2. Kapanmış issue'larda işaretlenmemiş kontrol listeleri (kanıt değerlendirmesi)

Issue gövdeleri bu düzeltmede **değiştirilmedi**. Aşağıdaki değerlendirme, issue sahiplerinin kutuları
kanıta göre işaretlemesi için hazırlanmıştır.

| Issue | İşaretlenmemiş maddeler | Depodaki kanıt | Öneri |
|---|---|---|---|
| #17 H1-01 | Tüm yapılacaklar ve kriterler | İST-01–16 ayrı issue'lar (#1–#16), `requirement` etiketi | Kanıtlı maddeler işaretlenebilir; "proje öneri formuyla tutarlı" maddesi öneri formu depoda olmadığından **doğrulanamadı** |
| #18 H1-02 | Tüm maddeler | `docs/diagrams/sistem-mimarisi.svg` (bileşenler, Celery/Redis, Docker sınırları, bağımsız referans) | İşaretlenebilir |
| #19 H1-03 | Tüm maddeler | `docs/diagrams/akis-docker-guvenlik-raporlama.svg` (PASS/FAIL/TEKNİK, TIMEOUT/OOM, doğrulanmış/olası/belirsiz) | İşaretlenebilir |
| #21 H1-05 | 2 yapılacak, 5 kriter | `docs/diagrams/ai-pipeline/*.svg` ("Geçersiz Testi Kaydet / Tek düzeltme sonrası teknik hata", "İzole Test Runner'a Aktar", "Değişmez girdiler") | İşaretlenebilir |
| #22 H1-06 | Tüm maddeler | `docs/diagrams/project-ast-reference/*.svg` ("HEDEF PROJE KODU ÇALIŞTIRILMAZ", "Bağımsız beklentiler; AST çıktısından türetilmez") | İşaretlenebilir |
| #24 H2-02 | Tüm maddeler | `docs/database/` (revizyon 3, PR 2 sonrası) | İşaretlenebilir |
| #26 H2-04 | (Tümü işaretli) | Sunum materyali depoda **yok** | "Sunum materyalleri GitHub reposunda mevcut" kriteri kanıtsız işaretli; D-05c kapanana kadar karşılanmamıştır |
| #27 H3-01 | Tüm maddeler | `benchmarks/drf_fixtures/`; 69 test geçiyor | İşaretlenebilir |
| #28 H3-02 | Tüm maddeler | `experiments/h3_02_eda/`; 67 test, notebook 23/23 hücre | İşaretlenebilir |
| #29 H3-03 | Tüm maddeler | `benchmarks/reference_cases/`; sabitleme kriteri #81 ile doğrulanabilir hâle geldi | İşaretlenebilir |
| #30 H3-04 | Tüm maddeler | `agent/test_generation/rule_based/`, `experiments/h3_04_rule_based_baseline/`; 122 test | İşaretlenebilir |

## 3. Güncel teslim yolları (#26 yorumlarındaki eski yolların karşılığı)

| Yorumdaki yol | Güncel yol |
|---|---|
| `docs/diagrams/er/` | `docs/diagrams/er-diagrams/` |
| `docs/technology_stack.md` | `docs/architecture/technology_stack.md` |
| `er_diagram_*.{svg,png,mmd,md}` ("(1)" ekli kopyalar) | `docs/diagrams/er-diagrams/er_diagram_*.{svg,png,mmd,md}` |
| Veritabanı şeması / veri sözlüğü | `docs/database/` (revizyon 3, kanonik) |
| Sunum materyali | `docs/presentations/` — **eklenmedi** |

## 4. CI önerisi (eklenmedi)

D-02, CI olmadığı için birleştirmede fark edilmedi. Aşağıdaki minimal iş akışı mevcut testleri çalıştırır.
Depoya **eklenmedi**, çünkü GitHub Actions üzerinde çalıştırılarak doğrulanmadı. Eklemeden önce ekip kararı ve
Actions izinleri gerekir. Önerilen konum: `.github/workflows/tests.yml`.

```yaml
name: tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - run: pip install -r benchmarks/drf_fixtures/sample_app/requirements.txt -r experiments/h3_02_eda/requirements.txt -r experiments/h3_04_rule_based_baseline/requirements.txt
      - run: cd benchmarks/drf_fixtures && python scripts/validate_scenarios.py && cd sample_app && python manage.py check && pytest -q
      - run: cd benchmarks/reference_cases && python scripts/check_references.py && pytest -q
      - run: cd experiments/h3_02_eda && pytest -q
      - run: cd agent/test_generation/rule_based && pytest -q
      - run: python -m agent.test_generation.rule_based all --no-isolation
```
