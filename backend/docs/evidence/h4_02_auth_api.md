# H4-02 | Kimlik Doğrulama ve Yetkilendirme — API ve Kanıt (Issue #34)

SimpleJWT giriş/yenileme/çıkış, django-axes (H4-01 #33) kilidine entegre; e-posta ile şifre sıfırlama;
proje sahipliği bazlı yetkilendirme. Kaynak: [`core/auth/`](../../core/auth/). Aşağıdaki davranışların
tamamı otomatik API testleriyle doğrulanmıştır: `core/tests/test_auth_api.py` (16),
`core/tests/test_permissions.py` (9).

## Uç noktalar (`/api/auth/`)

| Metot + yol | Açıklama | Yetki |
|---|---|---|
| `POST /api/auth/login/` | Kullanıcı adı+parola → access/refresh token | Açık |
| `POST /api/auth/refresh/` | Refresh → yeni access (refresh rotasyonu + blacklist) | Açık |
| `POST /api/auth/logout/` | `{refresh}` → refresh token'ı blacklist'e alır | Kimlik doğrulamalı |
| `GET  /api/auth/me/` | Oturumdaki kullanıcının temel bilgileri | Kimlik doğrulamalı |
| `POST /api/auth/password-reset/` | `{email}` → sıfırlama bağlantısı gönderir (genel yanıt) | Açık |
| `POST /api/auth/password-reset/confirm/` | `{uid, token, new_password}` → parolayı günceller | Açık |

## Yapılandırma (settings)

- `INSTALLED_APPS`: `rest_framework_simplejwt`, `rest_framework_simplejwt.token_blacklist`.
- `REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES`: `JWTAuthentication`.
- `SIMPLE_JWT`: access `JWT_ACCESS_MINUTES` (vars. 15 dk), refresh `JWT_REFRESH_DAYS` (vars. 7 gün),
  `ROTATE_REFRESH_TOKENS`, `BLACKLIST_AFTER_ROTATION`, `UPDATE_LAST_LOGIN`.
- E-posta: `EMAIL_BACKEND` (vars. konsol; test locmem), `DEFAULT_FROM_EMAIL`,
  `FRONTEND_PASSWORD_RESET_URL`, `PASSWORD_RESET_TIMEOUT` (vars. 3600 sn).
- İstek sınırı: `DEFAULT_THROTTLE_RATES["login"]` (vars. `10/min`).
- Kilit politikası H4-01'de tanımlı (`AXES_FAILURE_LIMIT=3`, `AXES_COOLOFF_TIME=15 dk`, kullanıcı bazında).
  Token süreleri/kilit parametreleri H4-06 (#38) ile ortam değişkenlerinden tam yapılandırılabilir olacaktır.

## Örnek istek–yanıtlar (testlerle doğrulanmış davranış)

**Başarılı giriş**
```
POST /api/auth/login/   {"username": "merve", "password": "<parola>"}
200 OK   {"access": "<jwt>", "refresh": "<jwt>"}
```

**Hatalı parola / bilinmeyen kullanıcı** (hesap varlığı ifşa edilmez)
```
POST /api/auth/login/   {"username": "merve", "password": "yanlis"}
401 Unauthorized   {"detail": "No active account found with the given credentials"}
```

**Hesap kilidi** — üçüncü başarısız denemede kilit; kilit süresince doğru parola da reddedilir
```
POST /api/auth/login/  (1. yanlış) → 401
POST /api/auth/login/  (2. yanlış) → 401
POST /api/auth/login/  (3. yanlış) → 429  {"detail": "... Hesap geçici olarak kilitlendi ...", "code": "account_locked"}
POST /api/auth/login/  (doğru parola, kilit süresinde) → 429
# 15 dk sonra (cooloff) → 200. Başarılı giriş başarısız deneme sayacını sıfırlar.
```

**Oturum bilgisi**
```
GET /api/auth/me/   Authorization: Bearer <access>
200 OK   {"id": 1, "username": "merve", "email": "merve@example.test"}
# Token yoksa 401; geçersiz token 401.
```

**Çıkış (blacklist)**
```
POST /api/auth/logout/   Authorization: Bearer <access>   {"refresh": "<refresh>"}
205 Reset Content
# Sonrasında aynı refresh ile /refresh/ → 401 (blacklist).
```

**Şifre sıfırlama talebi** (kayıtlı ve kayıtsız e-posta için aynı genel yanıt)
```
POST /api/auth/password-reset/   {"email": "merve@example.test"}
200 OK   {"detail": "E-posta kayıtlıysa şifre sıfırlama bağlantısı gönderildi."}
# Kayıtlıysa e-posta gönderilir; link: FRONTEND_PASSWORD_RESET_URL?uid=<uid>&token=<token>
```

**Yeni parola belirleme**
```
POST /api/auth/password-reset/confirm/   {"uid": "<uid>", "token": "<token>", "new_password": "<yeni>"}
200 OK   {"detail": "Parola güncellendi."}
# Geçersiz/süresi dolmuş/tekrar kullanılmış bağlantı → 400 (genel hata). Parola değişince eski bağlantı geçersizdir.
```

## Yetkilendirme (proje sahipliği)

- `core/auth/permissions.py`: `IsProjectOwner`, `owned_queryset`, `OwnedQuerysetMixin`. Sahiplik tüm
  modellerde `Project.owner` zincirinden türetilir (AnalysisRun, ReferenceRequirement, GeneratedTest,
  TestExecution, SecurityFinding, Endpoint, Report, LlmCall).
- Queryset kullanıcıya göre filtrelendiğinden **başkasına ait kayıt 404** döner (bilgi sızdırmaz);
  nesne bulunup sahiplik başarısız olursa **403**. Bu altyapı H4-03/H4-04 (#35/#36) view'larında kullanılır.

## Güvenlik kontrolleri

- Parola, JWT token, `SECRET_KEY`, sıfırlama token'ı API yanıtlarında ve loglarda yer almaz
  (`test_sensitive_data_not_in_responses`).
- Korumalı uçlar anonim ve geçersiz token ile kapalı; HTTP hata yanıtları tutarlı.
- Giriş kilidi + temel istek sınırı (İST-10) birlikte uygulanır; kilit kullanıcı bazındadır.
