# H3-02 | EDA Notebook ve Veri Kalitesi Analizi (Issue #28)

H3-01'de (#27, PR #77) hazırlanan **kontrollü Django/DRF senaryo veri kümesinin** kapsamını,
dağılımlarını ve veri kalitesini inceleyen, tekrarlanabilir keşifsel veri analizi (EDA) paketi.
Bulgular ve kapsam boşlukları bağımsız test kümesi ve ground truth hazırlığına (H3-03) girdi sağlar.

- **Girdi (değiştirilmez):** `benchmarks/drf_fixtures/scenarios/scenarios.json` (kanonik),
  `scenarios.csv` (türetilmiş; yalnızca tutarlılık kontrolü), `scenarios.schema.json`,
  `sample_app/catalog/fixtures/*.json`, `sample_app/**/urls.py`, `benchmarks/pygoat/`.
- **İlgili isterler:** İST-03, İST-13, İST-15, İST-16.
- Tüm sayılar çalışma anında hesaplanır; raporlarda elle yazılmış istatistik yoktur.

## Dizin yapısı

```
experiments/h3_02_eda/
├── H3_02_EDA_Veri_Kalitesi.ipynb   Çalıştırılmış (çıktılı) EDA notebook'u
├── scenario_eda/                   Yeniden kullanılabilir analiz paketi
│   ├── data.py                     Girdi bulma/yükleme, statik rota çözümleme, Django URL çözümlemesi,
│   │                               fixture'dan aktör–kaynak ilişkisi türetme
│   ├── quality.py                  Veri kalitesi kontrolleri (saf, test edilebilir fonksiyonlar)
│   ├── coverage.py                 Dağılımlar, çapraz tablolar, kapsam modeli, kapsam boşlukları
│   ├── report.py                   Rapor tabloları, CSV dışa aktarımı, Markdown özet
│   └── plots.py                    Grafikler (matplotlib)
├── tests/                          Birim testleri (sentetik) + gerçek veri/yeniden üretim testleri
├── reports/                        CSV tablolar + eda_summary.md (notebook üretir)
├── figures/                        PNG grafikler, 200 dpi (notebook üretir)
├── requirements.txt
└── pytest.ini
```

Konum gerekçesi: kök README'deki planlanan yapıda `benchmarks/` hedef uygulamalar ve veri
kümeleri, `experiments/` ise bu veriler üzerindeki analiz/deney çalışmaları için ayrılmıştır.
EDA bir analiz çıktısı olduğundan `experiments/h3_02_eda/` altına yerleştirilmiş ve H3-01
dizinine dokunulmamıştır.

## Yerel çalıştırma (Jupyter)

```bash
cd experiments/h3_02_eda
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

1. **Notebook'u açma:** `jupyter lab H3_02_EDA_Veri_Kalitesi.ipynb` (veya VS Code / Jupyter Notebook).
2. **Tüm hücreleri çalıştırma:** *Run → Run All Cells*. İlk hücre depo kökünü otomatik bulur;
   bulamazsa `H302_REPO_ROOT` ortam değişkenini depo köküne ayarlayın.
3. **Komut satırından baştan sona çalıştırma (arayüzsüz):**

```bash
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.record_timing=False H3_02_EDA_Veri_Kalitesi.ipynb
```

4. **Grafikleri inceleme:** grafikler notebook içinde ve `figures/` dizininde PNG olarak bulunur.
5. **Çıktılar:** `reports/` altındaki CSV dosyaları ve `reports/eda_summary.md` her çalıştırmada
   yeniden yazılır. Çıktılar deterministiktir (iki ardışık çalıştırma bayt düzeyinde aynı dosyaları üretir).
6. **Testler:**

```bash
python -m pytest -q
```

Django/DRF kurulu değilse analiz yine çalışır; yalnızca "Django URL çözümlemesi" katmanı (view
türü ve desteklenen metotlar) atlanır ve bu durum raporda belirtilir. Bu durumda
`tests/test_real_dataset.py` içindeki yeniden üretim testleri, depodaki (Django ile üretilmiş)
raporlarla farklılık bildirebilir.

## Google Colab

> **Doğrulama durumu:** Notebook yerel Jupyter'de ve temiz bir Python ortamında baştan sona
> doğrulanmıştır. Gerçek bir Google Colab çalışma zamanında henüz çalıştırılmamıştır; Colab
> desteği isteğe bağlı bir kolaylıktır.

1. Colab'da **Dosya → Not defterini aç → GitHub** sekmesine depo adresini girin ve
   `experiments/h3_02_eda/H3_02_EDA_Veri_Kalitesi.ipynb` dosyasını seçin
   (PR birleşmeden önce dal olarak `feat/h3-02-eda-data-quality` seçin). Doğrudan bağlantı:
   `https://colab.research.google.com/github/reyyannerva/Yapay-Zeka-Ajaniyla-Django-Test-Uretimi-ve-Guvenlik-Analizi/blob/main/experiments/h3_02_eda/H3_02_EDA_Veri_Kalitesi.ipynb`
   (birleşmeden önce `main` yerine `feat/h3-02-eda-data-quality`). Her denemede yeni bir çalışma
   zamanı kullanın; önceki bir klon `/content/` altında varsa yeniden kullanılır.
