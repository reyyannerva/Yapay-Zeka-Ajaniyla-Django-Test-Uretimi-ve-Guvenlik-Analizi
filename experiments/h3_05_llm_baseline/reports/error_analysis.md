# H3-05 | Karşılaşılan Model Hataları ve Ele Alınışı (Issue #31)

Bu belge, canlı Groq çalıştırması sırasında **gerçekten gözlemlenen** model/servis hatalarını ve
bunların kontrollü biçimde nasıl ele alındığını kaydeder (todo: "model kotası, bağlantı hatası,
zaman aşımı ve geçersiz yanıt durumlarını kontrollü biçimde ele almak; hata nedenlerini gizli bilgi
içermeyen kayıtlarla belgelemek"). Nihai `generation_report.json` başarılı (0 hata) çalıştırmadan
alınmıştır; aşağıdaki kayıtlar bu başarıya giden yolda ele alınan hatalardır.

## 1. `model_not_found` — istenen model erişilemez

- **Gözlem:** `litellm.NotFoundError: GroqException - The model 'llama-3.3-70b-versatile' does not
  exist or you do not have access to it` (38/38 senaryoda).
- **Kök neden:** Issue #31'in belirttiği Llama 3.3 70B, kullanılan Groq hesabının model kataloğunda
  yok (kota/ücret değil; `GET /openai/v1/models` listesinde Llama sohbet modeli görünmüyor).
- **Ele alış:** İstemci hatayı `auth/other` olarak sınıflandırıp kaydetti. Model `GET /models` ile
  doğrulandı; hesapta mevcut ve **açık-ağırlıklı** `openai/gpt-oss-120b`'ye geçildi (öneri formu
  model adını bağlamaz; bkz. README "Model notu"). Kod LiteLLM ile model-bağımsız olduğundan geçiş
  `.env`/`--model` ile yapıldı.

## 2. `RateLimitError` (quota) — dakikalık token sınırı (TPM)

- **Gözlem:** `litellm.RateLimitError: GroqException - Rate limit reached ... service tier
  'on_demand' on tokens per minute (TPM): Limit 8000 ... Please try again in ~2.9s`. Throttle'sız
  ilk çalıştırmada 38 senaryonun 26'sı `LLM_ERROR` (quota) oldu.
- **Kök neden:** Ücretsiz katman TPM sınırı 8000; 38 ardışık istek (~35k token) sınırı aşıyor.
- **Ele alış (kontrollü):**
  - **Geri çekilmeli yeniden deneme:** geçici hatalarda (`quota/timeout/connection`) mesajdaki
    "try again in Xs" ipucu okunur; yoksa üstel geri çekilme uygulanır (`generator._complete_with_retry`).
  - **İstekler arası bekleme:** `--inter-delay` ile TPM sınırının altında kalınır.
  - **Sonuç:** `--inter-delay 8 --max-retries 10` ile **38/38 GENERATED, 0 LLM_ERROR**.
  - Birim testi: `test_generator_retry_then_success` (geçici quota sonrası başarı), `test_classify_*`.

## 3. Hata yönetimi tasarımı

- Hata türleri: `auth` · `quota` · `timeout` · `connection` · `other` (`client.GroqClient._classify`).
- **Gizli bilgi koruması:** hata mesajlarında `gsk_...` kalıbı `gsk_***` ile maskelenir
  (`client._sanitize`); API anahtarı log/rapor/koda yazılmaz.
- Üretim raporunda her senaryonun `error` alanı bulunur (başarıda `null`); üretim durumu
  `LLM_ERROR/EMPTY_OUTPUT/INVALID_SYNTAX/GENERATED` olarak ayrılır.
- Çalıştırma tarafında üretim hatası (`GENERATION_ERROR`) ile bilinen kusur kaynaklı başarısızlık
  (`KNOWN_FLAW_DETECTED`) ayrı sınıflandırılır.
