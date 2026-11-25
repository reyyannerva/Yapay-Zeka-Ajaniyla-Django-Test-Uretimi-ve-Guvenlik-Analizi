import pytest
from django.core.management import call_command


@pytest.fixture
def seeded_db(db):
    call_command("loaddata", "users", "tasks", verbosity=0)
