# Geliştirme/Test Ayrımı ve Ground Truth Yöntemi (H3-03 / Issue #29)

Bu belge; bağımsız test kümesinin nasıl ayrıldığını, veri sızıntısının nasıl önlendiğini,
ground truth (altın etiket) referanslarının nasıl **bağımsız** hazırlandığını ve etiket
anlamlarını tanımlar.

**Kaynak:** `benchmarks/drf_fixtures/scenarios/scenarios.json` (#27, 38 senaryo).

## 1. Ayrım yöntemi (aile bazlı)

Senaryolar önce davranışsal **ailelere** gruplanır. **Bir aile asla iki gruba bölünmez** —
böylece benzer senaryo ailesinin hem geliştirme hem test kümesinde bulunmasından kaynaklanacak
**veri sızıntısı** önlenir. Ayrım `split.json` içinde sabittir; `test_set.json` bağımsız test
kümesini (yalnızca senaryo ID'leri) sabitler.

| Aile | Grup | Senaryolar |
|---|---|---|
| F-LIST | dev | SC-LST-001..003 |
| F-RETRIEVE | dev | SC-RET-001..006 |
| F-CREATE | dev | SC-CRT-001,002 · SC-INP-001,002,004 · SC-AUT-001 |
| F-PUBLISH | dev | SC-PUB-001 · SC-AUZ-004 · SC-AUT-005 |
| F-METHOD | dev | SC-MNA-001,002 |
| **F-UPDATE** | **test** | SC-UPD-001..004 · SC-AUZ-001,002 · SC-AUT-002,003 · SC-INP-003 · SC-NF-001 |
| **F-DELETE** | **test** | SC-DEL-001,002 · SC-AUZ-003 · SC-AUT-004 · SC-NF-002 |
| **F-FLAW** | **test** | SC-FLW-001,002,003 |

**Dev = 20, Test = 18.** Bağımsız test kümesi, değerlendirme odağıyla uyumlu olacak şekilde
**değiştiren işlemleri (PUT/PATCH/DELETE), kaynak sahipliği/yetki senaryolarını ve bilinen
güvenlik hatalarını** vurgular (güvenlik tespiti F1'i bu küme üzerinden ölçülür). Ground truth
ise **tüm 38 senaryoyu** kapsar (5 HTTP metodu da temsil edilir); dev/test yalnızca değerlendirme
ayrımıdır.

## 2. Veri sızıntısı önlemi

- İlişkili senaryolar (ör. aynı kaynak üzerinde PUT ve PATCH, ya da bir hatanın güvenli/güvensiz
  muadili) **aynı ailede** tutulur; aile tek gruba atanır.
- `check_references.py`, her ailenin tek grupta olduğunu ve dev ∪ test = tüm senaryolar, dev ∩ test
  = ∅ olduğunu mekanik olarak doğrular.

## 3. Ground truth'un bağımsızlığı

Altın etiketler **model çıktısından** ve **hedef uygulamanın gözlemlenen (bazen hatalı)
davranışından bağımsız** tanımlanır:

- Hatasız senaryolarda beklenen güvenli durum, Django/DRF semantiği ve fixture tasarımından
  türetilir (uygulama zaten doğru davrandığı için gözlemle örtüşür).
- **Bilerek-hatalı senaryolarda** ground truth **beklenen GÜVENLİ** davranışı kaydeder; bu,
  uygulamanın güvensiz uçta ürettiği davranıştan **ayrı alanlarda** gösterilir
  (`expected_result.secure_status` vs `security_finding.observed_flawed_status`).

`tests/test_ground_truth_crosscheck.py` bunu kanıtlar: hatasızlarda uygulama = altın güvenli durum;
hatalılarda uygulama altın durumdan **sapar** (durum veya içerik bazında).

## 4. Etiket anlamları

- **label = positive:** güvenli davranışta işlem **izinli** sonuçlanır (2xx).
- **label = negative:** güvenli davranışta işlem **engellenir** (4xx).
- Etiket, `expected_result.secure_status` sınıfından türetilir (model/uygulama çıktısından değil).

### 4.1 İki veri kümesindeki `label` alanları farklı şeyleri ölçer (denetim bulgusu D-04)

| Alan | Dosya | Anlamı | Türetildiği değer |
|---|---|---|---|
| `label` | `benchmarks/drf_fixtures/scenarios/scenarios.json` (H3-01) | Senaryonun **beklenen sonuç sınıfı**: `positive` = isteğin başarılı (2xx) olması beklenir; `negative` = istek reddedilir (4xx) **veya** senaryo bilerek-güvensiz uçta gözlenen hatalı davranışı temsil eder (`is_intentional_flaw: true`) | `expected_http_status` (bilerek-hatalı senaryolarda güvensiz uçta **gözlenen** kod) |
| `label` | `ground_truth.json` (H3-03) | **Güvenli davranışın** sonuç sınıfı: `positive` = güvenli sistemde işlem izinli (2xx); `negative` = güvenli sistemde işlem engellenir (4xx) | `expected_result.secure_status` |

İki alan 38 kaydın 37'sinde aynıdır. Tek fark **SC-FLW-003**'tür:

- `GET /api/insecure/articles/` (anonim). Güvenli beklenti: 200 ve yalnızca yayınlanan kayıtlar → ground
  truth `positive`.
- H3-01 aynı senaryoyu bilerek-hatalı olduğu için `negative` etiketler; gözlenen durum kodu da 200'dür,
  sapma **içerik** düzeyindedir (taslaklar ifşa edilir, `deviation_kind: content`).
- SC-FLW-001 ve SC-FLW-002 her iki dosyada `negative`tir: H3-01'de kusur nedeniyle, ground truth'ta
  güvenli beklenti 403 olduğu için.

Her iki etiket kendi tanımına göre doğrudur; kanonik veri kümeleri **yeniden etiketlenmemiştir**.
Sayılar: H3-01 15 pozitif / 23 negatif; H3-03 16 pozitif / 22 negatif.

### 4.2 Hangi alan ne için kullanılır

| Amaç | Kullanılacak alan |
|---|---|
| Üretilen testin beklediği HTTP durum kodu | `ground_truth.json` → `expected_result.secure_status` |
| Bilerek-hatalı uçta gözlenen (güvensiz) davranış | `security_finding.observed_flawed_status`, `deviation_kind` |
| Güvenlik tespiti değerlendirmesindeki **gerçek sınıf** | `is_known_flaw` (+ `security_finding`) |
| İstek izinli mi / engelli mi (yetkilendirme kapsamı analizi) | `ground_truth.json` → `label` |

`label` alanlarının hiçbiri güvenlik kusuru sınıfı değildir: `negative`, "güvenli sistemde istek reddedilmeli"
anlamına gelir (ör. SC-AUT-002 negatif ama kusursuzdur).

### 4.3 H3-06 için TP / FP / TN / FN tanımı (önerilen)

- **Değerlendirme birimi:** bağımsız test kümesindeki (`test_set.json`) her senaryo için üretilen test.
- **Pozitif gerçek sınıf:** `is_known_flaw = true` (senaryoda bilinen güvenlik kusuru var).
- **Pozitif tahmin:** sözdizimi geçerli ve çalıştırılabilir test, ground truth'taki güvenli beklentiyi ihlal
  eden davranışı yakaladı (test FAIL; durum kodu veya yan etki doğrulaması, bkz. H3-04 `check=status|side_effect`).

| | Kusur var (`is_known_flaw = true`) | Kusur yok (`is_known_flaw = false`) |
|---|---|---|
| Geçerli test FAIL | **TP** (H3-04: `KNOWN_FLAW_DETECTED`) | **FP** (H3-04: `APPLICATION_MISMATCH`) |
| Geçerli test PASS | **FN** (H3-04: `KNOWN_FLAW_NOT_DETECTED`) | **TN** (H3-04: `PASSED`) |
| Test üretilemedi / teknik hata | **FN** (kusur tespit edilmemiştir) | Güvenlik matrisine katılmaz; çalıştırılabilirlik metriğinde raporlanır |

Kurallar:

1. `label` alanları TP/FP/TN/FN için **kullanılmaz**.
2. Teknik hatalar (`GENERATION_ERROR`, `ENVIRONMENT_ERROR`, sözdizimi geçersiz test) "ilk geçişte
   çalıştırılabilir test oranı" metriğinde ayrıca raporlanır; kusursuz bir senaryodaki teknik hata FP sayılmaz.
3. İçerik düzeyi kusurlar (SC-FLW-003) yalnızca durum kodu doğrulayan bir testle yakalanamaz; böyle bir
   test PASS olursa sonuç **FN**'dir.
4. Örneklem küçüktür: test kümesinde 18 senaryo, bunlardan 3'ü kusurlu (2 durum kodu, 1 içerik sapması).
   Test kümesi POST ve 405 senaryosu içermez; bu, metrik sonuçlarının kapsam sınırı olarak raporlanmalıdır.

## 5. Referans kaynakları ve doğrulama durumu

- `reference_source`: `DRF_SEMANTICS` (standart Django/DRF davranışı), `FIXTURE_DESIGN`
  (kontrollü fixture tasarımı — ör. taslak görünürlüğü), `PROJECT_REQUIREMENT` (projenin
  güvenlik gereksinimi — bilerek-hatalı senaryoların güvenli beklentisi).
- `validation_status`: `verified` veya `uncertain`. Kontrollü ortam olduğundan beklentiler
  belirsizlik içermez; **0 uncertain**. Belirsiz durumlar çıkarsa ayrı işaretlenir ve doğrulanmış
  etiketlerle karıştırılmaz (`check_references.py` ayrı raporlar).

## 6. Sabitleme (bütünlük)

`INTEGRITY.txt`, `test_set.json` ve `ground_truth.json` için SHA-256 özetleri tutar;
`check_references.py` bunları doğrular. Böylece bağımsız test kümesi ve altın etiketler
değerlendirme sonuçlarına göre sessizce değiştirilemez.

## 7. Bilinen güvenlik bulguları (altın)

| Senaryo | Bulgu türü | Konum | Güvenli beklenti | Gözlemlenen (güvensiz) |
|---|---|---|---|---|
| SC-FLW-001 | BOLA/IDOR (OWASP API1:2023) | `/api/insecure/articles/<pk>/` (PUT) | 403 | 200 |
| SC-FLW-002 | BOLA/IDOR (OWASP API1:2023) | `/api/insecure/articles/<pk>/` (DELETE) | 403 | 204 |
| SC-FLW-003 | Hassas veri ifşası | `/api/insecure/articles/` (GET) | 200, taslaklar gizli | 200, taslaklar ifşa |

İlgili isterler: İST-03, İST-04, İST-06, İST-15, İST-16.
