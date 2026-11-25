"""Üretilen testlerin ortak fixture'ları — H3-05 / Issue #31 (H5-05 Katman B: fixture listesi endpoint özetinden uyarlandı)."""
import pytest
from django.core.management import call_command
from rest_framework.test import APIClient


@pytest.fixture
def seeded_db(db):
    call_command("loaddata", "users", "tasks", verbosity=0)


@pytest.fixture
def api_client():
    return APIClient()
