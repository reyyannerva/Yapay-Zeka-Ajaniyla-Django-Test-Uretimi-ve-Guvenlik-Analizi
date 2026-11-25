"""Yerel SMTP yakalayıcı — H5-03 / #41 entegrasyon testleri için.

Backend'in şifre sıfırlama e-postasını GERÇEK SMTP protokolüyle göndermesini doğrular; e-posta dış
dünyaya iletilmez, yalnızca verilen dizine .eml dosyası olarak yazılır. Kullanım:

    python smtp_catcher.py --port 1025 --out /tmp/h5-03-mail

Backend ortamı: EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend, EMAIL_HOST=127.0.0.1,
EMAIL_PORT=1025, EMAIL_USE_TLS=false. Üretim SMTP sunucusu kullanılmaz.
"""
import argparse
import asyncio
import time
from pathlib import Path

from aiosmtpd.controller import Controller


class FileHandler:
    def __init__(self, out: Path):
        self.out = out

    async def handle_DATA(self, server, session, envelope):  # noqa: N802 (aiosmtpd arayüzü)
        name = f"{time.time_ns()}.eml"
        (self.out / name).write_bytes(envelope.original_content or envelope.content)
        return "250 Message accepted for delivery"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=1025)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    controller = Controller(FileHandler(args.out), hostname="127.0.0.1", port=args.port)
    controller.start()
    print(f"SMTP yakalayıcı 127.0.0.1:{args.port} → {args.out}", flush=True)
    try:
        asyncio.new_event_loop().run_forever()
    finally:
        controller.stop()


if __name__ == "__main__":
    main()
