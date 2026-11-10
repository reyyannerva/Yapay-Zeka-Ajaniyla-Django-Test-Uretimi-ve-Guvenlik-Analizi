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
