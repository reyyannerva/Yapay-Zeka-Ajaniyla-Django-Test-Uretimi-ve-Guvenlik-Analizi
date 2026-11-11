# H3-05 | LLM ile İlk Pytest Üretimi Denemesi (Issue #31)

Groq üzerinden **açık-ağırlıklı bir dil modeli** (LiteLLM) kullanılarak, H3-04 ortak endpoint özeti
ve H3-03 bağımsız referans gereksinimlerinden üretilen Pytest testleri, bunların çalıştırma kanıtları
ve raporları. Kaynak kod: [`agent/test_generation/llm/`](../../agent/test_generation/llm/README.md).

İlgili isterler: İST-03, İST-04, İST-05, İST-06, İST-10, İST-11, İST-12, İST-15, İST-16.

## Model notu (Issue #31 ile fark)

Issue #31 **"Llama 3.3 70B"** modelini belirtir. Ancak çalıştırma sırasında bu model Groq
hesabında **erişilemez** çıktı (`model_not_found`; Groq kataloğunda Llama 3.x sohbet modeli
listelenmiyor — kota/ücret sorunu değil: aynı anahtarla diğer modeller çalıştı). Kabul edilen
proje öneri formu modeli ada bağlamaz; aynen *"Groq üzerinden erişilen açık ağırlıklı bir dil
modeli"* der (İST-05 model sağlayıcıyı esnek bırakır). Bu nedenle, hesapta mevcut ve açık-ağırlıklı
olan **`openai/gpt-oss-120b`** kullanılmıştır. Kod LiteLLM ile model-bağımsız olduğundan, Llama
3.3 70B ileride erişilebilir olursa tek satır (`.env` `LLM_MODEL`) ile geçilebilir. Kullanılan model
raporlara (`generation_report.json`) ve üretilen her teste kaydedilir.

## Dizin yapısı

```
experiments/h3_05_llm_baseline/
├── .env.example            Ortam değişkeni örneği (.env gitignore'ludur; anahtar repoya girmez)
├── prompts/pytest_v1.md    Prompt şablonu ve sızıntı ilkesi
├── prompts_sent/           LLM'e gönderilen render edilmiş istemler (giriş verileri; sır içermez)
├── generated_tests/        ÜRETİLMİŞ Pytest paketi (+ conftest.py, pytest.ini) — elle düzenlenmez
├── raw_responses/          Ham model yanıtları (sır içermez; izlenebilirlik)
├── reports/
│   ├── generation_report.{json,md}   Üretim durumları, token/süre, girdi SHA-256
│   ├── execution_report.{json,md}    Pytest sonuçları ve H3-04 uyumlu sınıflandırma
│   └── error_analysis.md             Karşılaşılan model hataları (model_not_found, TPM) ve ele alınışı
└── requirements.txt
```

## Kurulum ve anahtar

```bash
pip install -r experiments/h3_05_llm_baseline/requirements.txt
cp experiments/h3_05_llm_baseline/.env.example experiments/h3_05_llm_baseline/.env
# .env içine GROQ_API_KEY=... yazın (https://console.groq.com -> API Keys)
```

## Çalıştırma (depo kökünden)

```bash
python -m agent.test_generation.llm all        # üret + çalıştır + raporla (38 senaryo)
python -m agent.test_generation.llm prompts    # LLM çağrısı olmadan istemleri (giriş verileri) kaydet
# TPM sınırı için throttle: --inter-delay 8 --max-retries 10
# Üretilen testleri doğrudan pytest ile:
cd experiments/h3_05_llm_baseline/generated_tests && python -m pytest -q
```

Çıkış kodu: `0` = başarı, `2` = beklenmeyen uygulama uyuşmazlığı (APPLICATION_MISMATCH) var,
`3` = girdi/anahtar kullanılamaz.

## Sınıflandırma (H3-04 ile uyumlu)

- **Üretim:** GENERATED · INVALID_SYNTAX · EMPTY_OUTPUT · LLM_ERROR
- **Çalıştırma:** PASSED · KNOWN_FLAW_DETECTED · KNOWN_FLAW_NOT_DETECTED · APPLICATION_MISMATCH ·
  GENERATION_ERROR. Bilinen kusuru tespit eden başarısız test **beklenen** sonuçtur (üretim hatası değil).

## Sonuçlar

Model `groq/openai/gpt-oss-120b`, 38 senaryo, prompt `pytest_v1`, sıcaklık 0.0 ile gerçek
çalıştırma (ayrıntı: `reports/`). TPM (8000) sınırı nedeniyle istekler arası bekleme + geri
çekilmeli yeniden deneme kullanıldı (`--inter-delay 8 --max-retries 10`).

**Üretim:** 38/38 `GENERATED` (geçerli Pytest sözdizimi) · `INVALID_SYNTAX`/`EMPTY_OUTPUT`/
`LLM_ERROR` = 0. Metot dağılımı: GET 10, POST 9, PUT 8, PATCH 4, DELETE 7.

**Çalıştırma (kontrollü fixture):**

| Sınıf | Adet |
|---|---|
| PASSED | 35 |
| KNOWN_FLAW_DETECTED | 2 (SC-FLW-001 PUT, SC-FLW-002 DELETE — BOLA/IDOR; güvenli beklenti 403) |
| KNOWN_FLAW_NOT_DETECTED | 1 (SC-FLW-003 — içerik düzeyi taslak ifşası; durum kodu 200 doğru) |
| APPLICATION_MISMATCH | 0 |
| GENERATION_ERROR | 0 |

**Kaynak tüketimi (İST-12):** toplam ~35.060 token (prompt 25.638 / completion 9.422);
ortalama yanıt süresi ~1.666 ms, en yüksek ~5.695 ms.

> Not: pytest çıkış kodu 1'dir; çünkü bilinen güvenlik kusurunu doğru biçimde tespit eden 2 test
> (BOLA) bilerek başarısız olur — bu **beklenen** sonuçtur, üretim/çalıştırma hatası değildir.
> Bu çıktı, kural tabanlı baseline (#30: 35 PASSED / 2 DETECTED / 1 NOT_DETECTED) ile aynı kalitededir;
> H3-06 (#32) üç yöntemi aynı koşullarda karşılaştıracaktır. Sonuçlar çalıştırmadan alınmıştır;
> metrik uydurulmamıştır.

## Bilinen kısıtlar

- Bu bir **ilk LLM denemesidir**; amacı üretim geçerliliğini, çalıştırılabilirliğini ve model
  hatalarını incelemektir. Otomatik düzeltme (self-repair) kapsam dışıdır (sonraki haftalar).
- İçerik düzeyi kusur (SC-FLW-003) yalnızca durum koduyla değerlendirilir; durum kodu doğru olduğundan
  bu baseline onu KNOWN_FLAW_NOT_DETECTED olarak işaretler (H3-04 ile aynı sınır).
- Docker izole yürütme Hafta 8 kapsamıdır; bu prototip kontrollü fixture ortamında yerel çalışır.
