# H5-05 / Issue #43 — Hibrit test üretimi, metrik analizi ve karşılaştırmalı deney raporu

> **Durum:** Kısmi teslim. Hibrit yöntem geliştirildi ve iki katmanda çalıştırıldı. Groq LLM ile
> **yeni** üretim bu oturumda yapılamadı: kimlik bilgisi yok ve `api.groq.com` erişilemiyor. Bu yüzden AC3 ve AC7
> **Kısmen** karşılandı (§13, `ac_traceability.md`). Tüm sonuçlar **geliştirme kümesine** aittir;
> bağımsız test kümesi üzerinde doğrulanmış nihai performans olarak sunulamaz.

## 1. Amaç ve kapsam
H3-04 kural tabanlı ve H3-05 Groq LLM üreticilerini birleştiren sınırlı bir hibrit yaklaşım tanımlamak, üç
yöntemi aynı geliştirme senaryolarında aynı değerlendirme hattıyla (#32 `agent.evaluation`) karşılaştırmak
ve F1 ≥ 0.80 ile ilk geçişte çalıştırılabilirlik ≥ %70 hedefleriyle kıyaslamak.

## 2. Veri ve ayrım
- **Katman A:** H5-04'ün değiştirilmemiş 20 geliştirme senaryosu (`split.json` → dev; aileler F-LIST,
  F-RETRIEVE, F-CREATE, F-PUBLISH, F-METHOD). HTTP dağılımı: GET 9, POST 9, PUT 1 (405), DELETE 1 (405),
  **PATCH 0**. Bilinen kusur: 0. H5-04 manifesti koşudan önce doğrulanır (`h504.verify`).
- **Katman B:** H5-05 için ayrı bir `Task` kaynağı üzerinde hazırlanmış 17 kontrollü senaryo: GET 3, POST 2,
  PUT 3, PATCH 6, DELETE 3. 3 bağımsız etiketli BOLA/IDOR kusuru içerir (§3).
- Mühürlü H3-03 test kümesi (`test_set.json`) **açılmadı**. Yalnızca `split.json` içindeki kimlik→bölüm
  eşlemesi, ayrım ihlali denetimi için okunur. Bir test senaryosu deneye girerse `SplitViolation` oluşur.

## 3. Katman B tasarımı ve dondurma
Hedef uygulama `layer_b/target_app` (Django + DRF, SQLite):
- `TaskViewSet`: sahip veya yönetici yazabilir.
- `LegacyTaskDetail`: sahiplik denetimi **yoktur**; bilinçli BOLA kusuru.

Ground truth, senaryolar, şemalar, fixture'lar ve uygulama kodu **üretimden önce** SHA-256 ile donduruldu
(`layer_b/FROZEN.json`, 2026-11-25T21:51:54Z). Fixture çapraz kontrolü 19/19 geçti: kusursuz senaryolar
`secure_status`'u, kusurlu senaryolar `observed_flawed_status`'u döndürüyor. Koşu `verify_frozen()` ile başlar;
özet uyuşmazlığında durur.

## 4. Yöntemler
| Yöntem | Katman A kaynağı | Katman B kaynağı |
|---|---|---|
| Kural tabanlı (H3-04) | `experiments/h3_04_rule_based_baseline/generated_tests` (donmuş ilk geçiş) | H5-05'te etiket maskeli girdilerle üretildi (17/17 GENERATED) |
| Groq LLM (H3-05) | `experiments/h3_05_llm_baseline/raw_responses` (arşiv ilk geçiş) | **BLOCKED**: istemler kaydedildi, model çağrılmadı |
| Hibrit (H5-05) | İki adayın deterministik birleşimi | Yalnızca kural tabanlı aday mevcut, bu yüzden hibrit = kural tabanlı |

