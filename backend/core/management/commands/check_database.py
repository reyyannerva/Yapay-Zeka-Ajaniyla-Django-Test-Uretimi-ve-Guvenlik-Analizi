"""PostgreSQL bağlantısını gerçekten doğrular — H4-01 / Issue #33.

Ayarların okunabilmesi bağlantının çalıştığını kanıtlamaz; bu komut sunucuya bağlanıp sürüm sorgular.
Parola hiçbir çıktıya yazılmaz.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, OperationalError, connections


class Command(BaseCommand):
    help = "Veritabanı bağlantısını doğrular ve sunucu sürümünü yazdırır (parola gösterilmez)."

    def add_arguments(self, parser):
        parser.add_argument("--database", default=DEFAULT_DB_ALIAS)

    def handle(self, *args, **options):
        conn = connections[options["database"]]
        s = conn.settings_dict
        target = f"{s.get('USER')}@{s.get('HOST') or 'localhost'}:{s.get('PORT') or 5432}/{s.get('NAME')}"
        if conn.vendor != "postgresql":
            raise CommandError(f"Beklenen veritabanı PostgreSQL; yapılandırılan: {conn.vendor}")
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version(), current_database(), current_user")
                version, database, user = cur.fetchone()
        except OperationalError as exc:
            first = (str(exc).strip().splitlines() or ["bilinmeyen hata"])[0]
            password = s.get("PASSWORD")
            if password:
                first = first.replace(password, "***")
            raise CommandError(
                f"PostgreSQL bağlantısı kurulamadı ({target}): {first}\n"
                "Kontrol edin: sunucu çalışıyor mu, POSTGRES_HOST/POSTGRES_PORT doğru mu, kullanıcı ve "
                "veritabanı oluşturuldu mu (backend/README.md)."
            ) from None
        self.stdout.write(self.style.SUCCESS(f"Bağlantı başarılı: {user}@{database} — {version}"))
