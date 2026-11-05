# ER Diyagramı İnceleme Belgesi — Revizyon 3 (Mockup Uyumu)

| Bilgi | Değer |
|---|---|
| Proje | Yapay Zekâ Ajanıyla Django Test Üretimi ve Güvenlik Analizi (TestKalkan) |
| İş kalemleri | H2-02 / #24 (şema), H2-04 / #26 (ER diyagramı) |
| Revizyonun kaynağı | Figma mockup açıklaması `docs/mockup/README.md`, özellikle "Kapsam notları" |
| Teslim dosyaları | `database_schema.sql`, `django_models.py`, `data_dictionary.md`, `schema_validation.md`, `er_diagram_full.svg/.png`, `er_diagram_presentation.svg/.png`, `er_diagram_source.mmd`, bu belge |

## 1. Özet

| | Revizyon 1 | Revizyon 2 |
|---|---|---|
| Uygulama tablosu | 6 | 9 (`endpoints`, `reports`, `llm_calls` eklendi) |
| Uygulama sütunu | 76 | 122 |
| İlişki (FK) | 6 | 13 (9 zorunlu, 4 isteğe bağlı) |
| JSONB sütunu | 9 | 11 |
| Adlandırılmış tekil/CHECK kısıtı ve açık indeks | 51 | 85 |
| Çerçeve tarafından yönetilen kutu | auth_user | auth_user, django-axes (4 tablo) |
| AnalysisRun durumu | 6 | 9 |

Tablo başına sütun: projects 12, reference_requirements 13, analysis_runs 18, endpoints 10, generated_tests 18, test_executions 14, security_findings 17, reports 8, llm_calls 12.

## 2. Diyagram gösterimi

- Zorunlu FK'li ilişkide üst uç "tam bir" (‖), isteğe bağlı FK'li ilişkide (R6, R9, R10, R13) "sıfır veya bir" (çizgi karta yakın, çember dışta). Alt uç her ilişkide "sıfır veya çok".
- django-axes tabloları tek bir kesik çerçeveli kutuda listelenir; FK'leri olmadığı için çizgi bağlanmaz.
- AnalysisRun → LlmCall (R12) çizgisi GeneratedTest sütununun üstünden dolaşır; böylece hiçbir çizgi kart veya başka çizgi kesmez.
- Sunum görünümünde her kartta PK, tüm FK'ler ve birkaç önemli sütun vardır; tekil kısıt işaretleri yalnızca tam diyagramdadır.

## 3. Değişiklikler ve mockup karşılıkları

### 3.1 İstenen değişiklikler

| No | Değişiklik | Mockup ekranı / kararı |
|---|---|---|
| 1.1 | `analysis_runs.status` 9 değer: QUEUED, ANALYZING, GENERATING, VALIDATING, EXECUTING, SCANNING, COMPLETED, FAILED, CANCELLED | 16 (aşama şeridi), README "Diyagramlarla tutarlılık", 28–29 |
| 1.2 | Tek aktif analiz indeksi aktif kümesi: QUEUED … SCANNING (6 değer) | 16, 28 |
| 1.3 | Eklendi: `method`, `llm_provider`, `llm_model`, `fallback_enabled`, `coverage_percent` | 05 (yöntem, model, fallback), 24 (Groq/Gemini/Ollama), 08 (kod kapsamı) |
| 1.4 | `error_code` değerleri sözlük 8.6'da listelendi | 17 (hata ayrıntısı) |
| 1.5 | `retry_count` kaldırıldı | README: sandbox başlamazsa analiz FAILED olur; otomatik yeniden deneme yok (17) |
| 1.6 | CANCELLED'da `finished_at` zorunlu; tamamlanan sonuçlar ve bulgular saklanır | README "Analiz durdurma"; 28, 29 |
| 2 | Yeni `endpoints` tablosu; HEAD/OPTIONS kapsam dışı; `is_supported = false` ise neden zorunlu; (run, path, method) tekil | 06; README "HTTP metotları", İST-16 |
| 3 | `generated_tests`: `endpoint_id`, `role`, `expected_status`, `is_security_test`, `repair_count` (0–1); `generation_method` LLM, RULE_BASED | 07, 08; README tek düzeltme kuralı |
| 4 | `test_executions`: 7 durum; `observed_status`, `error_type`, `error_origin`; TECHNICAL_ERROR'da hata türü zorunlu; düzeltme kuralı sözlük 9.3'te | 08 (PASS/FAIL/teknik hata, beklenen–gözlenen), 16, 29 |
| 5 | `security_findings`: kaynak AUTH_TEST, BANDIT, CHECK_DEPLOY; sınıf VERIFIED, POSSIBLE, UNCERTAIN; önem HIGH, MEDIUM, LOW, UNKNOWN; `test_execution_id`, `endpoint_id`, `recommendation_key` | 09 (doğrulanmış/olası/belirsiz, kanıt, düzeltme önerisi) |
| 6 | Yeni `reports` tablosu: PDF/JSON, FULL/PARTIAL, seçili bölümler, göreli dosya yolu, boyut | 10, 21, 25 |
| 7 | Yeni `llm_calls` tablosu: sağlayıcı, model, amaç, token, gecikme, durum | İST-13; 02 (token kullanımı), 07 (fallback bildirimi), 24 (erişilebilirlik/kota) |
| 8.1 | `source_repository_url` kaldırıldı; `source_directory` (NULL olabilir) eklendi; `source_type` ARCHIVE, ALLOWED_DIRECTORY | 03 (arşiv veya izinli dizin) |
| 8.2 | Üyelik/paylaşım tablosu yok; proje silindiğinde tüm kayıtlar ORM ile, rapor dosyaları uygulama tarafından silinir | 30; README "Yetkilendirme" |
| 9 | `reference_requirements.category` ROLE, ACCESS_RULE, DEPLOY_EXPECTATION; `source` FORM, JSON_UPLOAD; ACCESS_RULE `specification` örneği sözlük 10.2'de | 04, 23, 31 |
| 10 | django-axes tabloları kesik çerçeveli "Çerçeve tarafından yönetilir" kutusunda; şifre sıfırlama tablosuz | 11 (kalan deneme hakkı), 26 |
| — | Veri sözlüğüne büyük/küçük harf notu (K3, bölüm 4 girişi, bölüm 8) | 16 (durum rozetleri küçük harfle) |
| — | Diyagram başlıklarındaki sayılar güncellendi | — |