## 5. Model şeffaflığı
- Planlanan model: Llama 3.3 70B (#31).
- Gerçekte kullanılan: `groq/openai/gpt-oss-120b`, istem `pytest_v1`, sıcaklık 0.0. Kaynak H3-05
  `generation_report.json`.
- Katman A'daki LLM çıktıları H3-05'in **arşivlenmiş** ilk geçiş yanıtlarıdır; H5-05'te yeniden üretilmedi.
- Sessiz model değişimi veya başka bir sağlayıcıya geçiş yapılmadı. Arşiv çıktısı yeni koşu gibi sunulmadı.

## 6. Hibrit politika (`hybrid.py`, `normalize.py`)
1. Her aday AST ile anlamsal imzaya indirgenir: yöntem, somut uç (endpoint özetindeki `url_name` → yol
   şablonu), kimlik/aktör, gövde, fixture önkoşulları, beklenen durum ve doğrulama türleri. Kod çalıştırılmaz.
2. Aday **referans gereksinimle** karşılaştırılır: yöntem, uç, kimlik, aktör ve `secure_status`. Tutarsızsa
   reddedilir. Ground truth etiketleri bu adıma girmez; `reference_view` bunları maskeler ve
   `assert_no_label_leak` ile doğrulanır.
3. Tutarlı adaylar için karar kuralları:
   - Aynı anahtar → yinelenen; kural tabanlı tutulur, çünkü rota ve yan etki doğrulamalarını da içerir.
   - Farklı anahtar → çözülmüş çelişki; daha çok doğrulama türü içeren aday seçilir, eşitlikte kural tabanlı.
   - Tek tutarlı aday → o aday seçilir.
   - Tutarlı aday yok → çözülmemiş çelişki; test üretilmez.
4. Her aday `hybrid_candidates.jsonl`'e, her karar `hybrid_decisions.jsonl`'e kaynak bilgisiyle yazılır.

| Sayaç | Katman A | Katman B |
|---|---|---|
| Kural tabanlı aday | 20 | 17 |
| LLM aday | 20 | 0 (BLOCKED) |
| Yinelenen | 20 | 0 |
| Çözülen / çözülmeyen çelişki | 0 / 0 | 0 / 0 |
| Nihai test | 20 (20 kural tabanlı) | 17 (17 kural tabanlı) |
| Ortak / yalnız kural / yalnız LLM | 20 / 0 / 0 | 0 / 17 / 0 |

## 7. Çalıştırma ortamı ve güvenlik
- Ortam: Python 3.13.18, Django 5.2.19, pytest 9.2.0, Linux.
- Yalıtım: her senaryo geçici bir dizinde ve ayrı bir pytest sürecinde çalışır; zaman aşımı 120 sn.
- Üretilen kod güvenilmez kabul edilir. Dış ağ veya süreç erişimi içeren test çalıştırılmaz
  (`UNSAFE_BLOCKED`). Alt süreç ortamından `GROQ_`/`OPENAI_`/`ANTHROPIC_` değişkenleri çıkarılır.
- Testler yalnızca geçici SQLite test veritabanı üzerinde çalışır; geliştirme PostgreSQL'ine dokunulmaz.
- Loglarda çalışma dizini `<WORK>`, depo yolu `<REPO>` olarak maskelenir.

## 8. Metrik tanımları (`metrics.py`, #32 üzerine)
- Birim senaryodur. Eşleşme `(scenario_id, http_method)` ile yapılır; yöntem uyuşmazlığında eşleşme yoktur.
- Karışıklık matrisi:
  - FAIL + kusur = TP; FAIL + kusursuz = FP.
  - PASS + kusur = FN; PASS + kusursuz = TN.
  - Teknik hata veya çalışmayan test + kusur = FN; + kusursuz = EXCLUDED.
- Bir senaryodaki birden çok başarısız doğrulama **tek** bulgu sayılır.
- Precision = TP/(TP+FP), Recall = TP/(TP+FN), F1 = 2PR/(P+R). Payda sıfırsa sonuç **Ölçülemedi** olur;
  0 veya 1 ile doldurulmaz.
- **İlk geçişte çalıştırılabilirlik:**
  - Pay: PASS veya FAIL sonuçlanan senaryo sayısı. İlk üretim kullanılır, otomatik düzeltme yapılmaz;
    `corrected=True` satırlar reddedilir.
  - Payda: değerlendirilebilir tüm senaryolar (test üretilmeyenler dahil).
  - Test düzeyinde ayrıca hesaplanır: PASS/FAIL sonuçlanan test fonksiyonu / toplanan test fonksiyonu.
- Sözdizimi (`ast.parse`), toplama (`--collect-only`) ve yürütme sonucu (PASS/FAIL/ERROR/TIMEOUT/NOT_RUN)
  ayrı ayrı kaydedilir. NOT_RUN satırında gerekçe zorunludur.
- Hedef durumu dört değerden biridir: Karşılandı / Karşılanmadı / Ölçülemedi (payda 0) / Karşılaştırılamadı
  (yöntem denenemedi).

## 9. Katman A sonuçları (20 senaryo, karşılaştırılabilir: aynı girdi özetleri)
| Yöntem | Sözdizimi | Toplanan | İlk geçiş (pay/payda) | PASS/FAIL/ERROR/TIMEOUT/NOT_RUN | P / R / F1 | F1 hedefi | Çalıştırılabilirlik hedefi |
|---|---|---|---|---|---|---|---|
| Kural tabanlı | 20/20 | 20/20 | 20/20 = 1.00 | 20/0/0/0/0 | Ölçülemedi | Ölçülemedi | Karşılandı |
| Groq LLM (arşiv) | 20/20 | 20/20 | 20/20 = 1.00 | 20/0/0/0/0 | Ölçülemedi | Ölçülemedi | Karşılandı |
| Hibrit | 20/20 | 20/20 | 20/20 = 1.00 | 20/0/0/0/0 | Ölçülemedi | Ölçülemedi | Karşılandı |

- Katman A'da bilinen kusur yoktur (TP+FN = 0, TP+FP = 0). Bu nedenle F1 **ölçülemez**.
- Sonuçlar H5-04 ile birebir aynıdır: 40/40 PASS, `per_scenario.csv` ile doğrulandı.

## 10. Katman B sonuçları (17 senaryo, 3 kusur)
| Yöntem | Sözdizimi | İlk geçiş (pay/payda) | TP/FP/TN/FN | P / R / F1 | F1 hedefi | Çalıştırılabilirlik hedefi |
|---|---|---|---|---|---|---|
| Kural tabanlı | 17/17 | 17/17 = 1.00 | 3/0/14/0 | 1.00 / 1.00 / 1.00 | Karşılandı | Karşılandı |
| Groq LLM | — | 0/0 (17 senaryo değerlendirme dışı, BLOCKED) | — | Ölçülemedi | **Karşılaştırılamadı** | **Karşılaştırılamadı** |
| Hibrit (= kural tabanlı) | 17/17 | 17/17 = 1.00 | 3/0/14/0 | 1.00 / 1.00 / 1.00 | Karşılandı | Karşılandı |

Kusur tespitleri durum kodu sapmasıyla oldu:
- SC-TKX-001 PUT: beklenen 403, gözlenen 200.
- SC-TKX-002 PATCH: beklenen 403, gözlenen 200.
- SC-TKX-003 DELETE: beklenen 403, gözlenen 204.

## 11. Hibrit yöntemin katkısı
- Katman A'da 20 senaryonun 20'sinde iki aday anlamsal olarak **özdeştir** (aynı istek, aktör ve beklenti). Hibrit
  kural tabanlı testi seçti; LLM'e özgü bir katkı oluşmadı.
- Katman B'de LLM adayı olmadığı için hibrit kural tabanlıya **indirgendi**.
- Bu nedenle bu deneyde hibritin kural tabanlıya göre ek yararı **gösterilememiştir**. Yöntem
  çelişki/reddetme yollarını işletebilir; bunlar birim testlerle doğrulandı (`tests/test_hybrid_policy.py`).
  Ancak gerçek veride bu yollar tetiklenmedi.

## 12. Başarılı / başarısız örnekler ve hata analizi
- Hiçbir yöntemde sözdizimi hatası, toplama hatası, ERROR veya TIMEOUT oluşmadı (`failure_analysis.json`).
- PASS dışındaki satırlar:
  - Katman B'de kural tabanlı ve hibrit için 3 FAIL; bunların üçü de beklenen tespittir.
  - Katman B'de LLM için 17 NOT_RUN; gerekçe `LLM_GENERATION_BLOCKED`.
- Güçlü yön (kural tabanlı): rota, durum ve yan etki doğrulamaları ile hatanın kaynağı ayrıştırılabilir.
- Zayıf yön (kural tabanlı): yalnızca endpoint özeti ve referansta tanımlı kalıpları üretebilir.
- LLM (Katman A arşivi): yalnızca durum kodunu doğrular; yan etki doğrulaması yoktur.

## 13. Hedef değerlendirmesi
- **Çalıştırılabilirlik ≥ %70:**
  - Katman A: üç yöntemde de Karşılandı (20/20).
  - Katman B: kural tabanlı ve hibritte Karşılandı (17/17); LLM'de Karşılaştırılamadı.
- **F1 ≥ 0.80:**
  - Katman A: Ölçülemedi (pozitif yok).
  - Katman B: kural tabanlı ve hibritte Karşılandı (1.00, n = 3 pozitif); LLM'de Karşılaştırılamadı.
- LLM için F1 hedefi hiçbir katmanda **gerçek ölçümle karşılaştırılamadı**. Bu yüzden AC7 Kısmen.

## 14. Sınırlılıklar ve geçerlilik tehditleri
- **LLM üretimi engellendi:** Katman B'de üç yöntem karşılaştırılamaz. PATCH metodu LLM tarafından hiçbir
  katmanda temsil edilmez. Bu nedenle AC3 Kısmen.
- **Döngüsellik riski:** Katman B'nin hedef uygulaması, ground truth'u ve senaryoları aynı ekip tarafından
  hazırlandı. Kural tabanlı üretici de şablon tabanlı olduğundan F1 = 1.00 küçük (n = 17, 3 pozitif) ve
  kontrollü bir kümeye aittir. **Genellenemez.**
- **Geliştirme kümesi:** sonuçlar nihai performans değildir. Bağımsız değerlendirme için H3-06 hattı ve
  mühürlü test kümesi korunmuştur.
- **Önceden var olan sızıntı riski (Katman A):** H3-04 `planner.py`/`codegen.py`, `is_known_flaw` alanını okur.
  Dev kümesinde kusur olmadığı için Katman A etkilenmez. Katman B'de etiket maskeli görünüm verildi.
- Katman A LLM çıktıları arşivdir; bugünkü model davranışını temsil etmeyebilir.
- Önceden var olan bulgu: H3-05 `generation_report.json` içinde mutlak bir Windows yolu bulunuyor. H5-05'te
  değiştirilmedi.

## 15. Yeniden üretim ve H5-06 devri
```bash
python -m experiments.h5_05_hybrid_experiment verify          # Katman B dondurma kontrolü
python -m experiments.h5_05_hybrid_experiment run [--layer A|B] [--resume]
python -m pytest -p no:cacheprovider experiments/h5_05_hybrid_experiment/tests
```
LLM adımını tamamlamak için gereken: geçerli Groq anahtarı ve `api.groq.com` erişimi. Ardından:
```bash
python -m agent.test_generation.llm generate \
  --endpoints experiments/h5_05_hybrid_experiment/layer_b/endpoint_summary.json \
  --ground-truth experiments/h5_05_hybrid_experiment/layer_b/generator_inputs/reference_requirements.json \
  --scenarios experiments/h5_05_hybrid_experiment/layer_b/generator_inputs/scenarios.json \
  --out experiments/h5_05_hybrid_experiment/layer_b/generated/llm/generated_tests \
  --raw experiments/h5_05_hybrid_experiment/layer_b/generated/llm/raw_responses \
  --reports experiments/h5_05_hybrid_experiment/layer_b/generated/llm/reports \
  --prompts-sent experiments/h5_05_hybrid_experiment/layer_b/generated/llm/prompts_sent
```
`generation_report.json` oluştuğunda `runner._layer_b` LLM adaylarını otomatik kullanır (durum `GENERATED`); ardından `run` yeniden koşulur. H5-06 devir
paketi: `reports/h5_06_handoff.json`.
