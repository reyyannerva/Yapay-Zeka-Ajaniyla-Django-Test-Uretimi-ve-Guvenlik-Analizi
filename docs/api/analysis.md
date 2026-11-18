# Analiz İşlemleri (AnalysisRun)

Tüm işlemler JWT ister ve yalnızca kullanıcının kendi projelerine ait analizleri kapsar.

| Yöntem | Yol | Açıklama |
|---|---|---|
| POST | `/api/analysis-runs/` | Analiz kaydı oluştur (**201**, `AnalysisRunDetail`) |
| GET | `/api/analysis-runs/` | Analizlerimi listele (**sayfasız** dizi, `AnalysisRunList`) |
| GET | `/api/analysis-runs/{id}/` | Detay + ilerleme (`AnalysisRunDetail`) |

Güncelleme ve silme işlemleri yoktur (**405**).

> **Önemli:** Bu sürümde analiz oluşturmak **arka plan görevi (Celery) başlatmaz**. Kayıt `QUEUED`
> durumunda oluşturulur; `celery_task_id`, `started_at`, `finished_at` `null` kalır. Analiz iş akışının
> yürütülmesi sonraki iş kalemlerinin konusudur.

## 1. Oluşturma

| Alan | Zorunlu | Değerler |
|---|---|---|
| `project` | evet | Sahip olunan proje kimliği |
| `method` | evet | `RULE_BASED`, `DIRECT_LLM`, `HYBRID` |
| `llm_provider` | `DIRECT_LLM`/`HYBRID` için evet | `GROQ`, `GEMINI`, `OLLAMA` |
| `llm_model` | `DIRECT_LLM`/`HYBRID` için evet | metin |
| `fallback_enabled` | hayır | boolean |

`RULE_BASED` ile LLM alanı gönderilmesi 400'dür. Diğer 400 durumları: geçersiz `method`
(`{"method": ["\"MAGIC\" geçerli bir seçim değil."]}`), başkasına ait veya olmayan proje
(`{"project": ["Geçersiz pk \"99999\" - obje bulunamadı."]}`).

Projede zaten aktif bir analiz varsa da 400 döner. **Bilinen kusur (H4-04):** bu durumda gerçek yanıt
`{"non_field_errors": ["project  alanları benzersiz bir set yapmak gerekir."]}` biçimindedir; DRF'nin koşullu
benzersizlik kısıtından otomatik ürettiği doğrulayıcı özel mesajı gölgelemektedir. Şema, uygulamanın
**gerçek** yanıtını belgeler; düzeltme H4-04 sahibine raporlanmıştır.

Oluşturma anında projenin aktif referans gereksinimleri `requirements_snapshot` alanına kopyalanır; sonraki
gereksinim değişiklikleri mevcut analizi etkilemez.

## 2. Durumlar (`AnalysisRunStatusEnum`, 9 değer)

| Durum | Anlam | Sınıf |
|---|---|---|
| `QUEUED` | Kuyrukta | aktif |
| `ANALYZING` | Analiz ediliyor | aktif |
| `GENERATING` | Test üretiliyor | aktif |
| `VALIDATING` | Testler doğrulanıyor | aktif |
| `EXECUTING` | Testler çalıştırılıyor | aktif |
| `SCANNING` | Güvenlik taraması | aktif |
| `COMPLETED` | Tamamlandı | son |
| `FAILED` | Başarısız | son |
| `CANCELLED` | İptal edildi | son |

Birincil iş akışı `QUEUED → ANALYZING → GENERATING → EXECUTING → COMPLETED / FAILED`'dir; `VALIDATING`,
`SCANNING` ve `CANCELLED` modelde desteklenen ek durumlardır. Bu API sürümünde durum geçişlerini yapan bir
uç nokta yoktur.

## 3. İlerleme (`progress`, yalnızca detay/oluşturma yanıtında)

`TestExecution` kayıtlarından her istekte türetilir (saklanmaz):

| Alan | Anlam |
|---|---|
| `total` | Yürütme kaydı olan test sayısı |
| `completed` / `running` / `pending` | Son denemesi sonuçlanmış / RUNNING / PENDING testler |
| `by_status` | Son deneme durumlarına göre sayaçlar |
| `completed_duration_ms_total`, `completed_with_duration` | Süre tahmini için girdi verisi |
| `run_started_at` | Çalıştırmanın `started_at` değeri |
| `percent` | `completed / total` yüzdesi; henüz kayıt yoksa **`null`** (0 değil) |

Yeni oluşturulan analizde `total = 0` ve `percent = null`'dır.

Detay yanıtındaki `generated_test_count`, analize ait üretilmiş test (`GeneratedTest`) sayısıdır; henüz
çalıştırılmamış testleri de sayar ve `progress.total`'dan (yürütme kaydı olan testler) farklı olabilir.
