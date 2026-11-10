# Kural Tabanlı Pytest Üretim Baseline'ı (H3-04 / Issue #30)

Django/DRF endpoint özeti ve bağımsız referans gereksinimlerinden, **LLM kullanmadan**, çalıştırılabilir
Pytest testleri üreten deterministik baseline. Ağ erişimi, harici servis veya API anahtarı gerektirmez.

Çalıştırma talimatları, örnek çıktılar ve kabul kriteri izlenebilirliği:
[`experiments/h3_04_rule_based_baseline/README.md`](../../../experiments/h3_04_rule_based_baseline/README.md).

## Mimari

```
loaders.py      Girdileri okur ve JSON Schema ile doğrular (endpoint özeti, ground truth, senaryolar, fixture'lar)
planner.py      Kural katmanı: endpoint eşleme, route parametresi, rol/sahiplik, beklenen durum, yan etki kuralı
codegen.py      AST tabanlı kaynak kod üretimi (metin birleştirme yok), conftest.py ve pytest.ini üretimi
validation.py   ast.parse + compile, dosya adı, yinelenen test adı, senaryo↔test izlenebilirliği, içe aktarımlar
generator.py    Akış: planla → üret → doğrula → yaz (eski üretilmiş dosyaları temizler)
runner.py       pytest --collect-only, JUnit XML ile çalıştırma, sonuç sınıflandırma, yalıtım kontrolü
reporting.py    Deterministik JSON + Markdown raporları
examples.py     Desteklenmeyen/geçersiz girdi örneklerinin çalıştırılması
runtime_support.py  Üretilen testlerin kullandığı yardımcılar (h304_support.py olarak kopyalanır)
contracts.py    Veri yapıları, durumlar (Status) ve tanı kodları (Code)
schemas/endpoint_summary.schema.json  Endpoint giriş sözleşmesi
```

## Girdi sözleşmeleri

| Girdi | Kaynak | Üreticide kullanımı |
|---|---|---|
| Endpoint özeti | `schemas/endpoint_summary.schema.json` | Yol şablonu (`/api/articles/{pk}/`), `url_name`, route parametreleri, view türü, metot → işlem (`list`, `retrieve`, `create`, `update`, `partial_update`, `destroy`, `custom_action`), kimlik doğrulama gereksinimi, nesne izni, kaynak modeli ve sahip alanı, yazılabilir alanlar, kaynak bilgisi (`source.kind`, `ast_integration`) |
| Bağımsız referans | `benchmarks/reference_cases/ground_truth.json` (H3-03) | **Beklenen durum kodu** (`expected_result.secure_status`), beklenen davranış, rol, metot, bilinen kusur ve `security_finding` |
| Senaryo istek verisi | `benchmarks/drf_fixtures/scenarios/scenarios.json` (H3-01) | Somut endpoint, örnek girdi (`request_input`), fixture kullanıcısı ve kaynağı, kategori |
| Fixture kayıtları | `users.json`, `articles.json` | Rol doğrulaması (`is_staff`) ve sahiplik (`owner`) |

Ground truth ve senaryo verisi `scenario_id` ile birleştirilir. Metot veya rol iki kaynakta farklıysa
senaryo üretilmez (`REFERENCE_CONFLICT`). **Beklenen sonuç asla senaryodaki `expected_http_status`
alanından alınmaz**: bilerek-hatalı senaryolarda bu alan güvensiz uçta gözlenen hatalı davranıştır.

## Üretim kuralları

- Beklenen durum kodu yalnızca referanstan alınır; rol veya metoda göre 401/403 varsayımı yapılmaz.
- URL'ler `django.urls.reverse(url_name, kwargs=...)` ile çözülür; sonuç senaryodaki somut yolla
  karşılaştırılır (`check=route`).
- Kimlik doğrulama: DRF `APIClient.force_authenticate`. Rol etiketi fixture'daki `is_staff` ve kaynağın
  sahip alanıyla doğrulanır; sahipliği doğrulanamayan `owner` senaryoları uyarıyla üretilir.
- Yan etki kontrolleri HTTP semantiğinden türetilir (uygulama kodundan değil):

| Kural | Ne zaman | Doğrulama |
|---|---|---|
| `count_plus_one` / `count_unchanged` | `create` başarılı / ret; desteklenmeyen metot (nesnesiz) | Kayıt sayısı +1 / değişmez |
| `update_applied` | `update` (PUT) 2xx | Gövdedeki yazılabilir alanlar kaydedildi |
| `partial_update_applied` | `partial_update` (PATCH) 2xx | Gövdedeki alanlar güncellendi **ve gövdede olmayan alanlar korundu** |
| `resource_unchanged` | Mevcut kaynakta PUT/PATCH/DELETE reddi; desteklenmeyen metot | Kaynak değişmedi |
| `resource_deleted` | `destroy` 2xx | Kaynak artık yok |
| `resource_still_absent` | Mevcut olmayan kaynak | Kaynak oluşmadı |
| `none` | `list`, `retrieve`, `custom_action` | Yalnızca durum kodu |

