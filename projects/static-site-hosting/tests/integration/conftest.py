# tests/integration/conftest.py
"""
Integration test configuration.
Automatically sets up the test database for all integration tests.
"""
import pytest

# Import the shared DB fixture from root conftest
from tests.conftest import setup_test_database, db_session, test_user, seed_users, fake_user_data


@pytest.fixture(scope="session", autouse=True)
def _integration_db_setup(setup_test_database):
    """
    Auto-use wrapper that ensures integration tests have DB initialized.
    """
    yield
