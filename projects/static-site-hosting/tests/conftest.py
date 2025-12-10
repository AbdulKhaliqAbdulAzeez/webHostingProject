"""
Shared test configuration for integration and e2e tests.
Unit tests have their own conftest in tests/unit/conftest.py.
"""
import os
import socket
import subprocess
import time
import logging
from typing import Generator, Dict, List
from contextlib import contextmanager

import pytest
import requests
from faker import Faker

# ======================================================================================
# Logging Configuration
# ======================================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ======================================================================================
# Lazy Database Imports (only when actually needed)
# ======================================================================================
# These are loaded lazily to avoid import-time database connections
# that would break unit tests running without a database.

_db_engine = None
_db_sessionmaker = None


def _get_db_engine():
    """Lazy load database engine only when needed."""
    global _db_engine
    if _db_engine is None:
        from app.database import get_engine
        from app.core.config import settings
        _db_engine = get_engine(database_url=settings.DATABASE_URL)
    return _db_engine


def _get_db_sessionmaker():
    """Lazy load sessionmaker only when needed."""
    global _db_sessionmaker
    if _db_sessionmaker is None:
        from app.database import get_sessionmaker
        _db_sessionmaker = get_sessionmaker(engine=_get_db_engine())
    return _db_sessionmaker


# Only import Playwright if available (not installed for unit/integration CI)
try:
    from playwright.sync_api import sync_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    sync_playwright = None
    Browser = None
    Page = None

# ======================================================================================
# Database Configuration (Lazy)
# ======================================================================================
fake = Faker()
Faker.seed(12345)

# ======================================================================================
# Helper Functions
# ======================================================================================
def create_fake_user() -> Dict[str, str]:
    """Generate a dictionary of fake user data for testing."""
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.unique.email(),
        "username": fake.unique.user_name(),
        "password": fake.password(length=12)
    }

@contextmanager
def managed_db_session():
    """Context manager for safe database session handling."""
    from sqlalchemy.exc import SQLAlchemyError
    SessionLocal = _get_db_sessionmaker()
    session = SessionLocal()
    try:
        yield session
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

# ======================================================================================
# Server Startup / Healthcheck
# ======================================================================================
def wait_for_server(url: str, timeout: int = 30) -> bool:
    """
    Wait for the server to be ready by repeatedly issuing GET requests until
    we receive a 200 status code or hit the timeout.
    """
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    return False

class ServerStartupError(Exception):
    """Raised when the test server fails to start properly."""
    pass

# ======================================================================================
# Database Fixtures
# ======================================================================================
@pytest.fixture(scope="session")
def setup_test_database(request):
    """
    Set up the test database before the session starts, and tear it down after tests
    unless --preserve-db is provided.

    NOTE: This is NOT autouse; only integration/e2e tests should request it.
    """
    from app.database import Base
    from app.database_init import init_db, drop_db

    test_engine = _get_db_engine()

    logger.info("Setting up test database...")
    try:
        Base.metadata.drop_all(bind=test_engine)
        Base.metadata.create_all(bind=test_engine)
        init_db()
        logger.info("Test database initialized.")
    except Exception as e:
        logger.error(f"Error setting up test database: {str(e)}")
        raise

    yield  # Tests run after this

    if not request.config.getoption("--preserve-db"):
        logger.info("Dropping test database tables...")
        drop_db()

@pytest.fixture
def db_session():
    """
    Provide a test-scoped database session. Commits after a successful test;
    rolls back if an exception occurs.
    """
    from sqlalchemy.orm import Session
    SessionLocal = _get_db_sessionmaker()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# ======================================================================================
# Test Data Fixtures
# ======================================================================================
@pytest.fixture
def fake_user_data() -> Dict[str, str]:
    """Provide fake user data."""
    return create_fake_user()

@pytest.fixture
def test_user(db_session):
    """
    Create and return a single test user in the database.
    """
    from app.models.user import User
    user_data = create_fake_user()
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    logger.info(f"Created test user ID: {user.id}")
    return user

@pytest.fixture
def seed_users(db_session, request) -> List:
    """
    Seed multiple test users in the database. By default, 5 users are created
    unless a 'param' value is provided (e.g., via @pytest.mark.parametrize).
    """
    from app.models.user import User
    num_users = getattr(request, "param", 5)
    users = [User(**create_fake_user()) for _ in range(num_users)]
    db_session.add_all(users)
    db_session.commit()
    logger.info(f"Seeded {len(users)} users.")
    return users

# ======================================================================================
# FastAPI Server Fixture
# ======================================================================================
def find_available_port() -> int:
    """Find an available port for the test server by binding to port 0."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

@pytest.fixture(scope="session")
def fastapi_server():
    """
    Start a FastAPI test server in a subprocess. If the chosen port (default: 8000)
    is already in use, find another available port. Wait until the server is up
    before yielding its base URL.
    """
    base_port = 8000
    server_url = f'http://127.0.0.1:{base_port}/'

    # Check if port is free; if not, pick an available port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('127.0.0.1', base_port)) == 0:
            base_port = find_available_port()
            server_url = f'http://127.0.0.1:{base_port}/'

    logger.info(f"Starting FastAPI server on port {base_port}...")

    process = subprocess.Popen(
        ['uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', str(base_port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd='.'  # ensure the working directory is set correctly
    )

    # IMPORTANT: Use the /health endpoint for the check!
    health_url = f"{server_url}health"
    if not wait_for_server(health_url, timeout=30):
        stderr = process.stderr.read()
        logger.error(f"Server failed to start. Uvicorn error: {stderr}")
        process.terminate()
        raise ServerStartupError(f"Failed to start test server on {health_url}")

    logger.info(f"Test server running on {server_url}.")
    yield server_url

    logger.info("Stopping test server...")
    process.terminate()
    try:
        process.wait(timeout=5)
        logger.info("Test server stopped.")
    except subprocess.TimeoutExpired:
        process.kill()
        logger.warning("Test server forcefully stopped.")

# ======================================================================================
# Playwright Fixtures for UI Testing
# ======================================================================================
@pytest.fixture(scope="session")
def browser_context():
    """Provide a Playwright browser context for UI tests (session-scoped)."""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not installed; skipping browser tests")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        logger.info("Playwright browser launched.")
        try:
            yield browser
        finally:
            logger.info("Closing Playwright browser.")
            browser.close()

@pytest.fixture
def page(browser_context: Browser):
    """
    Provide a new browser page for each test, with a standard viewport.
    Closes the page and context after each test.
    """
    context = browser_context.new_context(
        viewport={'width': 1920, 'height': 1080},
        ignore_https_errors=True
    )
    page = context.new_page()
    logger.info("New browser page created.")
    try:
        yield page
    finally:
        logger.info("Closing browser page and context.")
        page.close()
        context.close()

# ======================================================================================
# Pytest Command-Line Options
# ======================================================================================
def pytest_addoption(parser):
    """
    Add custom command line options:
      --preserve-db : Keep test database after tests
      --run-slow    : Run tests marked as 'slow'
    """
    parser.addoption("--preserve-db", action="store_true", help="Keep test database after tests")
    parser.addoption("--run-slow", action="store_true", help="Run tests marked as slow")

def pytest_collection_modifyitems(config, items):
    """
    Skip tests marked as 'slow' unless --run-slow is specified.
    """
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="use --run-slow to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
