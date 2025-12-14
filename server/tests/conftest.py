"""
Pytest configuration and fixtures for backend tests.
"""
import os
import pytest
import tempfile
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet

# Set test environment variables before importing app modules
os.environ["FLASK_ENV"] = "test"
os.environ["FLASK_SECRET"] = "test-secret-key"
os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode()
os.environ["GOOGLE_CLIENT_SECRETS_JSON"] = '{"web": {"client_id": "test", "client_secret": "test", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token"}}'
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["OPENAI_MODEL"] = "gpt-4o-mini"

# Import after setting env vars
from server.db import Base, db_session, User, Email, Task, CalendarEvent, UserSettings
from server.app import app as flask_app


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database for each test."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    db_url = f"sqlite:///{db_path}"
    
    # Create engine and session
    engine = create_engine(db_url, pool_pre_ping=True, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    
    # Create tables
    Base.metadata.create_all(engine)
    
    # Override the db_session context manager for this test
    import server.db
    original_db_session = server.db.db_session
    
    @contextmanager
    def test_db_session():
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
    
    # Monkey patch db_session for this test
    server.db.db_session = test_db_session
    
    yield test_db_session
    
    # Cleanup
    server.db.db_session = original_db_session
    Base.metadata.drop_all(engine)
    engine.dispose()
    os.close(db_fd)
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client for the Flask app."""
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def sample_user(test_db):
    """Create a sample user for testing."""
    with test_db() as s:
        user = User(
            email="test@example.com",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        s.add(user)
        s.flush()
        user_id = user.id
        s.expunge(user)
        return user_id


@pytest.fixture
def authenticated_client(client, sample_user):
    """Create an authenticated test client with JWT token."""
    from server.utils import encode_jwt
    
    token = encode_jwt("test@example.com")
    
    def make_request(method, url, **kwargs):
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Bearer {token}'
        kwargs['headers'] = headers
        return getattr(client, method.lower())(url, **kwargs)
    
    client.get_auth = lambda url, **kwargs: make_request('GET', url, **kwargs)
    client.post_auth = lambda url, **kwargs: make_request('POST', url, **kwargs)
    client.put_auth = lambda url, **kwargs: make_request('PUT', url, **kwargs)
    client.delete_auth = lambda url, **kwargs: make_request('DELETE', url, **kwargs)
    
    return client


@pytest.fixture
def sample_email(test_db, sample_user):
    """Create a sample email for testing."""
    with test_db() as s:
        email = Email(
            user_id=sample_user,
            gmail_message_id="test_message_id_123",
            subject="Test Email Subject",
            sender="sender@example.com",
            received_at=datetime.now(timezone.utc),
            snippet="Test snippet",
            body="Test body",
            processed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        s.add(email)
        s.flush()
        email_id = email.id
        s.expunge(email)
        return email_id


@pytest.fixture
def sample_task(test_db, sample_user, sample_email):
    """Create a sample task for testing."""
    with test_db() as s:
        task = Task(
            user_id=sample_user,
            email_id=sample_email,
            provider="google_tasks",
            provider_task_id="test_task_id_123",
            provider_metadata={"title": "Test Task", "webLink": "https://tasks.google.com/test"},
            status="created",
            created_at=datetime.now(timezone.utc),
        )
        s.add(task)
        s.flush()
        task_id = task.id
        s.expunge(task)
        return task_id


@pytest.fixture
def sample_calendar_event(test_db, sample_user, sample_email):
    """Create a sample calendar event for testing."""
    with test_db() as s:
        event = CalendarEvent(
            user_id=sample_user,
            email_id=sample_email,
            google_event_id="test_event_id_123",
            summary="Test Meeting",
            location="Test Location",
            start_datetime=datetime.now(timezone.utc),
            end_datetime=datetime.now(timezone.utc),
            html_link="https://calendar.google.com/test",
            provider_metadata={"id": "test_event_id_123"},
            status="created",
            created_at=datetime.now(timezone.utc),
        )
        s.add(event)
        s.flush()
        event_id = event.id
        s.expunge(event)
        return event_id
