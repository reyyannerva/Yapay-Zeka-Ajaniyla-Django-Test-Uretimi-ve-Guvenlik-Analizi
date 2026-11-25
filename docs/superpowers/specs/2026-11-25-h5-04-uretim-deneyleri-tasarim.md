# H5-04 (#42) — Kural Tabanlı ve LLM Tabanlı Test Üretimi Deneyleri — Tasarım Dokümanı

**Tarih:** 2026-11-25
**Issue:** #42 — H5-04 | Kural Tabanlı ve LLM Tabanlı Test Üretimi Deneylerinin Gerçekleştirilmesi
**Sahip:** Merve Çaloğlu (mervecaloglu) — _takas kararı: GitHub'da #42 Reyyan'a atalı; sözlü karar gereği #42 Merve'nin, #41 Reyyan'ın. Atamalar GitHub'da güncellenecek._
**Durum:** Taslak — onay bekliyor (henüz kod yazılmadı, commit edilmedi)

---

## 1. Amaç ve gerekçe (niçin)

Proje, kural tabanlı (H3-04/#30) ve Groq LLM tabanlı (H3-05/#31) Pytest üretimi olmak üzere iki
yaklaşım geliştirdi. #32 (H3-06) bu ikisini **bağımsız/mühürlü test kümesinde** (18 senaryo)
güvenlik tespiti açısından değerlendirdi (TP/FP/TN/FN, P/R/F1).

#42 bundan **ayrı ve tamamlayıcı** bir deneydir: iki yaklaşımı **geliştirme kümesinde** (20 senaryo)
karşılaştırmalı çalıştırıp **üretim kalitesi ve çalıştırılabilirlik** boyutunu belgelemek, ve bunu
#43'teki (H5-05) metrik analizi/karşılaştırma tablosu için **tekrarlanabilir, yapılandırılmış bir
deney veri kümesine** dönüştürmek.

**Neden geliştirme kümesi?** Mühürlü test kümesi, nihai/dürüst değerlendirme için saklanır (veri
sızıntısı önlemi, bkz. `benchmarks/reference_cases/split.md`). Geliştirme-fazı deneyleri bu küme
üzerinde yapılmaz. #42, issue'nun açık talebine uygun olarak yalnızca geliştirme kümesini kullanır.

## 2. Çözülen tasarım çelişkisi (önemli)

Issue iki şey ister: (a) yalnızca geliştirme kümesini kullan, (b) GET/POST/PUT/PATCH/DELETE
hepsini temsil et.

**Gerçek kapsam (uygulama sırasında manifestten doğrulandı, 2026-11-26):** Geliştirme kümesinde
(20 senaryo) metot dağılımı **GET: 9, POST: 9, PUT: 1, DELETE: 1, PATCH: 0**. Ancak buradaki tek
PUT (SC-MNA-002) ve tek DELETE (SC-MNA-001) **method-not-allowed (405)** senaryolarıdır — yani
gerçek güncelleme/silme (2xx/4xx) işlemlerini temsil etmezler. **Gerçek PUT/PATCH/DELETE
güncelleme/silme işlemleri ve 3 bilinen güvenlik açığının tamamı mühürlü test kümesindedir;
geliştirme kümesinde PATCH hiç yoktur.** (Not: ilk taslaktaki "dev yalnızca GET+POST içerir"
ifadesi hatalıydı; bu bölüm gerçek veriyle düzeltilmiştir.)

**Karar (kullanıcı onayı, 2026-11-25, Seçenek A):** #42 geliştirme kümesinde yürütülür; 5 metodun
tam resmi ve güvenlik açığı tespiti için **#32'nin mühürlü-küme sonuçlarına açıkça atıf yapılır**.
Böylece "geliştirme deneyi" (#42, betimleyici: üretim + çalıştırılabilirlik) ile "mühürlü
değerlendirme" (#32, nihai güvenlik metriği) arasında net bir duvar korunur ve sızıntı oluşmaz.
Proje bütününde 5 metot da, güvenlik açıkları da dürüstçe kapsanmış olur.

Bu çelişki ve çözümü, #42 issue metnine de yansıtılacaktır (ayrı, küçük bir düzenleme; §9).

## 3. Hedefler

1. **Dev deney manifesti:** `split.json`'daki 20 geliştirme senaryosu; #32'deki gibi girdi
   SHA-256 özetleri + sürüm bilgisiyle **dondurulmuş** (tekrarlanabilirlik, sessiz değişime karşı).
2. **İki yaklaşımın ortak girdilerle üretimi:** Aynı AST/endpoint özeti, bağımsız referans gereksinim
   JSON'u ve senaryo girdileri; yönteme özgü farklar (prompt vb.) belgelenir.
   - Kural tabanlı: deterministik; `agent.test_generation.rule_based` **değiştirilmeden** çağrılır.
   - LLM: **donmuş h3_05 çıktıları** yeniden kullanılır (model=`groq/openai/gpt-oss-120b`,
     prompt=`pytest_v1`, temperature=0.0). Groq'a yeni istek gönderilmez.
3. **Üretim kalitesi:** Her iki yaklaşımda üretilen Python/Pytest kodunun **sözdizimi geçerliliği**
   ve **pytest toplanabilirliği** kontrol edilir; geçersizler ve nedenleri kaydedilir.
4. **Çalıştırılabilirlik:** Geçerli testlerin kontrollü ortamda çalıştırılabilirliği doğrulanır;
   **ortam kaynaklı hatalar üretim hatalarından ayrı** kaydedilir.
5. **Sonuç sınıflandırması:** Senaryo başına **PASS / FAIL / ERROR / TIMEOUT** ayrı ayrı
   (kanonik `TestExecution` enum'una uygun; ERROR ≠ TIMEOUT); testin çalıştırılabilir olması ile
   hedef uygulamanın testi geçmesi **karıştırılmaz**.
6. **Yapılandırılmış sonuç:** Senaryo kimliği, üretim yöntemi, HTTP metodu, üretilen test sayısı,
   sözdizimi durumu, toplanma, çalıştırılabilirlik sonucu, hata türü ve yürütme çıktısı özeti ile
   **JSON + CSV** çıktı; ayrıca okunur **Markdown** karşılaştırma. Alan şeması #43'te doğrudan
   kullanılabilir olacak.
7. **Tekrarlanabilirlik belgesi:** model/prompt/kural sürümü, veri kümesi sürümü, bağımlılıklar,
   çalıştırma komutları; **gizli anahtar kayıtlara girmez.**
8. **Gerçek testler:** Yeni orkestrasyon/manifest/raporlama kodu için birim testleri (TDD).

## 4. Hedef olmayanlar (non-goals)

- Mühürlü test kümesinde (18 senaryo) değerlendirme — bu #32'nin işidir; #42 ona **dokunmaz**.
- Güvenlik tespiti metriği (TP/FP/TN/FN, P/R/F1) hesaplamak — geliştirme kümesinde bilinen açık
  yoktur; bu metrik #32'de (mühürlü küme) ve #43'te ele alınır. #42 betimleyici kalır.
- Canlı LLM yeniden üretimi / yeni model denemesi.
- Üretici veya değerlendirici modüllerinin davranışını değiştirmek (bkz. §6 ekip sınırı).
- Onarım/yeniden üretim mekanizması (bu H6-04/#48 kapsamıdır); #42 "ilk geçiş" çıktısını kullanır.

## 5. Anti-hedefler (başarısızlık sayılacak sonuçlar)

- Çalıştırılmamış bir testi "başarılı" raporlamak veya metrik uydurmak.
- Geliştirme ve test kümesi arasında sızıntı oluşturmak (test kümesi senaryolarını #42'ye katmak).
- Ground truth / beklenen güvensiz davranışı LLM prompt'una sızdırmak (zaten #31'de engellenmiş;
  yeniden üretim yapılmadığı için bu deneyde ek risk yok, yine de doğrulanır).
- Reyyan'ın dosyalarını (#30, #32 kodu) değiştirmek.

## 6. Kısıtlar

- **Ekip sınırı (CLAUDE.md):** `agent/test_generation/rule_based/**` (#30) ve `agent/evaluation/**`
  (#32) Reyyan'ın kodudur; **değiştirilmez**, yalnızca içe aktarılıp (kütüphane) çağrılır.
  `agent/test_generation/llm/**` (#31) Merve'nindir; gerekirse düzenlenebilir ama bu deneyde
  yeniden kullanım yeterli, değişiklik öngörülmüyor.
- **Kanonik veri modeli:** Sonuç alanları `docs/database/data_dictionary.md` ile tutarlı
  (`TestExecution`: PENDING/RUNNING/PASS/FAIL/ERROR/TIMEOUT/STOPPED/NOT_RUN).
- **Veri bütünlüğü:** Girdi dosyaları SHA ile sabitlenir; sonuç dosyaları deterministik yazılır.
- **Sırlar:** Yalnızca `.env`; koda/log/rapora anahtar yazılmaz.
- **Platform:** Windows; mevcut deneyler `uv` + Python 3.11 ile çalışıyor (bkz. kalıcı not).
  Çalıştırma komutları Windows'ta doğrulanır.
- **Git:** Yalnızca bu issue'nun dosyaları; `feat/h5-04-uretim-deneyleri` branch'i, güncel main'den.

## 7. Değerlendirilen yaklaşımlar

**Y1 — `agent/evaluation` harness'ını dev manifestini kabul edecek şekilde genişletmek.**
En az kod tekrarı; tek harness. _Ret:_ #32 (Reyyan) kodunu değiştirmek gerekir → ekip sınırı ihlali.

**Y2 — Bağımsız #42 deney paketi; Reyyan'ın modüllerini salt-okunur kütüphane olarak kullanmak.
(SEÇİLEN)** Yeni kod `experiments/h5_04_generation_experiment/` altında; dev manifesti + orkestrasyon
+ dev'e özgü raporlama #42 tarafında yazılır, ağır iş (`execution` sınıflandırma, isol: `pytest_probe`,
`reporting` yardımcıları) `agent.evaluation`'dan **import** edilerek yeniden kullanılır; üretim için
mevcut üretici CLI/API'leri çağrılır. _Artı:_ ekip sınırına tam uyum, yüksek yeniden kullanım, #32
ile aynı metodoloji ve kalite çıtası, ucuz (LLM yeniden üretimi yok). _Eksi:_ ince bir orkestrasyon
katmanı yazılır; `agent.evaluation` adaptörlerinin dev senaryolarını da eşleyebildiği
**doğrulanmalıdır** (bkz. §8, ilk adım).

**Y3 — Mevcut CLI'leri elle çalıştırıp sonuçları manuel birleştirmek.** _Ret:_ tekrarlanabilir
ve profesyonel değil; hata/uydurma riski.

## 8. Uygulama planına bırakılanlar (how — builder'a)

1. **Fizibilite doğrulaması (ilk adım):** `agent/evaluation/artifacts.py` içindeki `ADAPTERS`'ın,
   dev senaryo kimliklerini mevcut üretilmiş testlere (kural tabanlı h3_04 metot-dosyaları;
   LLM h3_05 `test_sc_*.py`) eşleyip eşleyemediğini doğrula. Eşleyemiyorsa: kural tabanlı testleri
   `rule_based` üreticisini (değiştirmeden) `--out experiments/h5_04.../generated/rule_based` ile
   yeniden üreterek ve/veya dev'e özgü ince bir adaptör yazarak çöz. Hangi yolun seçildiği planda
   netleşir. (Küçük bir spike uygun olabilir.)
2. **Dev manifesti:** 20 dev senaryosu; her biri için scenario_id, http_method, user_role,
   (varsa) expected secure_status, is_known_flaw=false; girdi dosyalarının SHA-256'sı; üretici/model/
   prompt/kural sürümleri. Donmuş dosya + doğrulama fonksiyonu (#32 manifestini örnek al).
3. **Orkestrasyon:** her baseline için dev senaryolarının testlerini topla → sözdizimi/toplanma
   ön kontrolü → yalıtılmış çalıştırma + sınıflandırma (`agent.evaluation.execution` yeniden kullanımı)
   → satır üret.
4. **Raporlama:** `results.json` (ham), `metrics.csv`/`per_scenario.csv` benzeri CSV, `comparison.md`;
   #43'ün ihtiyaç duyacağı alanlar netleştirilip şema sabitlenir. #32'ye atıf bölümü eklenir.
5. **Dizin yapısı:** `experiments/h5_04_generation_experiment/{README.md, manifest.json,
   results/, (gerekirse) generated/}` + orkestrasyon kodu (paket) + `tests/`.
6. **Testler (TDD):** manifest doğrulama, sınıflandırma eşleme, raporlama determinizmi, sızıntı-yok
   kontrolü (dev ∩ test = ∅).
7. **Dokümantasyon:** README (çalıştırma komutları, ortam, sürümler, sınırlılıklar: "LLM çıktısı
   H3-05'ten yeniden kullanıldı", "PUT/PATCH/DELETE ve güvenlik açıkları mühürlü kümede #32'de").

## 9. Issue metni düzeltmesi (ayrı, küçük)

#42 metnindeki iki nokta gerçekle hizalanacak (ayrı küçük düzenleme, kullanıcı onayıyla):
- Model adı "Llama 3.3 70B" → fiilen kullanılan `groq/openai/gpt-oss-120b`.
- "5 metot" ↔ "yalnızca geliştirme kümesi" çelişkisi: §2'deki çözüm (dev kümesi + #32 atfı) yazılır.

## 10. Kabul / kanıt

- `experiments/h5_04_generation_experiment/` altında çalışan, tekrarlanabilir deney; tek komutla
  üretilen deterministik JSON/CSV/MD sonuçlar.
- Yeni kodun birim testleri **gerçekten çalıştırılıp** geçtiği gösterilir (çıktı paylaşılır).
- Dev kümesi 20 senaryo; GET/POST/method-not-allowed temsil; PUT/PATCH/DELETE için #32'ye atıf.
- Sonuç alanları #43 için hazır; sızıntı-yok ve sır-yok doğrulanmış.
- Branch + (onayla) commit/PR; Türkçe conventional-commit.
