#!/usr/bin/env bash
# H5-06 / #44 — demo öncesi tam kontrol: (1) H5-03 gerçek E2E regresyonu (giriş, token yenileme, çıkış,
# hesap kilidi, şifre sıfırlama, proje CRUD, AnalysisRun, referans JSON, yetki), (2) canlı demo provası ve
# ekran görüntüleri. PostgreSQL + Django/DRF + Vite + Chromium + yerel SMTP yakalayıcı; API taklit edilmez.
# Ön koşullar ve ayrıntı: docs/demo/h5-06/README.md
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
H503="$ROOT/e2e/h5-03"
OUT="$ROOT/docs/demo/h5-06"
WORK="${E2E_WORK_DIR:-$(mktemp -d)}"
PIDS=()
cleanup() { for pid in "${PIDS[@]}"; do kill "$pid" 2>/dev/null || true; done; }
trap cleanup EXIT

python "$H503/make_fixtures.py" --out "$WORK/fixtures"
(cd "$ROOT/backend" && python "$H503/create_test_users.py" "$WORK/creds.json")
python "$H503/smtp_catcher.py" --port 1025 --out "$WORK/mail" > "$WORK/smtp.log" 2>&1 &
PIDS+=($!)
(cd "$ROOT/frontend" && VITE_API_BASE_URL=http://127.0.0.1:8000 npx vite --port 5173 --strictPort > "$WORK/vite.log" 2>&1) &
PIDS+=($!)
for _ in $(seq 1 60); do curl -sf -o /dev/null http://localhost:5173/login && break; sleep 0.5; done

export E2E_BACKEND_ENV='{"EMAIL_BACKEND":"django.core.mail.backends.smtp.EmailBackend","EMAIL_HOST":"127.0.0.1","EMAIL_PORT":"1025","EMAIL_USE_TLS":"false","JWT_ACCESS_MINUTES":"1","LOGIN_THROTTLE_RATE":"200/min"}'
export E2E_CREDS="$WORK/creds.json" E2E_FIXTURES="$WORK/fixtures" E2E_MAIL_DIR="$WORK/mail"
export NODE_PATH="${NODE_PATH:-$(npm root -g)}"
mkdir -p "$OUT"

REG=0
if [ "${DEMO_ONLY:-0}" != "1" ]; then
echo "== 1/2 H5-03 gerçek E2E regresyonu (çıktılar geçici dizine; H5-03 kanıtları değiştirilmez)"
set +e
E2E_SHOTS="$WORK/h503-shots" E2E_EVIDENCE="$WORK/h503-evidence" node "$H503/run_e2e.cjs"
REG=$?
set -e
cp "$WORK/h503-evidence/e2e-sonuclari.json" "$OUT/e2e-regresyon-sonuclari.json" 2>/dev/null || true
fi

echo "== 2/2 Canlı demo provası"
set +e
node "$HERE/run_demo.cjs"
DEMO=$?
set -e
echo "regresyon=$REG demo=$DEMO"
exit $(( REG != 0 || DEMO != 0 ))
