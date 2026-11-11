"""Prompt şablonu (pytest_v1) — H3-05 / Issue #31.

İsteme yalnızca ÜRETİM girdisi (metot, endpoint, rol, girdi, beklenen güvenli durum/davranış)
verilir. Cevap anahtarı meta (is_known_flaw, observed_flawed_status, dev/test ayrımı) KONMAZ.
"""
from __future__ import annotations

import json

from . import PROMPT_VERSION
from .contracts import Case

SYSTEM = (
    "Sen bir yazılım test otomasyonu uzmanısın. Django REST Framework tabanlı KONTROLLÜ bir hedef "
    "uygulama için TEK bir çalıştırılabilir Pytest test fonksiyonu yazarsın. Yalnızca istenen "
    "kodu üretirsin; açıklama veya ek metin yazmazsın."
)

_TEMPLATE = """\
Aşağıdaki kontrollü DRF uç noktası için tek bir Pytest test fonksiyonu yaz.

Ortam (hazır verilenler):
- pytest-django kullanılır; modül başında `pytestmark = pytest.mark.django_db` bulunur.
- İki fixture hazırdır (conftest.py sağlar): `seeded_db` (kullanıcı ve makale fixture'larını yükler)
  ve `api_client` (DRF APIClient). Test fonksiyonu bu ikisini parametre olarak ALMALIDIR.
- Kimlik doğrulama: `api_client.force_authenticate(user=User.objects.get(username="<kullanıcı>"))`.
  Anonim istekte force_authenticate ÇAĞRILMAZ.
- URL üretimi: pk varsa `reverse("{url_name}", kwargs={{"pk": {pk}}})`, yoksa `reverse("{url_name}")`.
- İstek: `api_client.{method_lower}(url, <gövde>, format="json")` (GET/DELETE'te gövde gönderilmez).

Test edilecek durum:
- Senaryo kimliği: {scenario_id}
- HTTP metodu: {http_method}
- reverse url adı: {url_name}
- pk: {pk}
- Kullanıcı: {user_display} (rol: {user_role})
- İstek gövdesi (JSON): {request_input}
- Endpoint yazılabilir alanları: {writable_fields}
- BEKLENEN HTTP durum kodu: {expected_status}
- Beklenen davranış: {expected_behavior}

Gereksinimler:
- Fonksiyon adı tam olarak: {test_name}
- Parametreler: (seeded_db, api_client)
- Gerekliyse önce `force_authenticate` ile kullanıcıyı doğrula (anonimse atla).
- İsteği gönder ve `assert response.status_code == {expected_status}` ile doğrula.
- Importlar: `import pytest`, `from django.contrib.auth.models import User`, `from django.urls import reverse`.
- Modül başında `pytestmark = pytest.mark.django_db` bulunsun.
- SADECE Python kodunu TEK bir ```python kod bloğu içinde döndür. Başka hiçbir şey yazma.
"""


def test_name(scenario_id: str) -> str:
    return "test_" + scenario_id.lower().replace("-", "_")


def render(case: Case) -> str:
    f = case.prompt_fields()
    body = json.dumps(f["request_input"], ensure_ascii=False) if f["request_input"] else "(gövde yok)"
    writable = json.dumps(f["writable_fields"], ensure_ascii=False) if f["writable_fields"] else "(yok)"
    return _TEMPLATE.format(
        url_name=f["url_name"],
        pk=f["pk"],
        method_lower=f["http_method"].lower(),
        scenario_id=f["scenario_id"],
        http_method=f["http_method"],
        user_display=f["user_username"] or "anonim",
        user_role=f["user_role"],
        request_input=body,
        writable_fields=writable,
        expected_status=f["expected_status"],
        expected_behavior=f["expected_behavior"],
        test_name=test_name(f["scenario_id"]),
    )


def version() -> str:
    return PROMPT_VERSION
