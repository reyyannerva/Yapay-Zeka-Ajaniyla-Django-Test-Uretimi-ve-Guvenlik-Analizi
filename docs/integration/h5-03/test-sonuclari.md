# H5-03 / #41 — Test sonuçları (kanıt)

Aşağıdaki çıktılar teslim commit'i üzerinde komutlar çalıştırılarak alınmıştır (özetler; tam çıktı yerel çalıştırmayla yeniden üretilebilir).

## Frontend

```text
$ npm run typecheck   → çıkış kodu 0
$ npm run build       → ✓ built in 3.53s
$ npx vitest run
✓ src/features/projects/ProjectPages.test.tsx (8 tests) 894ms
✓ src/features/auth/Login.test.tsx (9 tests) 2016ms
✓ src/features/analysis/AnalysisScreens.test.tsx (29 tests) 1915ms
✓ src/features/auth/ResetPassword.test.tsx (8 tests) 1061ms
✓ src/features/projects/ProjectUpload.test.tsx (10 tests) 780ms
✓ src/features/requirements/ReferenceRequirementsCard.test.tsx (6 tests) 498ms
✓ src/features/projects/StartAnalysisCard.test.tsx (5 tests) 413ms
✓ src/features/auth/ForgotAndExpired.test.tsx (3 tests) 335ms
✓ src/components/layout/AppLayout.test.tsx (6 tests) 314ms
✓ src/features/dashboard/Overview.test.tsx (6 tests) 287ms
✓ src/components/ui/Modal.test.tsx (6 tests) 203ms
✓ src/features/status/Unauthorized.test.tsx (4 tests) 174ms
✓ src/features/projects/DeleteConfirm.test.tsx (5 tests) 243ms
✓ src/components/ui/Input.test.tsx (3 tests) 164ms
✓ src/features/projects/ProjectList.test.tsx (3 tests) 185ms
✓ src/components/layout/ProtectedRoute.test.tsx (5 tests) 138ms
✓ src/components/ui/Button.test.tsx (3 tests) 102ms
✓ src/components/ui/Toast.test.tsx (2 tests) 135ms
✓ src/features/profile/Profile.test.tsx (4 tests) 140ms
✓ src/components/ui/AnalysisUi.test.tsx (13 tests) 128ms
✓ src/lib/session-guard.test.tsx (3 tests) 149ms
✓ src/lib/auth-context.test.tsx (6 tests) 123ms
✓ src/lib/api/client.test.ts (21 tests) 116ms
✓ src/components/ui/StageStrip.test.tsx (5 tests) 100ms
✓ src/components/ui/ConfirmDialog.test.tsx (3 tests) 112ms
✓ src/lib/theme-context.test.tsx (2 tests) 93ms
✓ src/components/ui/EmptyState.test.tsx (2 tests) 70ms
✓ src/components/ui/DataTable.test.tsx (2 tests) 72ms
✓ src/components/ui/StatusBadge.test.tsx (6 tests) 51ms
✓ src/components/ui/MetricCard.test.tsx (2 tests) 30ms
✓ src/lib/api/projects.test.ts (8 tests) 29ms
✓ src/lib/analysis-logic.test.ts (18 tests) 21ms
✓ src/lib/api/analysis-results.test.ts (9 tests) 14ms
✓ src/features/requirements/referenceJson.test.ts (18 tests) 14ms
✓ src/features/analysis/analysis-helpers.test.ts (6 tests) 7ms
✓ src/features/projects/useProjectForm.test.ts (5 tests) 5ms
✓ src/lib/queryKeys.test.ts (1 test) 4ms
Test Files  37 passed (37)
Tests  255 passed (255)
```

## Backend (PostgreSQL 16 test veritabanı)

```text
$ python manage.py check
System check identified no issues (1 silenced).
$ python manage.py makemigrations --check --dry-run
No changes detected
$ python -m pytest -q
471 passed in 81.94s (0:01:21)
```

