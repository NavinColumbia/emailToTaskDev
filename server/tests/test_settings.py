"""
Tests for settings routes.
"""
import pytest


def test_get_settings_unauthenticated(client):
    """Test getting settings without authentication."""
    response = client.get("/settings")
    assert response.status_code == 401


def test_get_settings_authenticated_no_settings(authenticated_client, test_db, sample_user):
    """Test getting settings when none exist (should return defaults)."""
    response = authenticated_client.get_auth("/settings")
    assert response.status_code == 200
    data = response.get_json()
    assert data["max"] == 10
    assert data["window"] == "1d"
    assert data["auto_generate"] is True
    assert data["task_categories"] == []
    assert data["calendar_categories"] == []


def test_get_settings_authenticated_with_settings(authenticated_client, test_db, sample_user):
    """Test getting existing settings."""
    # Create settings first
    with test_db() as s:
        from server.db import UserSettings
        from datetime import datetime, timezone
        
        settings = UserSettings(
            user_id=sample_user,
            provider="google_tasks",
            max=20,
            window="7d",
            task_categories=["Work"],
            calendar_categories=["Meetings"],
            auto_generate=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        s.add(settings)
        s.flush()
    
    response = authenticated_client.get_auth("/settings")
    assert response.status_code == 200
    data = response.get_json()
    assert data["max"] == 20
    assert data["window"] == "7d"
    assert data["auto_generate"] is False
    assert "Work" in data["task_categories"]
    assert "Meetings" in data["calendar_categories"]


def test_update_settings_unauthenticated(client):
    """Test updating settings without authentication."""
    response = client.put("/settings", json={"max": 15})
    assert response.status_code == 401


def test_update_settings_authenticated(authenticated_client, test_db, sample_user):
    """Test updating settings."""
    response = authenticated_client.put_auth(
        "/settings",
        json={
            "max": 25,
            "window": "30d",
            "task_categories": ["Work", "Personal"],
            "calendar_categories": ["Meetings"],
            "auto_generate": False,
        }
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["max"] == 25
    assert data["window"] == "30d"
    assert data["auto_generate"] is False
    assert len(data["task_categories"]) == 2
    assert "Work" in data["task_categories"]
    assert "Personal" in data["task_categories"]


def test_update_settings_invalid_request(authenticated_client):
    """Test updating settings with invalid request."""
    response = authenticated_client.put_auth("/settings", json={})
    assert response.status_code == 400
