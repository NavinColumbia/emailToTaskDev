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


def test_get_all_calendar_events_authenticated(authenticated_client, test_db, sample_user, sample_email, sample_calendar_event):
    """Test getting all calendar events with authentication."""
    response = authenticated_client.get_auth("/calendar-events/all")
    assert response.status_code == 200
    data = response.get_json()
    assert "events" in data
    assert "total" in data
    assert len(data["events"]) >= 1


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


def test_delete_calendar_events_authenticated(authenticated_client, test_db, sample_user, sample_email, sample_calendar_event):
    """Test deleting calendar events with authentication."""
    with patch('server.routers.calendar.get_calendar_service') as mock_service:
        mock_calendar_service = MagicMock()
        mock_service.return_value = mock_calendar_service
        
        response = authenticated_client.delete_auth(
            "/calendar-events",
            json={"event_ids": [sample_calendar_event]}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["deleted_count"] == 1


def test_confirm_calendar_events_authenticated(authenticated_client, test_db, sample_user, sample_email):
    """Test confirming pending calendar events."""
    with test_db() as s:
        from server.db import CalendarEvent, Email
        
        email = Email(
            user_id=sample_user,
            gmail_message_id="test_msg_pending",
            subject="Meeting Invitation",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        s.add(email)
        s.flush()
        
        event = CalendarEvent(
            user_id=sample_user,
            email_id=email.id,
            summary="Pending Meeting",
            status="pending",
            provider_metadata={
                "summary": "Pending Meeting",
                "start_datetime": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                "end_datetime": (datetime.now(timezone.utc) + timedelta(days=1, hours=1)).isoformat(),
                "client_timezone": "UTC",
            },
            created_at=datetime.now(timezone.utc),
        )
        s.add(event)
        s.flush()
        event_id = event.id
    
    with patch('server.routers.calendar.get_calendar_service') as mock_service:
        mock_calendar_service = MagicMock()
        mock_service.return_value = mock_calendar_service
        
        # Mock calendar event creation
        mock_calendar_service.events.return_value.insert.return_value.execute.return_value = {
            "id": "new_event_id",
            "summary": "Pending Meeting",
            "htmlLink": "https://calendar.google.com/test",
            "start": {
                "dateTime": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": (datetime.now(timezone.utc) + timedelta(days=1, hours=1)).isoformat(),
                "timeZone": "UTC"
            },
        }
        
        response = authenticated_client.post_auth(
            "/calendar-events/confirm",
            json={"event_ids": [event_id]}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["confirmed_count"] == 1
