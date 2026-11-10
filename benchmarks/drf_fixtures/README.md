# Kontrollü Django/DRF Fixture ve Senaryo Veri Kümesi (H3-01 / Issue #27)

AI test ajanının üzerinde test üreteceği **kontrollü bir Django/DRF hedef uygulaması** ve
beklenen sonuçları önceden tanımlı **30–40 senaryoluk etiketli veri kümesi**.

- Bu uygulama bir **değerlendirme hedefidir**; projenin ürün backend'i (Hafta 4) değildir.
- **PyGoat'tan ayrıdır** (PyGoat vendored edilmez; ayrı bir değerlendirme hedefidir).
- Bilerek eklenen güvenlik hataları `sample_app/catalog/insecure.py` içinde **ayrı ve işaretli**
  tutulur; veri kümesinde `is_intentional_flaw: true` ile gösterilir.

## Dizin yapısı

```
benchmarks/drf_fixtures/
├── sample_app/                 Çalıştırılabilir kontrollü Django/DRF uygulaması
│   ├── config/                 settings, urls, wsgi (SQLite, tek ayar)
│   ├── catalog/
│   │   ├── models.py           Article(owner, title, body, is_published, created_at)
│   │   ├── serializers.py      Girdi doğrulama (400) kaynağı
│   │   ├── permissions.py      IsOwnerOrAdminOrReadOnly (GÜVENLİ kural)
│   │   ├── views.py            GÜVENLİ uçlar: ViewSet + publish APIView
│   │   ├── insecure.py         BİLEREK GÜVENSİZ uçlar (ayrı/işaretli)
│   │   ├── urls.py
│   │   ├── fixtures/           users.json, articles.json (roller + kayıtlar)
│   │   └── migrations/
│   ├── tests/                  Smoke + senaryo-eşleşme testleri (doğrulama)
│   ├── manage.py, pytest.ini, conftest.py, requirements.txt
├── scenarios/
│   ├── scenarios.json          KANONİK etiketli veri kümesi (38 senaryo)
│   ├── scenarios.schema.json   JSON Schema
│   └── scenarios.csv           JSON'dan türetilmiş (EDA/okunurluk için)
└── scripts/
    ├── validate_scenarios.py   Şema + tutarlılık doğrulaması
    └── export_scenarios_csv.py JSON -> CSV
```

## Kurulum ve çalıştırma

```bash
cd benchmarks/drf_fixtures/sample_app
python -m venv .venv && source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata users articles
python manage.py runserver
```

Örnek istek (yayınlanmış kayıt, anonim):
```bash
curl -i http://127.0.0.1:8000/api/articles/1/        # 200
curl -i -X DELETE http://127.0.0.1:8000/api/articles/1/   # 401 (anonim)
```

> Manuel kimlik doğrulamalı deneme için fixture kullanıcılarının parolası `!` (kullanılamaz)
> olarak ayarlıdır; gerekirse `python manage.py changepassword alice`. Testler
> `force_authenticate` kullandığından parola gerektirmez.

## Uç noktalar ve roller

| Uç nokta | Metotlar | Kural |
|---|---|---|
| `/api/articles/` | GET (list), POST | GET herkese; POST kimlik doğrulama ister |
| `/api/articles/<pk>/` | GET, PUT, PATCH, DELETE | Değiştiren metotlar: sahip veya yönetici |
| `/api/articles/<pk>/publish/` | POST (APIView) | Sahip veya yönetici |
| `/api/insecure/articles/` | GET | **GÜVENSİZ:** taslakları da ifşa eder |
| `/api/insecure/articles/<pk>/` | GET, PUT, PATCH, DELETE | **GÜVENSİZ:** sahiplik kontrolü yok (BOLA) |

Roller (fixture): `admin` (yönetici), `alice`/`bob` (kaynak sahipleri), `carol` (sahip olmayan
kullanıcı), `anonymous` (kimlik yok).

## Senaryo veri kümesi şeması

Her senaryo: `id` · `category` (AUTHENTICATION/AUTHORIZATION/INPUT_VALIDATION/HTTP_BEHAVIOR/
SECURITY_CONFIGURATION) · `http_method` · `endpoint` · `user_role` · `request_input` ·
`expected_http_status` · `expected_behavior` · `label` (positive/negative) · `is_intentional_flaw`
· `flaw_explanation` (hatalıysa) · `fixture_ref` (user, article) · `requirement_refs` (İST-xx).

**Kapsam:** 38 senaryo — GET/POST/PUT/PATCH/DELETE'in tamamı; 200/201/204/400/401/403/404/405;
kimlik doğrulama, rol/kaynak sahipliği, girdi doğrulama; özellikle yetkisiz ve mevcut-olmayan
kaynak üzerinde PUT/PATCH/DELETE; 15 pozitif / 23 negatif; 3 bilerek-hatalı.

## Bilerek eklenen güvenlik hataları

| Senaryo | Hata | Gözlemlenen | Güvenli uçta beklenen |
|---|---|---|---|
| SC-FLW-001 | BOLA/IDOR: sahip olmayan kullanıcı PUT ile başkasının kaydını güncelliyor | 200 | 403 |
| SC-FLW-002 | BOLA/IDOR: sahip olmayan kullanıcı DELETE ile başkasının kaydını siliyor | 204 | 403 |
| SC-FLW-003 | Hassas veri ifşası: liste taslakları herkese döndürüyor | 200 (taslak dâhil) | taslaklar gizli |

Bu hatalar `catalog/insecure.py` içinde izole edilmiştir; **doğru davranışı** `catalog/views.py`
ve `permissions.py` temsil eder.

## Doğrulama

```bash
# 1) Veri kümesi yapısal + tutarlılık doğrulaması
cd benchmarks/drf_fixtures
python scripts/validate_scenarios.py

# 2) Uygulama + senaryo-eşleşme testleri (fixture'ların çalıştığını ve her senaryonun
#    gerçek uygulama davranışıyla eşleştiğini kanıtlar)
cd sample_app
pytest -q        # 67 test: 29 smoke + 38 senaryo-eşleşme

# 3) CSV'yi yeniden üret (opsiyonel)
cd ..
python scripts/export_scenarios_csv.py
```

## Notlar

- SQLite kullanılır; kurulum tek komutla çalışır. `SECRET_KEY` dev amaçlıdır, ortam değişkeninden
  override edilebilir; repoda gerçek sır tutulmaz.
- JSON **kanoniktir**; CSV türetilmiş kopyadır (H3-02 EDA için). Kaynak değişince CSV yeniden üretilir.
- İlgili isterler: İST-01, İST-02, İST-03, İST-04, İST-15, İST-16.
