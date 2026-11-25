"""Hesap kilidi yanıtındaki kalan süre bilgisi — H5-03 / Issue #41.

Kilit kararı django-axes'tedir; bu testler yanıtın (frontend'in gösterdiği) ``code``, ``locked_until``,
``retry_after_seconds`` ve ``Retry-After`` alanlarını ve kilidin gerçek süre dolumuyla kalktığını doğrular.
Süre dolumu 15 dakika beklenmeden, axes'in kalıcı zaman damgaları geçmişe çekilerek simüle edilir.
"""
from datetime import timedelta

import pytest
from axes.models import AccessAttempt, AccessAttemptExpiration
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

PASSWORD = "Gizli-Parola-123"


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def account(db):
    return get_user_model().objects.create_user(username="kilit", password=PASSWORD, email="kilit@example.test")


@pytest.fixture
def api():
    return APIClient()


def login(api, password=PASSWORD, username="kilit"):
    return api.post(reverse("auth:login"), {"username": username, "password": password}, format="json")


def lock(api):
    assert login(api, "y1").status_code == 401
    assert login(api, "y2").status_code == 401
    return login(api, "y3")


def test_third_failure_returns_lock_details(account, api):
    resp = lock(api)
    assert resp.status_code == 429
    assert resp.data["code"] == "account_locked"
    assert resp.data["detail"].startswith("Çok fazla başarısız giriş denemesi")
    locked_until = parse_datetime(resp.data["locked_until"])
    remaining = (locked_until - timezone.now()).total_seconds()
    assert 14 * 60 < remaining <= 15 * 60
    assert 14 * 60 < resp.data["retry_after_seconds"] <= 15 * 60
    assert int(resp["Retry-After"]) == resp.data["retry_after_seconds"]


def test_correct_password_during_lock_rejected_with_same_deadline(account, api):
    first = lock(api)
    second = login(api, PASSWORD)
    assert second.status_code == 429
    assert "access" not in second.data and "refresh" not in second.data
    assert second.data["locked_until"] == first.data["locked_until"]
    assert second.data["retry_after_seconds"] <= first.data["retry_after_seconds"]


def test_lock_expires_after_cooloff_then_login_succeeds(account, api):
    lock(api)
    # 15 dakika + 1 sn geçmiş gibi: axes'in kalıcı zaman damgaları geriye alınır (üretim süresi değişmez).
    past = timezone.now() - timedelta(minutes=15, seconds=1)
    AccessAttempt.objects.filter(username="kilit").update(attempt_time=past)
    AccessAttemptExpiration.objects.filter(access_attempt__username="kilit").update(expires_at=past)
    resp = login(api, PASSWORD)
    assert resp.status_code == 200
    assert "access" in resp.data


def test_lock_not_yet_expired_still_rejected(account, api):
    lock(api)
    almost = timezone.now() + timedelta(seconds=30)
    AccessAttemptExpiration.objects.filter(access_attempt__username="kilit").update(expires_at=almost)
    resp = login(api, PASSWORD)
    assert resp.status_code == 429
    assert 0 < resp.data["retry_after_seconds"] <= 30


def test_wrong_password_before_lock_has_no_lock_fields(account, api):
    resp = login(api, "yanlis")
    assert resp.status_code == 401
    assert "locked_until" not in resp.data


def test_lock_is_per_username(account, api):
    other = get_user_model().objects.create_user(username="diger", password=PASSWORD)
    lock(api)
    assert login(api, PASSWORD, username=other.username).status_code == 200
