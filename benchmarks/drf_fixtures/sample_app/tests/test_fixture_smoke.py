"""Fixture smoke testleri — H3-01 / Issue #27.

Senaryo veri kümesinin temsilî bir alt kümesinin, kontrollü hedef uygulamada GERÇEKTEN
beklenen HTTP davranışını ürettiğini doğrular. Bu testler H3-05'te LLM ile üretilecek
testler DEĞİLDİR; yalnızca fixture'ların ve beklenen sonuçların tutarlılığını kanıtlar.
"""
import pytest
from django.contrib.auth.models import User

pytestmark = pytest.mark.django_db


def as_user(api, username):
    api.force_authenticate(user=User.objects.get(username=username))
    return api


# --- GET list (HTTP_BEHAVIOR) ---
def test_list_anonymous_200_only_published(seeded_db, api):
    resp = api.get("/api/articles/")
    assert resp.status_code == 200
    titles = {a["title"] for a in resp.json()}
    assert "Alice Published" in titles
    assert "Alice Draft" not in titles  # taslaklar anonime görünmez


def test_list_admin_200_sees_all(seeded_db, api):
    resp = as_user(api, "admin").get("/api/articles/")
    assert resp.status_code == 200
    assert len(resp.json()) == 4


# --- GET retrieve (HTTP_BEHAVIOR / AUTHORIZATION) ---
def test_retrieve_published_anonymous_200(seeded_db, api):
    assert api.get("/api/articles/1/").status_code == 200


def test_retrieve_others_draft_user_404(seeded_db, api):
    assert as_user(api, "carol").get("/api/articles/2/").status_code == 404


def test_retrieve_own_draft_owner_200(seeded_db, api):
    assert as_user(api, "alice").get("/api/articles/2/").status_code == 200


def test_retrieve_nonexistent_404(seeded_db, api):
    assert api.get("/api/articles/999/").status_code == 404


# --- POST create (AUTHENTICATION / HTTP_BEHAVIOR / INPUT_VALIDATION) ---
def test_create_anonymous_401(seeded_db, api):
    assert api.post("/api/articles/", {"title": "x", "body": "y"}, format="json").status_code == 401


def test_create_user_valid_201(seeded_db, api):
    resp = as_user(api, "carol").post(
        "/api/articles/", {"title": "Carol Yazısı", "body": "içerik"}, format="json"
    )
    assert resp.status_code == 201
    assert resp.json()["owner"] == "carol"


def test_create_missing_title_400(seeded_db, api):
    assert as_user(api, "carol").post(
        "/api/articles/", {"body": "içerik"}, format="json"
    ).status_code == 400


def test_create_blank_title_400(seeded_db, api):
    assert as_user(api, "carol").post(
        "/api/articles/", {"title": "   ", "body": "x"}, format="json"
    ).status_code == 400


# --- PUT / PATCH update (AUTHENTICATION / AUTHORIZATION / HTTP_BEHAVIOR) ---
def test_put_anonymous_401(seeded_db, api):
    assert api.put(
        "/api/articles/1/", {"title": "T", "body": "B"}, format="json"
    ).status_code == 401


def test_put_non_owner_403(seeded_db, api):
    assert as_user(api, "carol").put(
        "/api/articles/1/", {"title": "T", "body": "B"}, format="json"
    ).status_code == 403


def test_put_owner_200(seeded_db, api):
    assert as_user(api, "alice").put(
        "/api/articles/1/", {"title": "Yeni", "body": "B"}, format="json"
    ).status_code == 200


def test_put_admin_other_200(seeded_db, api):
    assert as_user(api, "admin").put(
        "/api/articles/3/", {"title": "Yeni", "body": "B"}, format="json"
    ).status_code == 200


def test_put_owner_missing_title_400(seeded_db, api):
    assert as_user(api, "alice").put(
        "/api/articles/1/", {"body": "B"}, format="json"
    ).status_code == 400


def test_patch_non_owner_403(seeded_db, api):
    assert as_user(api, "carol").patch(
        "/api/articles/1/", {"title": "T"}, format="json"
    ).status_code == 403


def test_patch_owner_200(seeded_db, api):
    assert as_user(api, "alice").patch(
        "/api/articles/1/", {"title": "T"}, format="json"
    ).status_code == 200


def test_put_nonexistent_owner_404(seeded_db, api):
    assert as_user(api, "alice").put(
        "/api/articles/999/", {"title": "T", "body": "B"}, format="json"
    ).status_code == 404


# --- DELETE (AUTHORIZATION / HTTP_BEHAVIOR) ---
def test_delete_non_owner_403(seeded_db, api):
    assert as_user(api, "carol").delete("/api/articles/1/").status_code == 403


def test_delete_owner_204(seeded_db, api):
    assert as_user(api, "alice").delete("/api/articles/1/").status_code == 204


def test_delete_admin_other_204(seeded_db, api):
    assert as_user(api, "admin").delete("/api/articles/3/").status_code == 204


# --- 405 method not allowed (HTTP_BEHAVIOR) ---
def test_delete_collection_405(seeded_db, api):
    assert as_user(api, "alice").delete("/api/articles/").status_code == 405


def test_put_collection_405(seeded_db, api):
    assert as_user(api, "alice").put(
        "/api/articles/", {"title": "T"}, format="json"
    ).status_code == 405


# --- Publish APIView (AUTHENTICATION / AUTHORIZATION) ---
def test_publish_owner_200(seeded_db, api):
    resp = as_user(api, "alice").post("/api/articles/2/publish/")
    assert resp.status_code == 200
    assert resp.json()["is_published"] is True


def test_publish_non_owner_403(seeded_db, api):
    assert as_user(api, "carol").post("/api/articles/2/publish/").status_code == 403


def test_publish_anonymous_401(seeded_db, api):
    assert api.post("/api/articles/2/publish/").status_code == 401


# --- BİLEREK GÜVENSİZ uçlar: hatanın GERÇEKTEN var olduğunu kanıtlar ---
def test_insecure_put_non_owner_succeeds_200_FLAW(seeded_db, api):
    # BOLA: carol, alice'in kaydını güvensiz uçtan güncelleyebiliyor (olması gereken 403).
    assert as_user(api, "carol").put(
        "/api/insecure/articles/1/", {"title": "Ele geçti", "body": "B"}, format="json"
    ).status_code == 200


def test_insecure_delete_non_owner_succeeds_204_FLAW(seeded_db, api):
    assert as_user(api, "carol").delete("/api/insecure/articles/3/").status_code == 204


def test_insecure_list_anonymous_exposes_drafts_FLAW(seeded_db, api):
    resp = api.get("/api/insecure/articles/")
    assert resp.status_code == 200
    titles = {a["title"] for a in resp.json()}
    assert "Alice Draft" in titles  # taslak ifşası (olmaması gereken davranış)
