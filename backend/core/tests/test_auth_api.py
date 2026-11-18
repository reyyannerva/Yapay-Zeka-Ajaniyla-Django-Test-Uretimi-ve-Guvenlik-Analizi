"""SimpleJWT giriş + django-axes kilit + şifre sıfırlama API testleri — H4-02 / Issue #34."""
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient

from core.auth.serializers import make_reset_uid_token

pytestmark = pytest.mark.django_db

PASSWORD = "Gizli-Parola-123"
User = get_user_model()


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    """DRF throttle önbelleği testler arasında sıfırlanmaz; kilit testlerini etkilememesi için temizlenir."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def account(db):
    return User.objects.create_user(username="merve", password=PASSWORD, email="merve@example.test")


@pytest.fixture
def api():
    return APIClient()


def login(api, username="merve", password=PASSWORD):
    return api.post(reverse("auth:login"), {"username": username, "password": password}, format="json")


# --- Giriş / token ---
def test_login_success_returns_tokens(account, api):
    resp = login(api)
    assert resp.status_code == 200
    assert "access" in resp.data and "refresh" in resp.data


def test_login_wrong_password_401(account, api):
    assert login(api, password="yanlis").status_code == 401


def test_login_unknown_user_401(api):
    # Hesap varlığını ifşa etmeyen tutarlı yanıt.
    assert login(api, username="yokboyle", password="xyz").status_code == 401


def test_me_requires_authentication(account, api):
    assert api.get(reverse("auth:me")).status_code == 401
    token = login(api).data["access"]
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    me = api.get(reverse("auth:me"))
    assert me.status_code == 200 and me.data["username"] == "merve"


def test_me_invalid_token_401(api):
    api.credentials(HTTP_AUTHORIZATION="Bearer gecersiz.token.deger")
    assert api.get(reverse("auth:me")).status_code == 401


def test_refresh_returns_new_access(account, api):
    refresh = login(api).data["refresh"]
    resp = api.post(reverse("auth:refresh"), {"refresh": refresh}, format="json")
    assert resp.status_code == 200 and "access" in resp.data


def test_logout_blacklists_refresh(account, api):
    tokens = login(api).data
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    assert api.post(reverse("auth:logout"), {"refresh": tokens["refresh"]}, format="json").status_code == 205
    # Blacklist sonrası refresh reddedilir.
    api.credentials()
    assert api.post(reverse("auth:refresh"), {"refresh": tokens["refresh"]}, format="json").status_code == 401


# --- Hesap kilidi (3 başarısız / 15 dk) ---
def test_three_failures_lock_then_correct_password_rejected(account, api):
    assert login(api, password="yanlis1").status_code == 401
    assert login(api, password="yanlis2").status_code == 401
    # Üçüncü başarısız deneme kilidi tetikler.
    assert login(api, password="yanlis3").status_code == 429
    # Kilit süresince doğru parola da reddedilir.
    assert login(api, password=PASSWORD).status_code == 429


def test_login_works_again_after_lock_cleared(account, api):
    for pw in ("y1", "y2", "y3"):
        login(api, password=pw)
    assert login(api).status_code == 429  # kilitli
    from axes.utils import reset
    reset(username="merve")  # 15 dk cooloff süresinin dolmasını simüle eder
    assert login(api).status_code == 200  # süre sonunda yeniden giriş


def test_successful_login_resets_failure_counter(account, api):
    login(api, password="yanlis1")
    login(api, password="yanlis2")
    assert login(api).status_code == 200  # başarı sayacı sıfırlar
    # Sayaç sıfırlandığından iki başarısız deneme yeniden kilit getirmez.
    assert login(api, password="yanlis1").status_code == 401
    assert login(api, password="yanlis2").status_code == 401
    assert login(api).status_code == 200


# --- Şifre sıfırlama ---
def test_password_reset_request_registered_sends_email(account, api, mailoutbox):
    resp = api.post(reverse("auth:password-reset"), {"email": "merve@example.test"}, format="json")
    assert resp.status_code == 200
    assert len(mailoutbox) == 1 and "merve@example.test" in mailoutbox[0].to


def test_password_reset_request_unknown_email_generic_no_email(api, mailoutbox):
    resp = api.post(reverse("auth:password-reset"), {"email": "yok@example.test"}, format="json")
    assert resp.status_code == 200  # hesap varlığı ifşa edilmez
    assert len(mailoutbox) == 0


def test_password_reset_confirm_valid_changes_password(account, api):
    uid, token = make_reset_uid_token(account)
    resp = api.post(reverse("auth:password-reset-confirm"),
                    {"uid": uid, "token": token, "new_password": "Yeni-Gizli-456"}, format="json")
    assert resp.status_code == 200
    account.refresh_from_db()
    assert account.check_password("Yeni-Gizli-456")


def test_password_reset_confirm_expired_token_400(account, api):
    # Token'ı PASSWORD_RESET_TIMEOUT (3600 sn) öncesinden üretilmiş gibi oluştur → süresi dolmuş.
    # Django'nun token _now()'ı naive datetime kullanır.
    old = datetime.now() - timedelta(seconds=10000)
    with patch.object(default_token_generator, "_now", return_value=old):
        uid, token = make_reset_uid_token(account)
    resp = api.post(reverse("auth:password-reset-confirm"),
                    {"uid": uid, "token": token, "new_password": "Yeni-Gizli-456"}, format="json")
    assert resp.status_code == 400


def test_password_reset_confirm_invalid_token_400(account, api):
    uid, _ = make_reset_uid_token(account)
    resp = api.post(reverse("auth:password-reset-confirm"),
                    {"uid": uid, "token": "gecersiz-token", "new_password": "Yeni-Gizli-456"}, format="json")
    assert resp.status_code == 400


def test_password_reset_confirm_reused_link_400(account, api):
    uid, token = make_reset_uid_token(account)
    first = api.post(reverse("auth:password-reset-confirm"),
                     {"uid": uid, "token": token, "new_password": "Yeni-Gizli-456"}, format="json")
    assert first.status_code == 200
    # Parola değişince eski bağlantı geçersizdir.
    reused = api.post(reverse("auth:password-reset-confirm"),
                      {"uid": uid, "token": token, "new_password": "Baska-Gizli-789"}, format="json")
    assert reused.status_code == 400


# --- Hassas veri sızıntısı yok ---
def test_sensitive_data_not_in_responses(account, api):
    body = login(api).content.decode()
    assert PASSWORD not in body and "password" not in body.lower()
    token = login(api).data["access"]
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    me_body = api.get(reverse("auth:me")).content.decode()
    assert PASSWORD not in me_body and "password" not in me_body.lower()