### 3.2 İstenenin dışında yapılan ve onayınıza sunulan kararlar

| Karar | Gerekçe |
|---|---|
| Yeni isteğe bağlı FK'ler `on_delete=SET_NULL`; bağlanan kaydın aynı analize ait olması uygulama kuralı (sözlük 6.4) | Tek bir endpoint veya test silindiğinde bağlı kayıtlar kaybolmasın; Django bileşik FK desteklemez. |
| `RULE_BASED` ise `llm_provider` ve `llm_model` NULL, diğer yöntemlerde ikisi de dolu (iki yönlü CHECK) | İstenen "RULE_BASED ise NULL" kuralının tersi de anlamlı; model seçilmeyen LLM analizi oluşamaz. |
| `fallback_enabled` = model erişilemezse kural tabanlı üretime geçiş | Ekran 05 ve 07; testin kökeni `generation_method = RULE_BASED` olur. Varsayılan revizyon 3'te `true` yapıldı (3.3). |
| ROLE satırında `expected_result` boş olabilir | Rol satırının beklenen sonucu yoktur; diğer kategorilerde boş olamaz. |
| `error_code` listesine `ARCHIVE_INVALID`, `LLM_UNAVAILABLE`, `WORKER_LOST` eklendi | İlk ve sonuncusu revizyon 1 belgelerinde vardı; `LLM_UNAVAILABLE` fallback kapalıyken model erişilemezse gerekir. Liste CHECK ile sınırlandırılmadı. |
| Yeni CHECK'ler: HTTP kodları 100–599, `coverage_percent` 0–100, token/gecikme/dosya boyutu ≥ 0, başarılı çağrıda token zorunlu, boş olmayan yol/model adı | Diğer tablolardaki kısıt düzeyiyle aynı. |
| `auth_type`, `recommendation_key`, `sections` değerleri CHECK ile sınırlandırılmadı | README bu kümeleri tanımlamıyor; değer uydurulmadı. |
| `processing_metadata` ve `generation_metadata` örneklerinden model/token bilgisi çıkarıldı | Bu bilgiler artık sütunlarda ve `llm_calls` tablosunda. |
| Sözlük 13.1: başka kullanıcının kaydına erişim 404 yerine 403 | Ekran 13 ve README "Yetkilendirme". |
| İsteğe bağlı FK'ler için adlandırılmış indeksler (`ix_gentest_endpoint`, `ix_finding_execution`, `ix_finding_endpoint`, `ix_llmcall_generated_test`) ve `ix_report_run_created`, `ix_llmcall_run_created` | Revizyon 1'deki adlandırılmış indeks yaklaşımıyla aynı; Django'nun karma adlı otomatik indeksleri yerine. |

### 3.3 Revizyon 3

| Değişiklik | Mockup ekranı / kararı |
|---|---|
| `analysis_runs.fallback_enabled` varsayılanı `true` (SQL `DEFAULT true`, ORM `default=True`) | 05: "Model erişilemezse kural tabanlı yönteme geç" anahtarı varsayılan olarak açık |
| `projects.source_archive` ve `projects.archive_sha256` `NULL` olabilir (`DEFAULT ''` kaldırıldı) | 03: proje ya arşivden ya izinli dizinden alınır |
| `ck_projects_archive_source_present`: `ARCHIVE` ise `source_archive` (boş olmayan) ve `archive_sha256` dolu, `source_directory` `NULL` | 03 |
| `ck_projects_directory_source_present`: `ALLOWED_DIRECTORY` ise `source_directory` dolu, `source_archive` ve `archive_sha256` `NULL` | 03 |
| `ck_projects_source_archive_relative` ve `ck_projects_archive_sha256_format` `NULL`'a izin verecek biçimde güncellendi; boş metin özet artık reddedilir | Tek bir "değer yok" temsili (K6) |

