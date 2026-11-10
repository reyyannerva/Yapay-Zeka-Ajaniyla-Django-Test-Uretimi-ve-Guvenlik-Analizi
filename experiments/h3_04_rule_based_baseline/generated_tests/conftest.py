"""Üretilen testlerin ortak fixture'ları — H3-04 / Issue #30 (otomatik üretilmiştir).

Her test kendi işlem (transaction) kapsamında çalışır; pytest-django her testten sonra veritabanını geri alır. Fixture verisi her test için yeniden yüklenir, böylece testler birbirine ve çalışma sırasına bağımlı değildir."""
import pytest
from django.core.management import call_command
from rest_framework.test import APIClient
FIXTURES = ['users', 'articles']

@pytest.fixture
def seeded_db(db):
    call_command('loaddata', *FIXTURES, verbosity=0)

@pytest.fixture
def api_client():
    return APIClient()