## Gerçek uçtan uca (Chromium + Vite + Django/DRF + PostgreSQL + yerel SMTP)

`bash e2e/h5-03/run.sh` → 30 PASS / 0 FAIL, ilgili konsol sorunu: 0 (ayrıntı: [`e2e-sonuclari.json`](e2e-sonuclari.json), 2026-11-25T21:26:44.887Z).

| Senaryo | Sonuç |
| --- | --- |
| ENV-1 — Backend veritabanı gerçekten PostgreSQL | PASS |
| E2E-01-02 — Login ekranı açılır, gerçek kullanıcı A ile giriş yapılır | PASS |
| E2E-03 — Dashboard gerçek API verisiyle görüntülenir | PASS |
| E2E-04 — Gerçek ZIP arşivi multipart ile yüklenir; PostgreSQL kaydı A kullanıcısına aittir | PASS |
| E2E-04b — Geçersiz arşiv (bozuk ZIP) sunucu tarafından reddedilir ve kaydedilmez | PASS |
| E2E-05-06 — Proje listesinde gerçek proje görünür | PASS |
| E2E-07 — Proje detayı açılır | PASS |
| E2E-08-10 — Proje güncellenir; sayfa yenilemede ve PostgreSQL'de korunur | PASS |
| E2E-14-15 — Geçerli referans JSON kaydedilir; yenilemeden sonra backend'den okunur | PASS |
| E2E-16 — Geçersiz referans JSON (TRACE metodu) reddedilir; PostgreSQL'e yazılmaz | PASS |
| E2E-11-13 — Gerçek AnalysisRun oluşturulur; liste/detay gerçek durumu (QUEUED) gösterir | PASS |
| E2E-17-18 — Çıkış yapılır; refresh kara listeye alınır; korumalı sayfa ve geri tuşu önceki veriyi göstermez | PASS |
| E2E-19-22 — Kullanıcı B, A'nın kayıtlarını göremez; doğrudan URL backend tarafından reddedilir | PASS |
| E2E-23-25 — A tekrar girer; aktif analizli silme 409; analiz sonlanınca silinir (CASCADE) | PASS |
| AUTH-1 — Access token süresi dolunca refresh ile yenilenir ve istek tamamlanır | PASS |
| AUTH-2 — Sayfa yenilemede oturum korunur (refresh token ile) | PASS |
| AUTH-3 — Refresh token sunucuda iptal edilirse oturum güvenli biçimde sonlanır | PASS |
| LOCK-1 — 1. ve 2. hatalı giriş 401 (kilit yok) | PASS |
| LOCK-2 — 3. hatalı giriş 15 dakikalık kilidi başlatır; kalan süre sunucudan gösterilir | PASS |
| LOCK-3 — Kilit süresinde doğru parola reddedilir; sayfa yenilemede ve istemci saati ileri alınsa da kilit sürer | PASS |
| LOCK-4 — Kilit süresi dolunca (sunucu zamanı) doğru parolayla giriş yapılır ve sayaç sıfırlanır | PASS |
| RESET-1 — Şifremi unuttum talebi gönderilir; genel yanıt gösterilir | PASS |
| RESET-2 — Backend e-postayı SMTP ile gönderir; bağlantı frontend /reset-password rotasını gösterir | PASS |
| RESET-3 — Bağlantı açılır, token adres çubuğundan silinir; yeni parola belirlenir | PASS |
| RESET-4 — Eski parola reddedilir (401), yeni parola ile giriş yapılır | PASS |
| RESET-5 — Kullanılmış ve geçersiz bağlantılar reddedilir | PASS |
| NET-1 — Backend durunca kullanıcıya bağlantı hatası gösterilir (sahte başarı yok) | PASS |
| NET-2 — Backend yeniden başlatılınca oturum ve PostgreSQL kayıtları korunur | PASS |
| RESP-1 — 1440/1280/1024/768/390 px: yatay taşma yok | PASS |
| CLEAN — E2E test projeleri API ile silinir | PASS |
