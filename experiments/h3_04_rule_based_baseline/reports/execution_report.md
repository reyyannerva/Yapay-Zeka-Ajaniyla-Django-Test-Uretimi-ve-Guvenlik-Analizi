# H3-04 | Üretilen Testlerin Çalıştırma Raporu

> Otomatik üretilmiştir. Pytest sonucu (passed/failed) olduğu gibi korunur; sınıflandırma ayrı bir alandır. Bilinen güvenlik kusurunu tespit eden test **başarısız** olarak kalır.

- Planlanan test: **38**, pytest'in topladığı: **38**, pytest çıkış kodu: `1` (kusur tespit eden başarısız testler nedeniyle 0 olmayabilir).
- Pytest sonuçları: failed=2, passed=36.
- Yalıtım: 38 testin her biri tek başına ve paket ters sırayla çalıştırıldı; fark: tek başına 0, ters sıra 0 → **yalıtılmış**.
- Girdi dosyaları çalıştırma sonrası değişmedi: **evet**.

## Sınıflandırma

| Sınıf | Anlam | Test |
|---|---|---|
| PASSED | Geçti — referanstaki güvenli beklenti karşılandı | 35 |
| KNOWN_FLAW_DETECTED | Başarısız — bilinen güvenlik kusuru tespit edildi | 2 |
| KNOWN_FLAW_NOT_DETECTED | Geçti — bilinen güvenlik kusuru bu testle tespit edilemedi | 1 |
| APPLICATION_MISMATCH | Başarısız — uygulama davranışı bağımsız referanstan farklı | 0 |
| GENERATION_ERROR | Üretim kaynaklı teknik hata | 0 |
| ENVIRONMENT_ERROR | Hedef uygulama/ortam yüklenemedi (üretici kaynaklı değil) | 0 |

## Metot bazında

| Metot | Test | Geçti | Başarısız | Üretim hatası |
|---|---|---|---|---|
| GET | 10 | 10 | 0 | 0 |
| POST | 9 | 9 | 0 | 0 |
| PUT | 8 | 7 | 1 | 0 |
| PATCH | 4 | 4 | 0 | 0 |
| DELETE | 7 | 6 | 1 | 0 |

## Beklenen durum kodu bazında (destek ≠ kanıt: 0 test = kanıt yok)

| Beklenen kod | Test | Geçti |
|---|---|---|
| 200 | 12 | 12 |
| 201 | 2 | 2 |
| 204 | 2 | 2 |
| 400 | 4 | 4 |
| 401 | 5 | 5 |
| 403 | 6 | 4 |
| 404 | 5 | 5 |
| 405 | 2 | 2 |

## Test sonuçları

| Senaryo | Test | Metot | Beklenen | Gözlenen | Pytest | Sınıf | Kanıt |
|---|---|---|---|---|---|---|---|
| SC-AUT-001 | test_sc_aut_001_post_anonymous_401 | POST | 401 | 401 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-AUT-002 | test_sc_aut_002_put_anonymous_401 | PUT | 401 | 401 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-AUT-003 | test_sc_aut_003_patch_anonymous_401 | PATCH | 401 | 401 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-AUT-004 | test_sc_aut_004_delete_anonymous_401 | DELETE | 401 | 401 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-AUT-005 | test_sc_aut_005_post_anonymous_401 | POST | 401 | 401 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-AUZ-001 | test_sc_auz_001_put_user_403 | PUT | 403 | 403 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-AUZ-002 | test_sc_auz_002_patch_user_403 | PATCH | 403 | 403 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-AUZ-003 | test_sc_auz_003_delete_user_403 | DELETE | 403 | 403 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-AUZ-004 | test_sc_auz_004_post_user_403 | POST | 403 | 403 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-CRT-001 | test_sc_crt_001_post_user_201 | POST | 201 | 201 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-CRT-002 | test_sc_crt_002_post_owner_201 | POST | 201 | 201 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-DEL-001 | test_sc_del_001_delete_owner_204 | DELETE | 204 | 204 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-DEL-002 | test_sc_del_002_delete_admin_204 | DELETE | 204 | 204 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-FLW-001 | test_sc_flw_001_put_user_403 | PUT | 403 | 200 | failed | KNOWN_FLAW_DETECTED | Gözlenen 200, ground truth'taki bilinen kusur durumuyla (observed_flawed_status=200) aynı; güvenli beklenti 403. Broken Object Level Authorization (BOLA/IDOR, OWASP API1:2023) |
| SC-FLW-002 | test_sc_flw_002_delete_user_403 | DELETE | 403 | 204 | failed | KNOWN_FLAW_DETECTED | Gözlenen 204, ground truth'taki bilinen kusur durumuyla (observed_flawed_status=204) aynı; güvenli beklenti 403. Broken Object Level Authorization (BOLA/IDOR, OWASP API1:2023) |
| SC-FLW-003 | test_sc_flw_003_get_anonymous_200 | GET | 200 | 200 | passed | KNOWN_FLAW_NOT_DETECTED | Durum kodu referansla eşleşti; kusurun sapması bu testin doğruladığı boyutta değil (content). |
| SC-INP-001 | test_sc_inp_001_post_user_400 | POST | 400 | 400 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-INP-002 | test_sc_inp_002_post_user_400 | POST | 400 | 400 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-INP-003 | test_sc_inp_003_put_owner_400 | PUT | 400 | 400 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-INP-004 | test_sc_inp_004_post_user_400 | POST | 400 | 400 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-LST-001 | test_sc_lst_001_get_anonymous_200 | GET | 200 | 200 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-LST-002 | test_sc_lst_002_get_user_200 | GET | 200 | 200 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-LST-003 | test_sc_lst_003_get_admin_200 | GET | 200 | 200 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-MNA-001 | test_sc_mna_001_delete_owner_405 | DELETE | 405 | 405 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-MNA-002 | test_sc_mna_002_put_owner_405 | PUT | 405 | 405 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-NF-001 | test_sc_nf_001_put_owner_404 | PUT | 404 | 404 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-NF-002 | test_sc_nf_002_delete_owner_404 | DELETE | 404 | 404 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-PUB-001 | test_sc_pub_001_post_owner_200 | POST | 200 | 200 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-RET-001 | test_sc_ret_001_get_anonymous_200 | GET | 200 | 200 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-RET-002 | test_sc_ret_002_get_anonymous_404 | GET | 404 | 404 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-RET-003 | test_sc_ret_003_get_owner_200 | GET | 200 | 200 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-RET-004 | test_sc_ret_004_get_admin_200 | GET | 200 | 200 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-RET-005 | test_sc_ret_005_get_user_404 | GET | 404 | 404 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-RET-006 | test_sc_ret_006_get_anonymous_404 | GET | 404 | 404 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-UPD-001 | test_sc_upd_001_put_owner_200 | PUT | 200 | 200 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-UPD-002 | test_sc_upd_002_put_admin_200 | PUT | 200 | 200 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-UPD-003 | test_sc_upd_003_patch_owner_200 | PATCH | 200 | 200 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
| SC-UPD-004 | test_sc_upd_004_patch_admin_200 | PATCH | 200 | 200 | passed | PASSED | Durum kodu ve yan etki kontrolleri geçti. |
