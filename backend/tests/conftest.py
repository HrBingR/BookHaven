import pytest
import os
from alembic.config import Config
from unittest.mock import patch
from datetime import datetime, timezone
from bcrypt import hashpw, gensalt
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3
from celery_app import make_celery
from config.config import config

from routes.auth import generate_token

# Define all patches at module level
patch_settings = {
    "SECRET_KEY": "7959a31210e1d1e4a408b250d633ec0d861225e2d96c8f6a17f28f1961e672e3",
    "BASE_URL": "http://localhost:5001",
    "ADMIN_PASS": "P@ssw0rd",
    "DB_TYPE": "test",
    "ADMIN_EMAIL": "test@example.com",
    "ENVIRONMENT": "test",
    "ALLOW_UNAUTHENTICATED": "true"
}

# Create patch objects
patches = [
    patch(f"config.config.config.{key}", value)
    for key, value in patch_settings.items()
]

def pytest_sessionfinish(session, exitstatus):
    """
    Clean up after all tests are done.
    """
    # Stop all patches
    for p in patches:
        p.stop()
    print("Patches stopped")

    # Delete the test database file
    try:
        if os.path.exists("tests/test.db"):
            os.remove("tests/test.db")
            print("Test database removed")
    except Exception as e:
        print(f"Warning: Could not remove test database: {e}")

@pytest.fixture(scope="session")
def celery_config():
    return {
        'broker_url': 'memory://',
        'result_backend': 'cache+memory://',
        "task_always_eager": True,  # Execute tasks synchronously
        "task_eager_propagates": True,  # Propagate exceptions
    }


@pytest.fixture(scope="session")
def celery_worker(celery_app, celery_worker_parameters):
    """
    Fixture to run a Celery worker for testing tasks.
    """
    from celery.contrib.testing.worker import start_worker

    # Start the Celery worker with the app and parameters provided
    with start_worker(celery_app, **celery_worker_parameters) as worker:
        yield worker

@pytest.fixture(scope="session")
def celery_parameters():
    # Provide parameters for the Celery app or worker during testing
    return {
        # Example: add options for concurrency or workers (not required here)
        # Options like 'config_source', worker pool type, etc., can go here
    }

@pytest.fixture(scope="session")
def celery_enable_logging():
    # Return True to enable Celery logging during tests, False to disable it
    return True  # Enable logging (or False if not needed)

@pytest.fixture(scope="session")
def use_celery_app_trap():
    return False

@pytest.fixture(scope="session")
def celery_worker_pool():
    return "solo"

@pytest.fixture(scope="session")
def celery_worker_parameters():
    return {
        "concurrency": 1,  # Run Celery workers with a single concurrency process/thread
        "loglevel": "INFO",  # Set the worker log level
        "perform_ping_check": False  # Avoid unnecessary ping checks during tests
    }

@pytest.fixture(scope='session')
def celery_includes():
    return ['functions.tasks.scan']

@pytest.fixture(scope='session')
def celery_app():
    celery = make_celery()
    return celery

@pytest.fixture(scope="session", autouse=True)
def patch_config():
    """Initialize all patches before any tests run"""
    print("Starting patches")
    # Start all patches
    mocks = [p.start() for p in patches]

    # Now import everything after patches are active
    from config.config import config
    from functions.db import get_database_url

    yield

    # Stop all patches after tests complete
    for p in patches:  # Use the original patch objects to stop
        p.stop()
    print("Patches stopped")


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_test_engine():
    """Get a singleton engine for testing"""
    from functions.db import get_database_url
    from sqlalchemy import create_engine
    if not hasattr(get_test_engine, "_engine"):
        get_test_engine._engine = create_engine(
            get_database_url(),
            connect_args={"check_same_thread": False},  # Allow multiple threads to use the same connection
        )
    return get_test_engine._engine


def run_migrations():
    """
    Run Alembic migrations against the shared test database.
    """
    from functions.db import get_database_url
    from models.base import Base
    import alembic.command

    print("Starting Alembic migrations")

    # Get the shared engine
    engine = get_test_engine()

    # Create all tables directly
    Base.metadata.drop_all(engine)  # Clear existing tables
    Base.metadata.create_all(engine)  # Create new tables

    # Create Alembic configuration and stamp head
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", get_database_url())

    try:
        alembic.command.stamp(alembic_cfg, "head")
    except Exception as e:
        print(f"Warning: Failed to stamp database version: {e}")


@pytest.fixture(scope="session")
def test_engine():
    """Provide a shared engine for all tests"""
    return get_test_engine()


@pytest.fixture(scope='session')
def test_session_maker(test_engine):
    """Create a shared session maker"""
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=test_engine)
    return SessionLocal


