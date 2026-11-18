# Kimlik Doğrulama ve Parola İşlemleri

Kimlik doğrulama SimpleJWT ile yapılır. Korumalı uç noktalar `Authorization: Bearer <access token>` başlığı
ister; şemada bu `jwtAuth` (http / bearer / JWT) güvenlik şemasıyla gösterilir. Herkese açık işlemler (giriş,
yenileme, şifre sıfırlama talebi/onayı) şemada `security` içermez.

| Ayar | Varsayılan | Ortam değişkeni |
|---|---|---|
| Access token ömrü | 15 dakika | `JWT_ACCESS_MINUTES` |
| Refresh token ömrü | 7 gün | `JWT_REFRESH_DAYS` |
| Refresh rotasyonu / kara liste | açık | — |
| Giriş istek sınırı | 10/dk | `LOGIN_THROTTLE_RATE` |
| Hesap kilidi | 3 başarısız deneme → 15 dakika | — (`AXES_FAILURE_LIMIT`, `AXES_COOLOFF_TIME`) |
| Şifre sıfırlama bağlantı süresi | 3600 sn | `PASSWORD_RESET_TIMEOUT` |

## 1. Giriş — `POST /api/auth/login/`

```json
{"username": "<kullanıcı adı>", "password": "<parola>"}
```

- **200** → `{"access": "...", "refresh": "..."}`
- **400** → eksik alan: `{"username": ["Bu alan zorunlu."], "password": ["Bu alan zorunlu."]}`
- **401** → `{"detail": "Verilen kimlik bilgileriyle aktif bir hesap bulunamadı"}`. Kullanıcı adı yanlış ile
  parola yanlış **aynı** yanıtı üretir.
- **429** → hesap kilidi veya istek sınırı (aşağıda).

### Hesap kilidi (gerçek davranış)

Kilit kullanıcı adı bazlıdır (django-axes). Aynı kullanıcı adıyla **3 başarısız** denemede hesap **15 dakika**
kilitlenir. Sıra şöyledir: 1. ve 2. hatalı deneme **401**, **3. hatalı deneme 429** döner; kilit süresince
yapılan tüm denemeler — **doğru parolayla bile** — 429 döner:

```json
{"detail": "Çok fazla başarısız giriş denemesi. Hesap geçici olarak kilitlendi; lütfen bir süre sonra tekrar deneyin."}
```

Kilit yanıtında `Retry-After` başlığı **yoktur** ve gövdede kalan süre alanı bulunmaz. Başarılı giriş sayacı
sıfırlar. Bundan bağımsız olarak IP bazlı istek sınırı (`LOGIN_THROTTLE_RATE`) aşıldığında da 429 döner; bu
durumda DRF `Retry-After` başlığı ekler.

## 2. Token yenileme — `POST /api/auth/refresh/`

`{"refresh": "<refresh token>"}` → **200** `{"access": "...", "refresh": "..."}`. Rotasyon açık olduğundan
yanıttaki **yeni** refresh token saklanmalıdır; eskisi kara listeye alınır ve tekrar kullanılırsa 401 döner.
Geçersiz token: **401** `{"detail": "Token is invalid", "code": "token_not_valid"}`; eksik alan: **400**.

## 3. Çıkış — `POST /api/auth/logout/` (JWT)

`{"refresh": "<refresh token>"}` → **205** (gövde yok); refresh token kara listeye alınır. Access token süresi
dolana kadar geçerli kalır. Hatalar: **400** `{"detail": "refresh alanı zorunludur."}` veya
`{"detail": "Geçersiz veya süresi dolmuş token."}`; token yoksa **401**.

## 4. Oturumdaki kullanıcı — `GET /api/auth/me/` (JWT)

**200** → `{"id", "username", "email"}` (bkz. `Me` bileşeni). Token yoksa
`{"detail": "Giriş bilgileri verilmedi."}`, geçersizse `TokenError` biçiminde 401.

## 5. Şifre sıfırlama

### Talep — `POST /api/auth/password-reset/`

`{"email": "kullanici@example.test"}` → her zaman **200**:

```json
{"detail": "E-posta kayıtlıysa şifre sıfırlama bağlantısı gönderildi."}
```

Yanıt, adresin kayıtlı olup olmamasından **bağımsızdır**; kayıtlı ve kayıtsız adresler arasında durum kodu
veya gövde farkı yoktur. Geçersiz e-posta biçimi 400 döner. Kayıtlı ve aktif hesaba
`FRONTEND_PASSWORD_RESET_URL?uid=...&token=...` bağlantısı gönderilir.

### Onay — `POST /api/auth/password-reset/confirm/`

`{"uid": "...", "token": "...", "new_password": "..."}` → **200** `{"detail": "Parola güncellendi."}`.
Bağlantı `PASSWORD_RESET_TIMEOUT` (varsayılan 3600 sn) süresince geçerlidir ve **tek kullanımlıktır**; geçersiz,
süresi dolmuş veya kullanılmış bağlantı **400** `{"token": ["Bağlantı geçersiz veya süresi dolmuş."]}` döner.
Yeni parola Django parola doğrulayıcılarından geçmelidir (`new_password` alanında 400).
