# H5-03 / #41 gerçek uçtan uca testleri

Gerçek Chromium + Vite frontend + Django/DRF + PostgreSQL + yerel SMTP yakalayıcı ile çalışır. API
taklit edilmez. Senaryolar:

- Ana akış (Issue #41, 25 adım): giriş, yükleme, CRUD, analiz, referans JSON, çıkış, ikinci kullanıcı
  izolasyonu, silme.
- Access süresi dolumu ve refresh.
- Sunucuda iptal edilen refresh.
- Hesap kilidi.
- Şifre sıfırlama (SMTP).
- Bağlantı kesintisi ve yeniden başlatma sonrası kalıcılık.
- 5 genişlikte taşma kontrolü.

```bash
pip install aiosmtpd            # yalnızca test yakalayıcısı için
bash e2e/h5-03/run.sh           # backend/.env PostgreSQL bağlantısı gerekir
```

| Dosya | Görev |
| --- | --- |
| `run.sh` | Fixture, kullanıcı, SMTP yakalayıcı ve Vite'i başlatır; `run_e2e.cjs`'i çalıştırır. |
| `run_e2e.cjs` | Senaryolar. Backend'i kendisi başlatıp durdurur. Ekran görüntülerini `docs/mockup/h5-03/`, sonuçları `docs/integration/h5-03/` altına yazar. |
| `create_test_users.py` | `e2e_kullanici_a/b/c` hesaplarını rastgele parolayla oluşturur; parolalar yalnızca geçici dosyada (0600) tutulur. |
| `db_probe.py` | PostgreSQL'i ORM ile sorgular. Yalnızca `e2e_` kullanıcıları için kilit süresinin dolmasını, refresh iptalini ve analizin sonlanmasını simüle eder. |
| `smtp_catcher.py` | 127.0.0.1:1025 SMTP sunucusu; e-postaları `.eml` olarak yazar, dışarı iletmez. |
| `make_fixtures.py` | Geçerli/bozuk ZIP ve geçerli/geçersiz referans JSON örnekleri. |

Yalnızca test süreci için kullanılan ayarlar (üretim varsayılanları değişmez):

- `JWT_ACCESS_MINUTES=1`: token yenileme gerçek süre dolumuyla test edilir.
- `LOGIN_THROTTLE_RATE=200/min`: tek IP'den çok sayıda test girişi yapılabilir. Kilit politikası
  değişmez (3 deneme / 15 dk).
- SMTP: e-postalar `127.0.0.1:1025`'teki yerel yakalayıcıya gider.

Betik, oluşturduğu test projelerini sonda siler.