@pytest.fixture(scope="session", autouse=True)
def setup_database(patch_config, test_engine, test_session_maker):
    """
    Ensure Alembic migrations are applied to the shared test database before any tests.
    """
    from models.users import Users
    from models.progress_mapping import ProgressMapping
    from models.epub_metadata import EpubMetadata  # Add this import
    from models.base import Base
    Base.metadata.drop_all(test_engine)  # Clear existing tables
    Base.metadata.create_all(test_engine)  # Create new tables

    run_migrations()

    # Use the shared session maker
    session = test_session_maker()

    try:
        # Create admin user
        hashed_password = hashpw("P@ssw0rd".encode('utf-8'), gensalt()).decode('utf-8')
        admin_user = Users(
            id=2,
            username="administrator",
            email="test@example.com",
            password_hash=hashed_password,
            is_admin=True
        )
        other_user = Users(
            id=50,
            username="other",
            email="other@example.com",
            password_hash=hashed_password,
            is_admin=False
        )
        other_user2 = Users(
            id=51,
            username="other2",
            email="other2@example.com",
            password_hash=hashed_password,
            auth_type="oidc",
            is_admin=False
        )
        totp_user = Users(
            id=49,
            username="totp_user",
            email="totp@example.com",
            password_hash=hashed_password,
            mfa_enabled=True,
            mfa_secret="gAAAAABnjOwcZtzHFzIsOj2PRs7tyeJCeeZWOwrC8Nyp1DpVqMN1Lx-BuDD3r1UVVsn9dd0LijbpCDqBQSNyPAp1i7wWyVQp_A==",
        )
        other_user3 = Users(
            id=53,
            username="other3",
            email="other3@example.com",
            password_hash=hashed_password,
            auth_type="local",
            is_admin=False
        )
        session.add(totp_user)
        session.add(admin_user)
        session.add(other_user)
        session.add(other_user2)
        session.add(other_user3)
        session.flush()  # Ensure user is created before creating dependent records

        # Create a test book
        test_book = EpubMetadata(
            id=1,
            identifier="61cee114-a920-4427-809f-50da0678c004",
            title="Test Book",
            authors="Author One",
            series="Test Series",
            seriesindex=1.0,
            relative_path="/path/to/test.epub"
        )
        test_book_2 = EpubMetadata(
            id=50,
            identifier="29c52cdf-3bb8-4a69-8e36-67c865fa45e6",
            title="Test Book 2",
            authors="Author Two",
            series="Test Series 2",
            seriesindex=2.0,
            relative_path="/path/to/test2.epub"
        )
        session.add(test_book)
        session.add(test_book_2)
        session.flush()  # Ensure book is created before creating progress mapping

        # Now create the progress mapping
        progress = ProgressMapping(
            id=1,
            user_id=admin_user.id,  # Use the actual user id
            book_id=test_book.id,  # Use the actual book id
            progress="20",
            is_finished=True,
            marked_favorite=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(progress)

        session.commit()
    except Exception as e:
        print(f"Error setting up test data: {e}")
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture(scope='session')
def app(patch_config):
    from main import create_app
    flask_app = create_app()

    flask_app.config.update({
        "TESTING": True,
        "FLASK_RUN_PORT": 5001,
    })
    return flask_app


@pytest.fixture(scope='function')
def db_session(test_session_maker):
    """Provide a transactional scope around tests"""
    session = test_session_maker()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def headers():
    from routes.auth import generate_token
    token = generate_token(user_id=2, user_is_admin=True, user_email="test@example.com")
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

@pytest.fixture
def form_headers():
    token = generate_token(user_id=2, user_is_admin=True, user_email="test@example.com")
    return {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {token}"
    }

@pytest.fixture
def form_with_image_headers():
    token = generate_token(user_id=2, user_is_admin=True, user_email="test@example.com")
    return {
        "Content-Type": "multipart/form-data",
        "Authorization": f"Bearer {token}"
    }

def generate_expired_token(user_id, user_is_admin):
    import jwt
    from datetime import datetime, timezone, timedelta
    return jwt.encode(
        {'user_id': user_id, 'user_is_admin':user_is_admin, 'exp': datetime.now(timezone.utc) - timedelta(hours=24)},
        config.SECRET_KEY,
        algorithm='HS256'
    )

@pytest.fixture
def headers_expired():
    token = generate_expired_token(user_id=2, user_is_admin=True)
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

@pytest.fixture
def headers_invalid_user():
    from routes.auth import generate_token
    token = generate_token(user_id=500, user_is_admin=True, user_email="lolno@example.com")
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

@pytest.fixture
def headers_other_user():
    from routes.auth import generate_token
    token = generate_token(user_id=50, user_is_admin=True, user_email="other@example.com")
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

@pytest.fixture
def headers_other_user2():
    from routes.auth import generate_token
    token = generate_token(user_id=51, user_is_admin=False, user_email="other@example.com")
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
@pytest.fixture
def headers_other_user3():
    from routes.auth import generate_token
    token = generate_token(user_id=53, user_is_admin=False, user_email="other3@example.com")
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

@pytest.fixture
def headers_non_admin():
    from routes.auth import generate_token
    token = generate_token(user_id=2, user_is_admin=False, user_email="test@example.com")
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

@pytest.fixture
def headers_media_test():
    from routes.auth import generate_token
    token = generate_token(user_id=2, user_is_admin=True, user_email="test@example.com")
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "file": "not_found"
    }

@pytest.fixture
def headers_totp():
    from routes.auth import generate_totp_token
    token = generate_totp_token(user_id=2)
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }