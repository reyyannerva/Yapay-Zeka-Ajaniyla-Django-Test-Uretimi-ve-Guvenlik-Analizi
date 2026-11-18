"""Giriş denemesi ve geçici kilit verisinin kalıcılığı (django-axes) — Issue #33.

Bu testler Django ``authenticate()`` düzeyinde django-axes'in deneme sayısını ve kilit bitiş zamanını
veritabanına yazdığını doğrular. DRF/SimpleJWT giriş uç noktaları ve API yanıtları H4-02 (#34) kapsamındadır.
"""
from datetime import timedelta

import pytest
from axes.models import AccessAttempt, AccessAttemptExpiration, AccessFailureLog
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.test import RequestFactory

pytestmark = pytest.mark.django_db

PASSWORD = "Gizli-Parola-123"


def login(username, password):
    request = RequestFactory().post("/admin/login/", REMOTE_ADDR="10.0.0.5", HTTP_USER_AGENT="pytest")
    return authenticate(request=request, username=username, password=password)


@pytest.fixture
def alice(db):
    return get_user_model().objects.create_user(username="alice", password=PASSWORD)


def test_policy_settings():
    assert settings.AXES_FAILURE_LIMIT == 3
    assert settings.AXES_COOLOFF_TIME == timedelta(minutes=15)
    assert settings.AXES_LOCKOUT_PARAMETERS == ["username"]
    assert settings.AXES_USE_ATTEMPT_EXPIRATION is True
    assert settings.AUTH_USER_MODEL == "auth.User"  # özel kullanıcı modeli yok; kullanıcı tablosu değişmedi


def test_failed_attempts_are_counted_and_persisted(alice):
    assert login("alice", "yanlis") is None
    assert login("alice", "yanlis") is None
    attempt = AccessAttempt.objects.get(username="alice")
    assert attempt.failures_since_start == 2
    assert AccessFailureLog.objects.filter(username="alice").count() == 2


def test_third_failure_locks_for_fifteen_minutes(alice):
    for _ in range(3):
        login("alice", "yanlis")
    attempt = AccessAttempt.objects.get(username="alice")
    assert attempt.failures_since_start == 3
    expiration = AccessAttemptExpiration.objects.get(access_attempt=attempt)
    assert expiration.expires_at - attempt.attempt_time == timedelta(minutes=15)
    assert AccessFailureLog.objects.filter(username="alice", locked_out=True).exists()
    # Kilit süresince doğru parola da reddedilir (axes kimlik doğrulama arka ucu).
    assert login("alice", PASSWORD) is None


def test_lock_data_survives_new_query_and_does_not_store_password(alice):
    for _ in range(3):
        login("alice", "yanlis-parola-xyz")
    stored = AccessAttempt.objects.values().get(username="alice")
    assert stored["failures_since_start"] == 3
    assert "yanlis-parola-xyz" not in " ".join(str(v) for v in stored.values())


def test_successful_login_resets_counter(alice, client):
    """Sayaç sıfırlama ``user_logged_in`` sinyaliyle olur; bu yüzden gerçek oturum açma akışı kullanılır."""
    alice.is_staff = True
    alice.save()
    client.post("/admin/login/", {"username": "alice", "password": "yanlis"})
    assert AccessAttempt.objects.get(username="alice").failures_since_start == 1
    response = client.post("/admin/login/?next=/admin/", {"username": "alice", "password": PASSWORD})
    assert response.status_code == 302
    assert not AccessAttempt.objects.filter(username="alice").exists()


def test_locked_account_rejected_by_http_login_flow(alice, client):
    for _ in range(3):
        client.post("/admin/login/", {"username": "alice", "password": "yanlis"})
    response = client.post("/admin/login/", {"username": "alice", "password": PASSWORD})
    assert response.status_code == 429  # axes kilit yanıtı (Too Many Requests)


def test_lock_is_per_username(alice):
    get_user_model().objects.create_user(username="bob", password=PASSWORD)
    for _ in range(3):
        login("alice", "yanlis")
    assert login("bob", PASSWORD) is not None
