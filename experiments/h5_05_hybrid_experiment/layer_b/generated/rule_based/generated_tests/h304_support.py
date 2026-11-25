"""Üretilen testlerin kullandığı küçük çalışma zamanı yardımcıları — H3-04 / Issue #30.

Bu dosya üretim sırasında değiştirilmeden ``h304_support.py`` adıyla üretilen test dizinine
kopyalanır. Doğrulama iletileri ``[H304] scenario=... check=... expected=... observed=...``
biçimindedir; sonuç sınıflandırıcısı (runner) bu işaretle hatanın kaynağını ayırt eder:

* ``check=route``       → üretici kaynaklı teknik hata (yanlış URL üretimi)
* ``check=status``      → uygulama davranışı / bilinen güvenlik kusuru (beklenen kod referanstan)
* ``check=side_effect`` → uygulama davranışı / bilinen güvenlik kusuru (yan etki referans semantiğine aykırı)
"""
from __future__ import annotations

from django.apps import apps


def _model(label: str):
    app_label, model_name = label.split(".")
    return apps.get_model(app_label, model_name)


def snapshot(model_label: str, pk, fields):
    """Kaynağın yazılabilir alanlarının anlık görüntüsü; kaynak yoksa ``None``."""
    return _model(model_label).objects.filter(pk=pk).values(*fields).first()


def model_count(model_label: str) -> int:
    return _model(model_label).objects.count()


def route_message(scenario_id: str, expected_path: str, actual_path: str) -> str:
    return (f"[H304] scenario={scenario_id} check=route expected={expected_path} observed={actual_path} | "
            "üretilen URL senaryodaki endpoint ile uyuşmuyor")


def status_message(scenario_id: str, expected: int, response, behavior: str) -> str:
    body = getattr(response, "content", b"")[:300]
    try:
        body = body.decode("utf-8", "replace")
    except AttributeError:
        pass
    return (f"[H304] scenario={scenario_id} check=status expected={expected} observed={response.status_code} | "
            f"{behavior} | yanıt: {body}")


def side_effect_message(scenario_id: str, rule: str, expected, observed) -> str:
    return (f"[H304] scenario={scenario_id} check=side_effect expected={rule} observed=violated | "
            f"beklenen={expected!r} gözlenen={observed!r}")
