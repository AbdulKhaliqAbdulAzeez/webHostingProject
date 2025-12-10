# tests/e2e/conftest.py
"""
End-to-end test configuration.
Automatically sets up the test database and FastAPI server for e2e tests.
"""
import pytest

# Import the shared fixtures from root conftest
from tests.conftest import (
    setup_test_database,
    fastapi_server,
    browser_context,
    page,
    db_session,
    test_user,
    fake_user_data,
)


@pytest.fixture(scope="session", autouse=True)
def _e2e_setup(setup_test_database, fastapi_server):
    """
    Auto-use wrapper that ensures e2e tests have DB and server ready.
    """
    yield