Sütun sayısı (122), ilişkiler (13) ve adlandırılmış kısıt/indeks sayısı (85) değişmedi. İstekte geçen `'DIRECTORY'` değeri şemadaki `ALLOWED_DIRECTORY` olarak uygulandı; kaynak türü değerleri değiştirilmedi.

### 3.4 `test_executions.status` ve mockup sonuç kategorileri

| Mockup kategorisi (ekran 08) | Kayıt |
|---|---|
| PASS | `status = 'PASS'` |
| FAIL | `status = 'FAIL'` (beklenen ≠ gözlenen HTTP kodu) |
| Teknik hata: test kodu hatası | `status = 'TECHNICAL_ERROR'`, `error_type` ∈ {IMPORT, FIXTURE, SYNTAX}, `error_origin = 'TEST_CODE'`; bir kez düzeltilir |
| Teknik hata: ortam hatası | `status = 'TECHNICAL_ERROR'`, `error_origin = 'INFRASTRUCTURE'` (`error_type` çoğunlukla OTHER) |
| Teknik hata: TIMEOUT | `status = 'TECHNICAL_ERROR'`, `error_type = 'TIMEOUT'`; düzeltilmez |
| Teknik hata: OOM | `status = 'TECHNICAL_ERROR'`, `error_type = 'OOM'`; düzeltilmez |

Durumun 7 değeri: QUEUED, RUNNING, PASS, FAIL, TECHNICAL_ERROR, STOPPED, NOT_RUN. Teknik hata türleri ayrı durum değerleri değil, `TECHNICAL_ERROR` + `error_type` / `error_origin` birleşimidir. Her satır senaryo testleriyle doğrulandı (T03, T17–T23); `TECHNICAL_ERROR`'da `error_type` olmadan kayıt reddedilir (T06).

## 4. PostgreSQL ve Django ORM notları

- FK'ler `DEFERRABLE INITIALLY DEFERRED`, `ON DELETE` eylemi yok. `CASCADE` ve `SET_NULL` ORM tarafından uygulanır; ham SQL ile alt kaydı veya başvurusu olan üst kayıt silinemez (senaryo X01, X03).
- `coverage_percent` → `DecimalField(5, 2)`, HTTP kodları ve `repair_count` → `SmallIntegerField`, `file_size_bytes` → `BigIntegerField`.
- django-axes tablo seti django-axes 9.0.0 kaynak kodundan alınmıştır; 8.1'den eski sürümlerde `axes_accessattemptexpiration` yoktur.

## 5. Bilinen sınırlamalar

1. Django kurulamadığı için `manage.py check`, `makemigrations` ve `sqlmigrate` çalıştırılmadı; adımlar `schema_validation.md` H'de.
2. "Aynı analiz çalıştırması" kuralı (R6, R9, R10, R13) ve rapor kapsamı kuralı veritabanında zorlanamaz; uygulama katmanında uygulanmalıdır.
3. Mermaid bileşik ve kısmi tekil kısıtları ifade edemez; bunlar öznitelik yorumu olarak yazıldı. django-axes tabloları Mermaid'de yalnızca yorum satırı olarak yer alır, çünkü sütun tipleri django-axes sürümüne ve `DEFAULT_AUTO_FIELD` ayarına bağlıdır.
4. Figma, PowerPoint ve GitHub SVG önizlemesi bu ortamda denenmedi.

## 6. Gerçekleştirilen doğrulamalar

| Kontrol | Sonuç |
|---|---|
| DDL'in PostgreSQL 16.15'te çalıştırılması | Hatasız; 9 tablo, 26 indeks |
| SQL kataloğu ↔ SQL metni ↔ ORM ↔ veri sözlüğü | 122/122 sütunda ad, sıra, tip, NULL ve uzunluk aynı; 13 FK'de hedef, NULL ve `on_delete` beklenenle aynı; 85 adlandırılmış kısıt/indeks SQL ve ORM'de aynı adla |
| Kısıt davranış senaryoları | 132/132 beklendiği gibi (53 kabul, 79 red; red senaryolarında beklenen kısıt adı doğrulandı) |
| `django_models.py` sözdizimi | `py_compile` başarılı |
| Tam diyagram SVG otomatik kontrolü | 224/224 |
| Sunum diyagramı SVG otomatik kontrolü | 195/195 |
| Doğrulayıcının kendisi | Bilerek bozulan kopyalarda (üst uç türü, sütun tipi, uydurma sütun, kart çakışması) hatalar yakalandı |
| Görsel inceleme | Her iki PNG ve yakın plan kesitler gözle incelendi; tam diyagramda taşan gösterim satırı kısaltıldı |
| PNG ↔ SVG, rsvg ↔ Chrome | PNG'ler SVG'nin tam 2 katı; Chrome ile ortalama piksel farkı 1,07/255 (tam) ve 0,61/255 (sunum) |
| Mermaid | mermaid-cli 11.16.0 ile hatasız render; öznitelikler, anahtarlar, NULL yorumları ve 13 ilişkinin isteğe bağlılığı matrisle aynı |
| Markdown tabloları | İki belgede sütun sayısı hatalı satır yok |
