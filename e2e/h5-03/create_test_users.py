"""Kontrollü E2E test kullanıcıları — H5-03 / #41.

e2e_kullanici_a / _b / _c hesaplarını oluşturur veya parolalarını yeniler. Parolalar her çalıştırmada
rastgele üretilir ve YALNIZCA verilen dosyaya (izin 0600) yazılır; repoya, loga veya ekrana yazılmaz.
Gerçek kişisel veri kullanılmaz (example.test alan adı). Kullanıcıların axes kilit kayıtları sıfırlanır.

    cd backend && python ../e2e/h5-03/create_test_users.py /tmp/e2e/creds.json
"""
import json
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from axes.utils import reset  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402

USERS = {"A": "e2e_kullanici_a", "B": "e2e_kullanici_b", "C": "e2e_kullanici_c"}


def main(out: Path) -> None:
    model = get_user_model()
    creds = {}
    for key, username in USERS.items():
        password = f"E2e-{secrets.token_urlsafe(12)}"
        user, _ = model.objects.get_or_create(username=username)
        user.email = f"{username}@example.test"
        user.is_staff = False
        user.is_superuser = False
        user.is_active = True
        user.set_password(password)
        user.save()
        reset(username=username)
        creds[key] = {"username": username, "password": password, "email": user.email}
    out.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as handle:
        json.dump(creds, handle)
    print(f"test kullanıcıları hazır: {', '.join(USERS.values())}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