2. PR birleşmeden önce çalıştırıyorsanız ilk kod hücresinden önce yeni bir hücrede:
   ```python
   import os; os.environ["H302_REPO_REF"] = "feat/h3-02-eda-data-quality"
   ```
3. **Çalışma zamanı → Tümünü çalıştır.** İlk hücre, depo bulunamadığında herkese açık depoyu
   `git clone --depth 1` ile `/content/` altına indirir ve `requirements.txt` dosyasını kurar.
   GPU, ücretli servis, LLM API anahtarı veya kimlik bilgisi gerekmez.
4. **Depo özelse:** kimlik bilgisi/token'ı notebook'a **yazmayın**. Depoyu ZIP olarak indirip
   Colab'a yükleyin, `/content/` altına açın ve bir hücrede
   `os.environ["H302_REPO_ROOT"] = "/content/<açılan-dizin>"` ayarlayın.
5. **Doğrulama kanıtı:** ilk hücre analiz edilen git dalını ve commit'i yazdırır; dışa aktarımdan
   sonraki karşılaştırma hücresi yeniden üretilen raporların depodaki sürümle aynı olup olmadığını
   bildirir (PNG farkları matplotlib/font sürümüne bağlı olabilir).
6. **Raporları indirme:** "Yalnızca Google Colab" başlıklı hücre yalnızca `reports/` ve `figures/`
   içeriğini `h3_02_eda_ciktilari.zip` olarak indirir.

## Yöntem özeti

| Katman | Ne yapar | Kanıt türü |
|---|---|---|
| JSON Schema | Kanonik şema (Draft 2020-12) ile yapısal doğrulama; H3-01 `validate_scenarios.py` ile karşılaştırılır | Statik |
| Semantik | Eksik/null zorunlu alan, boş metin, geçersiz metot/kategori/rol/durum kodu, kimlik biçimi, yinelenen kimlik/içerik, etiket–durum kodu–hata işareti tutarlılığı | Statik |
| Referans bütünlüğü | `fixture_ref.user/article` ↔ fixture dosyaları, endpoint ↔ `urls.py` desenleri, endpoint pk ↔ `fixture_ref.article`, rol etiketi ↔ `is_staff`/`owner`, güvensiz uç ↔ `is_intentional_flaw` | Statik |
| Django URL çözümlemesi | `django.urls.resolve` ile view sınıfı ve desteklenen metotlar; 405 beklentisinin doğrulanması | Statik (HTTP isteği yok) |
| Durum kodu incelemesi | Hedef uygulama yapılandırmasına dayanan sezgisel kurallar; yalnızca "inceleme" üretir | Sezgisel |
| JSON ↔ CSV | CSV, export betiğinin dönüşümüyle JSON'dan yeniden türetilip hücre hücre karşılaştırılır | Statik |
| Kapsam modeli | Alan modeline göre açıkça listelenmiş (endpoint türü × metot × koşul) hücreleri; Açıkça mevcut / Dolaylı / Kapsanmıyor / Uygulanamaz | Statik |

**Davranışsal (çalışma zamanı) doğrulama** bu paketin kapsamında değildir: her senaryonun gerçek
uygulama davranışıyla eşleştiği H3-01'in `pytest` paketiyle (67 test) doğrulanır.

Önemli yorum kuralları:

- `user_role` etiketi, fixture kimliği (admin/alice/bob/carol) ve aktör–kaynak ilişkisi ayrı
  boyutlardır; sahiplik kullanıcı adından değil `articles.json` `owner` alanından türetilir.
- `negative` etiketi bozuk veri anlamına gelmez: beklenen ret (4xx) veya bilerek güvensiz uçta
  gözlemlenen hatalı davranışı ifade eder.
- Bilerek-hatalı senaryolar veri hatası değildir; ayrı tabloda güvenli karşılıklarıyla raporlanır.
- Kapsanmayan hücre bir kapsam boşluğudur, doğrulanmış güvenlik açığı değildir.
- "Düşük temsil" eşiği (%10) ve öncelikler proje-özgü, yapılandırılabilir sezgisel değerlerdir.

## Çıktılar

