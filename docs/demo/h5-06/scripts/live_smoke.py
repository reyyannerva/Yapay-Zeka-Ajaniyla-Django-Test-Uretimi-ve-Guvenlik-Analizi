"""H5-06 canlı API smoke testi — Issue #44.

Çalışan backend'e (varsayılan http://127.0.0.1:8000) karşı gerçek HTTP istekleriyle temel entegrasyon
akışlarını doğrular: JWT giriş, /auth/me, proje CRUD, sahiplik (başkasının kaydını görememe), silme,
şifre sıfırlama talebi ve 3 hatalı girişte hesap kilidi. Çıktı redakte edilir (token/parola yazılmaz)
ve evidence/live_smoke_result.json'a kaydedilir. Stdlib dışında bağımlılık yoktur.

Kullanım (demo kullanıcıları tohumlanmış ve sunucu ayakta iken), depo kökünden:
    python docs/demo/h5-06/scripts/live_smoke.py
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "http://127.0.0.1:8000"
REPO = Path(__file__).resolve().parents[4]
ARCHIVE = REPO / "docs" / "demo" / "h5-06" / "demo-verileri" / "ornek-proje.zip"
OUT = REPO / "docs" / "demo" / "h5-06" / "evidence" / "live_smoke_result.json"
PW = "DemoParola!2026"  # yerel demo parolası (gerçek değil)


def _call(method, path, token=None, json_body=None, raw=None, content_type=None):
    url = BASE + path
    headers = {}
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode()
        headers["Content-Type"] = "application/json"
    elif raw is not None:
        data = raw
        headers["Content-Type"] = content_type
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return None, f"ERROR: {type(e).__name__}: {e}"


def _json(body):
    try:
        return json.loads(body)
    except Exception:  # noqa: BLE001
        return {}


def _multipart(fields, filename, filecontent):
    boundary = "----h506demoBoundary7MA4YWxkTrZu0gW"
    parts = []
    for k, v in fields.items():
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"archive\"; filename=\"{filename}\"\r\n"
        f"Content-Type: application/zip\r\n\r\n".encode())
    parts.append(filecontent)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def login(username, password):
    status, body = _call("POST", "/api/auth/login/", json_body={"username": username, "password": password})
    data = _json(body)
    return status, data.get("access"), data.get("refresh")


def main():
    ev = {"report": "H5-06 canlı API smoke testi", "issue": "#44", "base": BASE,
          "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "steps": []}

    def step(name, status, ok, detail=""):
        ev["steps"].append({"step": name, "http": status, "ok": bool(ok), "detail": detail})
        print(f"[{'OK ' if ok else 'XX '}] {name}: HTTP {status} {detail}")

    # 1. Giriş (JWT)
    s, access, refresh = login("demo_merve", PW)
    step("Giriş (demo_merve) JWT", s, s == 200 and bool(access) and bool(refresh),
         "access+refresh alındı" if access else "token yok")

    # 2. /auth/me
    s, body = _call("GET", "/api/auth/me/", token=access)
    step("Korumalı /auth/me", s, s == 200, f"username={_json(body).get('username')}")

    # 3. Proje listele
    s, body = _call("GET", "/api/projects/", token=access)
    d = _json(body)
    count = d.get("count", len(d) if isinstance(d, list) else "?")
    step("Proje listele (GET)", s, s == 200, f"count={count}")

    # 4. Proje oluştur (multipart upload)
    pid = None
    try:
        content = ARCHIVE.read_bytes()
        name = "Demo Mağaza API " + datetime.now().strftime("%H%M%S")
        raw, ct = _multipart({"name": name, "description": "H5-06 demo projesi"}, "ornek-proje.zip", content)
        s, body = _call("POST", "/api/projects/", token=access, raw=raw, content_type=ct)
        pid = _json(body).get("id")
        step("Proje oluştur (POST multipart)", s, s == 201 and bool(pid), f"id={pid}")
    except Exception as e:  # noqa: BLE001
        step("Proje oluştur (POST multipart)", None, False, f"HATA: {e}")

    # 5-8 yalnızca oluşturma başarılıysa
    if pid:
        s, body = _call("GET", f"/api/projects/{pid}/", token=access)
        step("Proje detay (GET)", s, s == 200, f"name={_json(body).get('name')}")

        s, body = _call("PATCH", f"/api/projects/{pid}/", token=access,
                        json_body={"description": "güncellendi (demo)"})
        step("Proje güncelle (PATCH)", s, s == 200, "")

        # Sahiplik: ikinci kullanıcı başkasının projesini görememeli (404)
        s2, acc2, _ = login("demo_ikinci", PW)
        s, body = _call("GET", f"/api/projects/{pid}/", token=acc2)
        step("Sahiplik kontrolü (başkasının projesi → 404)", s, s == 404, "")

        s, body = _call("DELETE", f"/api/projects/{pid}/", token=access)
        step("Proje sil (DELETE)", s, s in (204, 200), "")

    # 9. Şifre sıfırlama talebi (konsol e-posta backend)
    s, body = _call("POST", "/api/auth/password-reset/", json_body={"email": "demo.merve@example.test"})
    step("Şifre sıfırlama talebi (POST)", s, s in (200, 202, 204), "")

    # 10. Hesap kilidi: 3 hatalı giriş (ayrı kullanıcı)
    lock_statuses = []
    for i in range(4):
        s, _, _ = login("demo_kilit", "yanlis-parola")
        lock_statuses.append(s)
    locked = any(x in (403, 423, 429) for x in lock_statuses)
    step("Hesap kilidi (3 hatalı giriş)", lock_statuses, locked, f"statuses={lock_statuses}")

    ev["ozet"] = {"toplam": len(ev["steps"]), "gecen": sum(1 for x in ev["steps"] if x["ok"]),
                  "kalan": sum(1 for x in ev["steps"] if not x["ok"])}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(ev, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"\nOzet: {ev['ozet']}  ->  {OUT}")
    return 0 if ev["ozet"]["kalan"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
