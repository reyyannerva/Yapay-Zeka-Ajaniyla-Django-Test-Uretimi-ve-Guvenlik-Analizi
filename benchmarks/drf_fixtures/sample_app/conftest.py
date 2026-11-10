"""pytest-django ortak fixture'ları — H3-01 / Issue #27."""
import pytest
from django.core.management import call_command
from rest_framework.test import APIClient


@pytest.fixture
def seeded_db(db):
    """Users + articles fixture'larını yükler (fixture'ların yüklenebilirliğini de doğrular)."""
    call_command("loaddata", "users", "articles", verbosity=0)


@pytest.fixture
def api():
    return APIClient()
