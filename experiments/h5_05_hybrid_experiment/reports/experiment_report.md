# H5-05 / Issue #43 — Hibrit test üretimi, metrik analizi ve karşılaştırmalı deney raporu

> Tüm sonuçlar **geliştirme kümelerine** aittir. Bağımsız (mühürlü) test kümesi üzerinde doğrulanmış nihai
> performans olarak sunulamaz. Güncel koşu: 2026-11-25 (koşu 2). Groq erişimi olmadan yapılan koşu 1, deney
> geçmişi olarak `results/history/run1_2026-11-25_llm_blocked/` altında saklanmıştır ve geçersiz kılınmıştır.

## 1. Amaç ve kapsam
Bu çalışmanın hedefleri:
- H3-04 kural tabanlı ve H3-05 Groq LLM üreticilerini birleştiren sınırlı bir hibrit yaklaşım tanımlamak.
- Üç yöntemi aynı geliştirme senaryolarında ve aynı değerlendirme hattıyla (#32 `agent.evaluation`,
  değiştirilmeden) karşılaştırmak.
- Sonuçları F1 ≥ 0.80 ve ilk geçişte çalıştırılabilirlik ≥ %70 hedefleriyle kıyaslamak.

## 2. Veri ve ayrım
**Katman A:**
- H5-04'ün değiştirilmemiş 20 geliştirme senaryosudur (`split.json` → dev).
- HTTP dağılımı: GET 9, POST 9, PUT 1 (405), DELETE 1 (405), **PATCH 0**. Bilinen kusur: 0.
- H5-04 manifesti koşudan önce doğrulanır.

**Katman B:**
- Ayrı bir `Task` kaynağı üzerinde 17 kontrollü senaryodur.
- HTTP dağılımı: GET 3, POST 2, PUT 3, PATCH 6, DELETE 3.
- 3 bağımsız etiketli BOLA/IDOR kusuru içerir.
- Issue #43, H5-04 alt kümesi ile "beş metodun tamamı" koşulunu birlikte istiyor. H5-04 alt kümesinde PATCH
  olmadığı için iki koşul aynı kümede sağlanamaz. Katman B bu boşluğu kontrollü bir ek geliştirme kümesi
  olarak kapatır; Katman A değiştirilmeden korunur.

**Mühürlü test kümesi:** H3-03 `test_set.json` açılmadı. Ayrım ihlali denetimi için yalnızca `split.json`
içindeki kimlik→bölüm eşlemesi okunur.

## 3. Katman B tasarımı ve dondurma
Hedef uygulama `layer_b/target_app` (Django + DRF, SQLite):
- `TaskViewSet`: kayıtları yalnızca sahibi veya yönetici değiştirebilir.
- `LegacyTaskDetail`: sahiplik denetimi yoktur (bilinçli kusur).

Dondurma:
- Ground truth, senaryolar, şemalar, fixture'lar ve uygulama kodu **üretimden önce** SHA-256 ile donduruldu
  (`layer_b/FROZEN.json`, commit `c513958`, 2026-11-25T21:51:54Z).
- Koşu 2'den önce bu dosyaların `c513958` ile birebir aynı olduğu doğrulandı (`git diff` boş, `verify` OK).
- Fixture ↔ ground truth çapraz kontrolü: 19/19.

## 4. Yöntemler
| Yöntem | Katman A kaynağı | Katman B kaynağı |
|---|---|---|
| Kural tabanlı (H3-04) | Donmuş ilk geçiş testleri | H5-05'te etiket maskeli girdilerle üretildi (17/17) |
| Groq LLM (H3-05) | H3-05'in **arşivlenmiş** ilk geçiş ham yanıtları | H5-05'te **yeni gerçek Groq koşusu** (17/17 GENERATED, 0 hata) |
| Hibrit (H5-05) | İki adayın deterministik birleşimi | İki adayın deterministik birleşimi |

