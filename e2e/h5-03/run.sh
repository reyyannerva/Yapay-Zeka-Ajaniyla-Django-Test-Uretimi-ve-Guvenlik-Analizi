#!/usr/bin/env bash
# H5-03 / #41 gerçek uçtan uca entegrasyon testleri: PostgreSQL + Django/DRF + Vite + Chromium + SMTP yakalayıcı.
# Ön koşullar: backend/.env içinde PostgreSQL bağlantısı, backend bağımlılıkları (+ aiosmtpd), frontend
# bağımlılıkları ve Playwright (Chromium). Ayrıntı: e2e/h5-03/README.md
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
WORK="${E2E_WORK_DIR:-$(mktemp -d)}"
PIDS=()
cleanup() { for pid in "${PIDS[@]}"; do kill "$pid" 2>/dev/null || true; done; }
trap cleanup EXIT

python "$HERE/make_fixtures.py" --out "$WORK/fixtures"
(cd "$ROOT/backend" && python "$HERE/create_test_users.py" "$WORK/creds.json")

python "$HERE/smtp_catcher.py" --port 1025 --out "$WORK/mail" > "$WORK/smtp.log" 2>&1 &
PIDS+=($!)
(cd "$ROOT/frontend" && VITE_API_BASE_URL=http://127.0.0.1:8000 npx vite --port 5173 --strictPort > "$WORK/vite.log" 2>&1) &
PIDS+=($!)
for _ in $(seq 1 60); do curl -sf -o /dev/null http://localhost:5173/login && break; sleep 0.5; done

# Test ortamı ayarları (yalnızca bu süreç için; üretim varsayılanları değişmez):
# - E-posta gerçek SMTP ile yerel yakalayıcıya gider.
# - Access süresi 1 dk: token yenileme gerçek süre dolumuyla test edilir.
# - Giriş istek sınırı yükseltilir: tek IP'den çok sayıda test girişi yapılır (kilit politikası değişmez: 3/15 dk).
export E2E_BACKEND_ENV='{"EMAIL_BACKEND":"django.core.mail.backends.smtp.EmailBackend","EMAIL_HOST":"127.0.0.1","EMAIL_PORT":"1025","EMAIL_USE_TLS":"false","JWT_ACCESS_MINUTES":"1","LOGIN_THROTTLE_RATE":"200/min"}'
export E2E_CREDS="$WORK/creds.json" E2E_FIXTURES="$WORK/fixtures" E2E_MAIL_DIR="$WORK/mail"
NODE_PATH="${NODE_PATH:-$(npm root -g)}" node "$HERE/run_e2e.cjs"
