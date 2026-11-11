"""Üretilen testlerin ortak fixture'ları — H3-05 / Issue #31."""
import pytest
from django.core.management import call_command
from rest_framework.test import APIClient


@pytest.fixture
def seeded_db(db):
    call_command("loaddata", "users", "articles", verbosity=0)


@pytest.fixture
def api_client():
    return APIClient()
