"""E2E arşiv fixture'ları — H5-03 / #41.

Küçük ama geçerli bir Django/DRF proje arşivi (ornek_api.zip) ile geçersiz örnekleri üretir. Arşivdeki kod
yalnızca backend'in statik arşiv doğrulamasından geçirilir; hiçbir aşamada çalıştırılmaz.

    python make_fixtures.py --out /tmp/h5-03-fixtures
"""
import argparse
import io
import zipfile
from pathlib import Path

FILES = {
    "ornek_api/manage.py": (
        "#!/usr/bin/env python\nimport os\nimport sys\n\n"
        "if __name__ == '__main__':\n"
        "    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ornek_api.settings')\n"
        "    from django.core.management import execute_from_command_line\n"
        "    execute_from_command_line(sys.argv)\n"
    ),
    "ornek_api/ornek_api/__init__.py": "",
    "ornek_api/ornek_api/settings.py": (
        "SECRET_KEY = 'yalnizca-ornek'\nDEBUG = False\nALLOWED_HOSTS = ['localhost']\n"
        "INSTALLED_APPS = [\n    'django.contrib.auth',\n    'django.contrib.contenttypes',\n"
        "    'rest_framework',\n    'siparis',\n]\nROOT_URLCONF = 'ornek_api.urls'\n"
    ),
    "ornek_api/ornek_api/urls.py": (
        "from django.urls import path\nfrom siparis.views import SiparisListe\n\n"
        "urlpatterns = [path('api/siparisler/', SiparisListe.as_view())]\n"
    ),
    "ornek_api/siparis/__init__.py": "",
    "ornek_api/siparis/views.py": (
        "from rest_framework.permissions import IsAuthenticated\nfrom rest_framework.response import Response\n"
        "from rest_framework.views import APIView\n\n\nclass SiparisListe(APIView):\n"
        "    permission_classes = [IsAuthenticated]\n\n    def get(self, request):\n        return Response([])\n"
    ),
}


def valid_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in FILES.items():
            zf.writestr(name, content)
    return buf.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    out = parser.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    (out / "ornek_api.zip").write_bytes(valid_zip())
    (out / "bozuk.zip").write_bytes(b"PK\x03\x04 bu bir zip degil")  # .zip uzantılı bozuk içerik
    (out / "gecerli_referans.json").write_text(
        '[{"requirement_code":"ACC-SIPARIS-1","category":"ACCESS_RULE","title":"Anonim sipariş listesini göremez",'
        '"expected_result":"Kimliksiz istek 401 döner.","specification":{"schema_version":1,"endpoint":"/api/siparisler/",'
        '"method":"GET","expected_status_by_role":{"anonim":401,"kullanici":200}}},'
        '{"requirement_code":"ROL-KULLANICI","category":"ROLE","title":"Standart kullanıcı rolü",'
        '"specification":{"schema_version":1,"role":"kullanici"}}]',
        encoding="utf-8",
    )
    (out / "gecersiz_referans.json").write_text(
        '{"requirement_code":"ACC-HATALI","category":"ACCESS_RULE","title":"Geçersiz metot",'
        '"expected_result":"-","specification":{"schema_version":1,"endpoint":"/api/x/","method":"TRACE",'
        '"expected_status_by_role":{"anonim":401}}}',
        encoding="utf-8",
    )
    print(f"fixture'lar yazıldı: {out}")


if __name__ == "__main__":
    main()