- Her test kendi transaction'ında çalışır (pytest-django); fixture'lar her test için yeniden yüklenir.
- Kaynak kod AST düğümleriyle kurulur; veri değerleri `ast.Constant` olarak yerleştirilir. Aynı girdi
  her zaman bayt düzeyinde aynı çıktıyı verir (girdi sırasından bağımsız).

## Senaryo durumları ve tanı kodları

| Durum | Anlam |
|---|---|
| `GENERATED` | Test üretildi (uyarılar varsa raporda listelenir) |
| `UNSUPPORTED` | Geçerli fakat baseline kapsamı dışında (ör. `HEAD`, DRF dışı view, desteklenmeyen kimlik doğrulama, `supported: false` endpoint) |
| `INVALID_INPUT` | Girdi hatalı veya çelişkili (geçersiz metot/durum kodu, çözümlenemeyen/belirsiz rota, eksik route parametresi, eksik fixture kullanıcısı, rol–fixture çelişkisi, geçersiz gövde, şema ihlali) |
| `MISSING_REFERENCE` | Bağımsız referans veya senaryo istek verisi yok; beklenen sonuç uydurulmaz |
| `GENERATION_ERROR` | Üretilen kod statik doğrulamadan geçmedi (sözdizimi, yinelenen test adı, izlenebilirlik) |

Tanı kodlarının tamamı `contracts.Code` içindedir.

## Çalıştırma sonucu sınıfları

Pytest sonucu (passed/failed/error) olduğu gibi korunur; sınıflandırma ayrı bir alandır.

| Sınıf | Anlam |
|---|---|
| `PASSED` | Güvenli beklenti karşılandı |
| `KNOWN_FLAW_DETECTED` | Test **başarısız**; gözlenen kod ground truth'taki `observed_flawed_status` ile aynı (bilinen kusur tespit edildi) |
| `KNOWN_FLAW_NOT_DETECTED` | Test geçti, ancak senaryo bilinen bir kusur (ör. içerik düzeyi sapma) |
| `APPLICATION_MISMATCH` | Test doğru çalıştı; uygulama davranışı referanstan farklı |
| `GENERATION_ERROR` | Üretici kaynaklı teknik hata (yanlış URL, içe aktarma, fixture, beklenmeyen istisna, toplanamayan test) |
| `ENVIRONMENT_ERROR` | Hedef uygulama/ortam yüklenemedi (ön kontrol: `django.setup()` + `ROOT_URLCONF` içe aktarımı); üreticiye yüklenmez |

## Üretilen testlerin hata yakalama kanıtı

`tests/test_execution.py::test_generated_suite_detects_injected_faults`, hedef uygulamanın **geçici bir
kopyasına** hata enjekte eder (depodaki uygulama değişmez) ve aynı üretilmiş paketin bunu yakaladığını doğrular:

| Enjekte edilen hata | Yakalayan senaryolar |
|---|---|
| Nesne düzeyi yetkilendirme kaldırıldı (`has_object_permission` → `True`) | SC-AUZ-001, SC-AUZ-002, SC-AUZ-003 |
| Başlık zorunluluğu ve boş başlık kontrolü kaldırıldı | SC-INP-001, SC-INP-002 |
| PATCH gövdede olmayan alanı siliyor | SC-UPD-003, SC-UPD-004 (yalnızca kısmi güncelleme yan etki kontrolüyle) |

Not: yalnızca `validate_title`'ı devre dışı bırakmak eşdeğer bir mutasyondur; DRF `CharField` boşlukları
kırpıp boş değeri zaten reddettiği için davranış değişmez ve hiçbir testin başarısız olmaması doğrudur.

## Testler

```bash
cd agent/test_generation/rule_based
python -m pytest -q
```

## Bilinen kısıtlar

- AST endpoint çıkarımı henüz yoktur; endpoint özeti kontrollü fixture kaynak kodundan elle hazırlanmıştır
  (`source.ast_integration: false`). Format, AST çıktısının üreteceği sözleşme olarak tasarlanmıştır.
- İçerik düzeyi güvenlik beklentileri (ör. "taslaklar gizlenmeli") ground truth'ta makine-okunur değildir;
  bu senaryolarda yalnızca durum kodu doğrulanır ve `CONTENT_ASSERTION_UNSUPPORTED` uyarısı verilir.
- `custom_action` işlemlerinin yan etkisi bilinmediğinden yalnızca durum kodu doğrulanır.
- Desteklenen metotlar GET, POST, PUT, PATCH, DELETE; desteklenen kimlik doğrulama BasicAuthentication,
  SessionAuthentication, TokenAuthentication (testte `force_authenticate`).