## 5. Model şeffaflığı
- Planlanan model: Llama 3.3 70B (#31).
- **Gerçekte kullanılan:** `groq/openai/gpt-oss-120b` (her iki katmanda da aynı).
- Üretim parametreleri:
  - İstem `pytest_v1`, sıcaklık 0.0, max_tokens 1200, istek zaman aşımı 60 sn.
  - Bunlar H3-05 CLI varsayılanlarıdır ve H3-05 raporuyla aynıdır.
  - Ek olarak istekler arası 2 sn bekleme ve en fazla 3 yeniden deneme kullanıldı.
- Katman B LLM koşusu:
  - 17 istek, 15 714 token, toplam 16,3 sn gecikme.
  - Ücretli kullanım başlatılmadı.
  - Kayıtlı hata yok (`LLM_ERROR` 0).
- Sessiz model değişimi yapılmadı. Katman A arşiv çıktısı ile Katman B yeni koşusu ayrı kaynak olarak kaydedildi
  (`raw_generation_results.json`, `experiment_config.json`).
- API anahtarı oturumun ağ proxy'si tarafından yalnızca `api.groq.com` isteklerine eklendi. Anahtar hiçbir
  dosyaya, loga veya üretilen testlerin ortamına girmedi. Değerlendirme alt süreçlerinden `GROQ_*`
  değişkenleri ayrıca çıkarılır.

## 6. Hibrit politika (`hybrid.py`, `normalize.py`)
**1. İmza çıkarma.** Her aday AST ile anlamsal imzaya indirgenir. Kod çalıştırılmaz. İmza alanları:
- yöntem;
- somut uç (`url_name` → yol şablonu);
- kimlik ve aktör;
- gövde;
- fixture önkoşulları;
- beklenen durum;
- doğrulama türleri: `status`, `route`, `side_effect`, `body`. `response`'tan türeyen değişkenler üzerindeki
  doğrulamalar da `body` sayılır.

**2. Referans kontrolü.** Aday referans gereksinimle karşılaştırılır: yöntem, uç, kimlik, aktör ve
`secure_status`. Tutarsız aday reddedilir. Ground truth değerlendirme etiketleri bu adıma girmez.

**3. Tutarlı adaylar için karar kuralları:**
- **Aynı anahtar (anlamsal eşitlik).** Kod eşitliği ayrıca `code_identical` alanına yazılır.
  - LLM doğrulamaları kural tabanlının alt kümesiyse → **yinelenen**. Kural tabanlı tutulur, LLM düşürülür.
  - LLM ek doğrulama türü içeriyorsa → **birleştirilir**. Kural tabanlı test ve LLM testi (`__llm` son ekiyle)
    aynı modüle konur, böylece hiçbir kontrol kaybolmaz.
- **Farklı anahtar** → çözülmüş çelişki. Daha çok doğrulama türü içeren aday seçilir; eşitlikte kural tabanlı.
- **Tek tutarlı aday** → o aday seçilir.
- **Hiç tutarlı aday yok** → çözülmemiş çelişki; test üretilmez.

**4. Kayıt.** Aday ve karar kayıtları kaynak bilgisiyle `hybrid_candidates.jsonl` ve
`hybrid_decisions.jsonl` dosyalarına yazılır.

**Koşu 1'deki hatanın düzeltilmesi:**
- Önceki politika, anahtar eşitse LLM adayını koşulsuz düşürüyordu.
- Katman A SC-LST-001'de LLM testi, yanıttaki her kaydın `is_published` olduğunu doğrulayan bir **gövde
  kontrolü** içeriyor. Bu kontrol kural tabanlı testte yok ve önceki politika onu kaybediyordu.
- Ayrıca gece raporundaki "20/20 özdeş" ifadesi **yanlıştı**. Anahtarlar aynıydı, ama kod hiçbir çiftte
  birebir aynı değil: kural tabanlı testler rota ve yan etki, LLM testleri genellikle yalnızca durum kontrol eder.
- Politika düzeltildi ve birim testleriyle doğrulandı; deney tamamen yeniden koşuldu.

| Sayaç | Katman A | Katman B |
|---|---|---|
| Kural tabanlı aday | 20 | 17 |
| LLM aday | 20 | 17 |
| Anlamsal anahtarı eşit çift | 20 | 17 |
| Kodu birebir aynı çift | **0** | **0** |
| Yinelenen (LLM düşürüldü; doğrulamaları kural tabanlının alt kümesi) | 19 | 17 |
| Birleştirilen (kural tabanlı + LLM tamamlayıcı test) | 1 (SC-LST-001, `body`) | 0 |
| Çözülen / çözülmeyen çelişki | 0 / 0 | 0 / 0 |
| Referansla tutarsız aday | 0 | 0 |
| Nihai test modülü / test fonksiyonu | 20 / 21 | 17 / 17 |

## 7. Çalıştırma ortamı ve güvenlik
- Ortam: Python 3.13.18, Django 5.2.19, pytest 9.2.0, Linux.
- Her senaryo geçici bir dizinde ve ayrı bir pytest sürecinde çalışır; zaman aşımı 120 sn.
- Üretilen kod güvenilmez kabul edilir:
  - Dış ağ veya süreç erişimi içeren test çalıştırılmaz (`UNSAFE_BLOCKED`; bu koşuda 0).
  - Testler yalnızca geçici SQLite test veritabanında çalışır.
- Loglarda çalışma dizini `<WORK>`, depo yolu `<REPO>` olarak maskelenir.
- **Test altyapısı uyarlaması (Katman B LLM):**
  - H3-05'in destek `conftest.py`'si fixture adlarını `"users", "articles"` olarak sabit yazar.
  - Katman B hedefinde `articles` fixture'ı yoktur; bu haliyle her LLM testi model kodundan bağımsız olarak
    kurulum hatası verirdi.
  - Yalnızca bu fixture listesi, endpoint özetindeki `target_app.fixtures` (`users`, `tasks`) ile değiştirildi
    (`layer_b_inputs.write_llm_harness`).
  - Başka bir satır değişmez; bu bir testle doğrulanır. **LLM test kodu değiştirilmedi** (ilk geçiş).

## 8. Metrik tanımları (`metrics.py`, #32 üzerine)
**Birim ve eşleşme:**
- Birim senaryodur. Ground truth eşleşmesi `(scenario_id, http_method)` ile yapılır; yöntem uyuşmazlığında
  eşleşme yoktur.
- Bir senaryoda birden çok başarısız doğrulama olsa da **tek** bulgu sayılır.

**Karışıklık matrisi:**

| Sonuç | Kusur var | Kusur yok |
|---|---|---|
| FAIL | TP | FP |
| PASS | FN | TN |
| Teknik hata / çalışmayan test | FN | EXCLUDED |

- PASS hiçbir zaman TP sayılmaz. Kusursuz senaryoda FAIL bir tespit değil, FP'dir.

**Oranlar:**
- Precision = TP/(TP+FP), Recall = TP/(TP+FN), F1 = 2PR/(P+R).
- Payda sıfırsa değer **Ölçülemedi** olur; 0 veya 1 ile doldurulmaz.

**İlk geçişte çalıştırılabilirlik:**
- **Pay:** PASS veya FAIL sonuçlanan senaryo sayısı. İlk üretim kullanılır, otomatik düzeltme yapılmaz;
  `corrected=True` satırlar reddedilir.
- **Payda:** değerlendirilebilir tüm senaryolar (test üretilemeyen veya çalışmayanlar dahil).
- Test düzeyinde ayrıca: PASS veya FAIL sonuçlanan test fonksiyonu / toplanan test fonksiyonu.

**Ayrı kaydedilen ölçütler:**
- sözdizimi (`ast.parse`);
- toplama (`--collect-only`);
- yürütme sonucu (PASS/FAIL/ERROR/TIMEOUT/NOT_RUN). NOT_RUN satırında gerekçe zorunludur.

**Bağımsız çapraz kontrol:** `verify_metrics.py`, metrik motorunu kullanmadan yalnızca
`execution_results.csv` ve donmuş ground truth'tan yeniden hesaplar. Sonuç: **UYUŞUYOR**.

## 9. Katman A sonuçları (20 senaryo; aynı girdi özetleri, karşılaştırılabilir)
| Yöntem | Sözdizimi | Toplanan | İlk geçiş (pay/payda) | Test düzeyi | PASS/FAIL/ERROR/TIMEOUT/NOT_RUN | TP/FP/TN/FN | P / R / F1 | F1 hedefi | Çalıştırılabilirlik hedefi |
|---|---|---|---|---|---|---|---|---|---|
| Kural tabanlı | 20/20 | 20/20 | 20/20 = 1.00 | 20/20 | 20/0/0/0/0 | 0/0/20/0 | Ölçülemedi | Ölçülemedi | Karşılandı |
| Groq LLM (arşiv) | 20/20 | 20/20 | 20/20 = 1.00 | 20/20 | 20/0/0/0/0 | 0/0/20/0 | Ölçülemedi | Ölçülemedi | Karşılandı |
| Hibrit | 20/20 | 20/20 | 20/20 = 1.00 | 21/21 | 20/0/0/0/0 | 0/0/20/0 | Ölçülemedi | Ölçülemedi | Karşılandı |

- Katman A'da kusur yoktur: TP+FN = 0 ve TP+FP = 0, bu yüzden Precision, Recall ve F1 **ölçülemez**.
- Kural tabanlı ve LLM sonuçları H5-04 ile aynıdır (40/40 PASS).

## 10. Katman B sonuçları (17 senaryo, 3 kusur; aynı girdi özetleri, karşılaştırılabilir)
| Yöntem | Sözdizimi | Toplanan | İlk geçiş (pay/payda) | PASS/FAIL/ERROR/TIMEOUT/NOT_RUN | TP/FP/TN/FN | P / R / F1 | F1 hedefi | Çalıştırılabilirlik hedefi |
|---|---|---|---|---|---|---|---|---|
| Kural tabanlı | 17/17 | 17/17 | 17/17 = 1.00 | 14/3/0/0/0 | 3/0/14/0 | 1.00 / 1.00 / 1.00 | Karşılandı | Karşılandı |
| Groq LLM (yeni koşu) | 17/17 | 17/17 | 17/17 = 1.00 | 14/3/0/0/0 | 3/0/14/0 | 1.00 / 1.00 / 1.00 | Karşılandı | Karşılandı |
| Hibrit | 17/17 | 17/17 | 17/17 = 1.00 | 14/3/0/0/0 | 3/0/14/0 | 1.00 / 1.00 / 1.00 | Karşılandı | Karşılandı |

Kusurların değerlendirme semantiği: her üç yöntemde de tespit, **durum kodu sapmasıyla** oldu (beklenen
güvenli kod 403):

| Senaryo | Metot | Beklenen | Gözlenen (kural tabanlı ve hibrit) | Gözlenen (LLM) |
|---|---|---|---|---|
| SC-TKX-001 | PUT | 403 | 200 (`check=status`) | 200 |
| SC-TKX-002 | PATCH | 403 | 200 (`check=status`) | 200 |
| SC-TKX-003 | DELETE | 403 | 204 (`check=status`) | 204 |

Kusursuz 14 senaryonun hiçbiri FAIL vermedi (FP = 0).

## 11. HTTP metodu kapsamı
| Yöntem | Katman A | Katman B | Birleşim |
|---|---|---|---|
| Kural tabanlı | GET, POST, PUT, DELETE | GET, POST, PUT, PATCH, DELETE | 5/5 |
| Groq LLM | GET, POST, PUT, DELETE | GET, POST, PUT, PATCH, DELETE | 5/5 |
| Hibrit | GET, POST, PUT, DELETE | GET, POST, PUT, PATCH, DELETE | 5/5 |

PUT, PATCH ve DELETE metotlarının gerçek güvenlik davranışı (yetki, sahiplik, yan etki) yalnızca Katman B'de
sınanır. Katman A'da PUT ve DELETE yalnızca 405 senaryolarıdır.

## 12. Hibrit yöntemin katkısı (gerçek sonuç)
- Hibrit gerçekten iki üreticiyi kullanmıştır. Her senaryoda iki aday değerlendirildi (`candidate_status`) ve
  Katman A SC-LST-001'de kural tabanlı rota kontrolü ile LLM gövde kontrolü birleştirildi.
- Buna karşın **metrik düzeyinde ek kazanım yoktur.** Üç yöntem iki katmanda da aynı karışıklık matrisini ve
  aynı çalıştırılabilirliği verdi. Birleştirilmiş SC-LST-001 de PASS oldu; ek kontrol yeni bir bulgu üretmedi.
- Hibritin kalıcı katkısı **doğrulama kapsamıdır**. Nihai test kümesi rota, yan etki ve gövde kontrollerinin
  birleşimini içerir; tek bir üreticinin kontrolleri kaybolmaz. Bu deneyde hibritin tespit üstünlüğü
  **gösterilememiştir** ve iddia edilmemektedir.

## 13. Başarılı / başarısız örnekler ve hata analizi
**Sonuç dağılımı:**
- Hiçbir yöntemde sözdizimi hatası, toplama hatası, ERROR, TIMEOUT, NOT_RUN veya UNSAFE_BLOCKED oluşmadı
  (`failure_analysis.json`).
- PASS dışı sonuçlar yalnızca Katman B'de görüldü: her yöntemde 3 FAIL. Üçü de beklenen tespittir (TP).

**Kural tabanlı:**
- Güçlü yön: `[H304] check=route|status|side_effect` işaretleriyle hatanın kaynağı ayrıştırılabilir ve yan
  etki doğrulanır.
- Sınırlılık: yalnızca endpoint özeti ve referansta tanımlı kalıpları üretebilir.

**LLM:**
- Güçlü yön: zaman zaman ek anlamsal kontroller üretir (SC-LST-001 gövde kontrolü).
- Sınırlılık: çoğunlukla yalnızca durum kodunu doğrular; yan etki kontrolü yoktur.

**Altyapı riski:**
- H3-05 destek conftest'i hedefe özgü sabit fixture içeriyordu (§7).
- Bu, yeni bir hedefte model kodundan bağımsız hata üretebilecek bir taşınabilirlik sorunudur.

## 14. Hedef değerlendirmesi (gerçek ölçümler)
| Hedef | Katman A | Katman B |
|---|---|---|
| İlk geçişte çalıştırılabilirlik ≥ %70 | Üç yöntem Karşılandı (20/20) | Üç yöntem Karşılandı (17/17) |
| F1 ≥ 0.80 | Üç yöntem **Ölçülemedi** (pozitif yok) | Üç yöntem Karşılandı (1.00; n = 17, 3 pozitif) |

## 15. Sınırlılıklar, geçerlilik tehditleri ve yeniden üretim
**Sınırlılıklar ve geçerlilik tehditleri:**
- **Döngüsellik:** Katman B'nin senaryoları, hedef uygulaması ve ground truth'u aynı geliştirme sürecinde
  hazırlandı. F1 = 1.00 küçük (3 pozitif) ve kontrollü bir kümeye aittir. Bağımsız test performansı veya
  genellenebilirlik kanıtı **değildir**; tüm projenin performansı olarak sunulamaz.
- **Sızıntı riski (önceden var):** H3-04 `planner.py` / `codegen.py`, `is_known_flaw` alanını okur. Katman A
  dev kümesinde kusur olmadığından sonuç etkilenmez. H5-05 Katman B'de iki üreticiye de etiket maskeli görünüm
  verildi; sızıntı testlerle doğrulanır:
  - `is_known_flaw` maske olarak `False` yapılır, `security_finding` kaldırılır;
  - senaryodaki gözlenen kusurlu kod güvenli kodla değiştirilir;
  - endpoint özetinde `intentionally_insecure=false` yapılır.
- Katman A LLM çıktıları H3-05 arşividir. Katman B ise yeni koşudur; iki koşu arasında model sağlayıcısının
  davranışı değişmiş olabilir.
- Katman B LLM için test altyapısı uyarlaması (§7) yapılmıştır; model kodu değiştirilmemiştir.
- Önceden var olan bulgu: H3-05 `generation_report.json` içinde mutlak bir Windows yolu var. H5-05'te
  değiştirilmedi. Katman B LLM raporu göreli yollar içerir.
- Önceki haftaların sonuçları değiştirilmedi; H5-04 ve H3 artefaktlarına dokunulmadı.

**Yeniden üretim:**
```bash
python -m experiments.h5_05_hybrid_experiment verify
python -m experiments.h5_05_hybrid_experiment run [--layer A|B] [--resume]
python experiments/h5_05_hybrid_experiment/verify_metrics.py
python -m pytest -p no:cacheprovider experiments/h5_05_hybrid_experiment/tests
```
Katman B LLM üretimi (Groq erişimi gerekir; anahtar `GROQ_API_KEY` ortam değişkeninde ya da proxy'de olmalı):
```bash
python -m agent.test_generation.llm generate \
  --endpoints experiments/h5_05_hybrid_experiment/layer_b/endpoint_summary.json \
  --ground-truth experiments/h5_05_hybrid_experiment/layer_b/generator_inputs/reference_requirements.json \
  --scenarios experiments/h5_05_hybrid_experiment/layer_b/generator_inputs/scenarios.json \
  --out experiments/h5_05_hybrid_experiment/layer_b/generated/llm/generated_tests \
  --raw experiments/h5_05_hybrid_experiment/layer_b/generated/llm/raw_responses \
  --reports experiments/h5_05_hybrid_experiment/layer_b/generated/llm/reports \
  --prompts-sent experiments/h5_05_hybrid_experiment/layer_b/generated/llm/prompts_sent \
  --max-retries 3 --inter-delay 2
```
`--resume` yalnızca artefakt (destek dosyaları dahil) ve girdi özetleri aynı olan kontrol noktalarını yeniden
kullanır. LLM çıktıları eklendiğinde Katman B'nin LLM ve hibrit satırları otomatik olarak yeniden çalışır.

H5-06 devir paketi: `reports/h5_06_handoff.json`.
