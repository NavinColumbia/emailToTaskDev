"""
Tests for calendar routes.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta


def test_get_all_calendar_events_unauthenticated(client):
    """Test getting calendar events without authentication."""
    response = client.get("/calendar-events/all")
    assert response.status_code == 401


def test_get_calendar_events_with_category_filter(authenticated_client, test_db, sample_user, sample_email):
    """Test getting calendar events with category filter."""
    with test_db() as s:
        from server.db import CalendarEvent, Email
        
        email = Email(
            user_id=sample_user,
            gmail_message_id="test_msg_1",
            subject="Meeting Email",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        s.add(email)
        s.flush()
        
        event = CalendarEvent(
            user_id=sample_user,
            email_id=email.id,
            summary="Test Meeting",
            category="Work",
            status="created",
            created_at=datetime.now(timezone.utc),
        )
        s.add(event)
        s.flush()
    
    response = authenticated_client.get_auth("/calendar-events/all?category=Work")
    assert response.status_code == 200
    data = response.get_json()
    assert all(event["category"] == "Work" for event in data["events"])


def test_delete_calendar_events_unauthenticated(client):
    """Test deleting calendar events without authentication."""
    response = client.delete("/calendar-events", json={"event_ids": [1]})
    assert response.status_code == 401


