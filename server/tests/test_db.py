"""
Tests for database models and operations.
"""
import pytest
from datetime import datetime, timezone
from server.db import User, Email, Task, CalendarEvent, UserSettings


def test_user_creation(test_db, sample_user):
    """Test creating a user."""
    with test_db() as s:
        from sqlalchemy import select
        stmt = select(User).where(User.id == sample_user)
        user = s.execute(stmt).scalar_one()
        assert user.email == "test@example.com"
        assert user.id == sample_user
        assert user.created_at is not None
        assert user.updated_at is not None


def test_email_creation(test_db, sample_user, sample_email):
    """Test creating an email."""
    with test_db() as s:
        from sqlalchemy import select
        stmt = select(Email).where(Email.id == sample_email)
        email = s.execute(stmt).scalar_one()
        assert email.user_id == sample_user
        assert email.gmail_message_id == "test_message_id_123"
        assert email.subject == "Test Email Subject"
        assert email.sender == "sender@example.com"
        assert email.processed is False


def test_task_creation(test_db, sample_user, sample_email, sample_task):
    """Test creating a task."""
    with test_db() as s:
        from sqlalchemy import select
        stmt = select(Task).where(Task.id == sample_task)
        task = s.execute(stmt).scalar_one()
        assert task.user_id == sample_user
        assert task.email_id == sample_email
        assert task.provider == "google_tasks"
        assert task.provider_task_id == "test_task_id_123"
        assert task.status == "created"
        assert task.provider_metadata["title"] == "Test Task"


def test_calendar_event_creation(test_db, sample_user, sample_email, sample_calendar_event):
    """Test creating a calendar event."""
    with test_db() as s:
        from sqlalchemy import select
        stmt = select(CalendarEvent).where(CalendarEvent.id == sample_calendar_event)
        event = s.execute(stmt).scalar_one()
        assert event.user_id == sample_user
        assert event.email_id == sample_email
        assert event.google_event_id == "test_event_id_123"
        assert event.summary == "Test Meeting"
        assert event.status == "created"


def test_user_settings_creation(test_db, sample_user):
    """Test creating user settings."""
    with test_db() as s:
        settings = UserSettings(
            user_id=sample_user,
            provider="google_tasks",
            max=20,
            window="7d",
            task_categories=["Work", "Personal"],
            calendar_categories=["Meetings"],
            auto_generate=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        s.add(settings)
        s.flush()
        
        assert settings.user_id == sample_user
        assert settings.max == 20
        assert settings.window == "7d"
        assert settings.task_categories == ["Work", "Personal"]
        assert settings.auto_generate is True


def test_user_email_relationship(test_db, sample_user):
    """Test user-email relationship."""
    with test_db() as s:
        from sqlalchemy import select
        stmt = select(User).where(User.id == sample_user)
        user = s.execute(stmt).scalar_one()
        
        email = Email(
            user_id=user.id,
            gmail_message_id="test_msg_2",
            subject="Another email",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        s.add(email)
        s.flush()
        
        # Test relationship
        assert len(user.emails) >= 1
        assert email.user.email == "test@example.com"


def test_email_task_relationship(test_db, sample_user, sample_email, sample_task):
    """Test email-task relationship."""
    with test_db() as s:
        from sqlalchemy import select
        stmt = select(Task).where(Task.id == sample_task)
        task = s.execute(stmt).scalar_one()
        
        assert task.email.id == sample_email
        assert task.email.subject == "Test Email Subject"
