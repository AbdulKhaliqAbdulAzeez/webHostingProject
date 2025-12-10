# tests/unit/conftest.py
"""
Unit test configuration.
Unit tests must NOT depend on external services (DB, Redis, browsers).
This conftest intentionally does not import DB or Playwright fixtures.
"""
import pytest
from faker import Faker

# Seed Faker for reproducibility
Faker.seed(12345)

@pytest.fixture
def fake():
    """Provide a seeded Faker instance."""
    return Faker()