| Dosya | İçerik |
|---|---|
| `reports/eda_summary.md` | Akademik özet: genel bakış, yöntem, istatistikler, kapsam, kalite, yetkilendirme, kaynak ayrımı, öneriler, sınırlılıklar, yeniden üretim |
| `reports/general_statistics.csv` | Toplam/benzersiz kimlik, sınıf oranları, temsil edilen değer sayıları |
| `reports/method_distribution.csv` | Beş HTTP metodu (sıfır dâhil), yüzde, sınıf kırılımı, temsil durumu |
| `reports/class_distribution.csv` | Pozitif/negatif ve türetilmiş beklenti sınıfı |
| `reports/category_distribution.csv` | Şemadaki tüm kategoriler |
| `reports/role_distribution.csv` | Rol etiketi, fixture kimliği, aktör–kaynak ilişkisi |
| `reports/status_code_distribution.csv` | Şemadaki tüm durum kodları |
| `reports/endpoint_distribution.csv` | Rota deseni, view, view türü, metotlar |
| `reports/cross_tabulations.csv` | Metot × kategori/rol/durum kodu/… çapraz tabloları (uzun biçim) |
| `reports/coverage_matrix.csv` | Kapsam modeli hücreleri, durum ve senaryo kimlikleri |
| `reports/authorization_coverage.csv` | PUT/PATCH/DELETE yetkilendirme matrisi |
| `reports/coverage_gaps.csv` | Doğrulanmış/olası eksik ve yetersiz meta veri kayıtları, öneriler |
| `reports/data_quality_findings.csv` | Kayıt düzeyi bulgular (boşsa yalnızca başlıklar) |
| `reports/data_quality_checks.csv` | Çalıştırılan kontrol envanteri ve bulgu sayıları |
| `reports/intentional_flaws.csv` | Bilerek-hatalı senaryolar ve güvenli karşılıkları |
| `reports/source_comparison.csv` | Kontrollü fixture vs PyGoat kaynak tablosu |
| `figures/01…10_*.png` | Metot, sınıf, kategori, rol, durum kodu dağılımları; metot × kategori/rol ısı haritaları; yetkilendirme matrisi; kalite bulguları; kapsam modeli durumu |

Kaynak karşılaştırma grafiği yalnızca depoda PyGoat senaryo kaydı bulunduğunda üretilir; mevcut
durumda kayıt olmadığından üretilmez ve bu durum raporda açıklanır.

## Issue #28 izlenebilirlik matrisi

| # | Issue maddesi | Notebook bölümü / dosya | Fonksiyon | Çıktı / kanıt | Doğrulama |
|---|---|---|---|---|---|
| Y1 | JSON/CSV'yi Jupyter'de okumak; kütüphaneleri yapılandırmak | §2–3 | `find_repo_root`, `load_context` | Sürüm tablosu, yükleme özeti | Notebook baştan sona çalıştı |
| Y2 | Toplam senaryo, benzersiz kimlik, kategori dağılımı | §5, §7 | `general_statistics`, `category_distribution` | `general_statistics.csv`, `category_distribution.csv`, şekil 03 | `test_statistics_match_raw_json` |
| Y3 | Pozitif/negatif sayı ve oranları; dengesizlik | §5, §11 | `label_distribution`, `expectation_distribution` | `class_distribution.csv`, şekil 02 | `test_statistics_match_raw_json` |
| Y4 | GET/POST/PUT/PATCH/DELETE dağılımı; eksik/yetersiz metot | §6 | `method_distribution` | `method_distribution.csv`, şekil 01, 06, 07 | `test_all_five_methods_assessed`, `test_method_distribution_reports_all_five_methods_even_if_absent` |
| Y5 | Endpoint türü, rol ve kimlik doğrulama/yetkilendirme/girdi doğrulama dağılımı | §7–8 | `endpoint_distribution`, `role_distribution`, `standard_crosstabs` | `endpoint_distribution.csv`, `role_distribution.csv`, `cross_tabulations.csv`, şekil 04 | `test_actor_relation_uses_fixture_ownership` |
| Y6 | PUT/PATCH/DELETE yetkili-yetkisiz, sahiplik, silme | §9 | `coverage_matrix`, `authorization_coverage` | `authorization_coverage.csv`, şekil 08 | `test_missing_coverage_combination_is_reported` |
| Y7 | Durum kodu dağılımı; metot/rol/tür ile tutarsız kayıtlar | §10 | `status_distribution`, `check_method_support`, `check_status_plausibility` | `status_code_distribution.csv`, şekil 05 | `test_method_support_vs_405`, `test_status_plausibility_is_review_only` |
| Y8 | Eksik alan, yinelenen kimlik, geçersiz metot, tutarsız kategori/rol, eksik fixture referansı | §4, §13–14 | `check_json_schema`, `check_record_fields`, `check_duplicate_ids`, `check_fixture_references`, `check_csv_consistency` | `data_quality_findings.csv`, `data_quality_checks.csv`, şekil 09 | `tests/test_quality_checks.py` (26 test), `tests/test_notebook.py` |
| Y9 | PyGoat ve kontrollü fixture ayrı gruplar | §15 | `pygoat_inventory`, `source_comparison` | `source_comparison.csv` | `test_pygoat_separation`, `test_pygoat_inventory_counts_only_real_records` |
| Y10 | Kalite sorunları ve kapsam eksikleri sonuç bölümü, senaryo kimlikleriyle | §16, §18 | `coverage_gaps`, `render_summary` | `coverage_gaps.csv`, `eda_summary.md`, şekil 10 | `test_findings_reference_real_ids` |
| Y11 | Veri dosyalarından yeniden çalıştırılabilir; bağımlılıklar, çıktılar, talimatlar repoda | Bu README, `requirements.txt` | `export_reports`, `render_all` | `reports/`, `figures/` | `test_committed_reports_are_reproducible`, `test_committed_summary_is_reproducible` |
