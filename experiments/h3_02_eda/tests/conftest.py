"""Ortak test yardımcıları — H3-02 / Issue #28.

Buradaki SENTETİK kayıtlar yalnızca izole birim testleri içindir; gerçek proje analiz
sonuçlarına hiçbir şekilde karışmaz. Gerçek veri kümesi testleri ``test_real_dataset.py``
içindedir ve depodaki kanonik dosyaları okur.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

PKG_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PKG_ROOT.parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

SCHEMA_PATH = REPO_ROOT / "benchmarks" / "drf_fixtures" / "scenarios" / "scenarios.schema.json"

# Sentetik fixture'lar (gerçek fixture yapısını taklit eder)
USERS = [
    {"model": "auth.user", "pk": 1, "fields": {"username": "root", "is_staff": True}},
    {"model": "auth.user", "pk": 2, "fields": {"username": "u_owner", "is_staff": False}},
    {"model": "auth.user", "pk": 3, "fields": {"username": "u_other", "is_staff": False}},
]
ARTICLES = [
    {"model": "catalog.article", "pk": 10, "fields": {"owner": 2, "is_published": True}},
    {"model": "catalog.article", "pk": 11, "fields": {"owner": 2, "is_published": False}},
]
CONFIG_URLS = 'urlpatterns = [path("api/", include("catalog.urls"))]'
CATALOG_URLS = '''
from .insecure import BadDetail
from .views import ItemViewSet, PublishView
router = SimpleRouter(trailing_slash=True)
router.register(r"articles", ItemViewSet, basename="article")
urlpatterns = [
    path("articles/<int:pk>/publish/", PublishView.as_view(), name="p"),
    path("insecure/articles/<int:pk>/", BadDetail.as_view(), name="b"),
]
urlpatterns += router.urls
'''


def make_scenario(**over) -> dict:
    base = {
        "id": "SC-TST-001",
        "category": "HTTP_BEHAVIOR",
        "http_method": "GET",
        "endpoint": "/api/articles/10/",
        "user_role": "owner",
        "request_input": None,
        "expected_http_status": 200,
        "expected_behavior": "Sentetik test kaydı.",
        "label": "positive",
        "is_intentional_flaw": False,
        "fixture_ref": {"user": "u_owner", "article": 10},
        "requirement_refs": ["İST-03"],
    }
    base.update(copy.deepcopy(over))
    return base


@pytest.fixture
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def routes():
    from scenario_eda.data import parse_routes

    return parse_routes(CONFIG_URLS, CATALOG_URLS)
