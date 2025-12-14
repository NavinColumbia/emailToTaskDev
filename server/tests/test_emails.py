"""
Tests for email processing routes.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


def test_fetch_emails_unauthenticated(client):
    """Test fetching emails without authentication."""
    response = client.post("/fetch-emails")
    assert response.status_code == 401


@patch('server.routers.emails.get_gmail_service')
@patch('server.routers.emails.ml_decide')
def test_fetch_emails_authenticated(mock_ml_decide, mock_gmail_service, authenticated_client, test_db, sample_user):
    """Test fetching and processing emails."""
    # Mock Gmail service
    mock_service = MagicMock()
    mock_gmail_service.return_value = mock_service
    
    # Mock Gmail API responses
    mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [{"id": "test_msg_id"}]
    }
    
    mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
        "id": "test_msg_id",
        "threadId": "test_thread",
        "snippet": "Test snippet",
        "internalDate": str(int(datetime.now(timezone.utc).timestamp() * 1000)),
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Test Email"},
                {"name": "From", "value": "sender@example.com"},
            ],
            "body": {"data": ""},
        }
    }
    
    # Mock ML decision
    mock_ml_decide.return_value = {
        "should_create": True,
        "confidence": 0.9,
        "title": "Test Task",
        "notes": "Test notes",
        "reasoning": "Test reasoning",
        "category": None,
    }
    
    # Mock task creation
    with patch('server.routers.emails.dispatch_task') as mock_dispatch:
        mock_dispatch.return_value = {
            "id": "test_task_id",
            "title": "Test Task",
            "status": "needsAction",
        }
        
        response = authenticated_client.post_auth(
            "/fetch-emails",
            json={},
            query_string={"max": "1", "window": "1d"}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert "processed" in data
        assert "query" in data
        assert "created" in data


@patch('server.routers.emails.get_gmail_service')
def test_fetch_emails_not_authenticated(mock_gmail_service, authenticated_client):
    """Test fetching emails when Gmail service is not available."""
    mock_gmail_service.return_value = None
    
    response = authenticated_client.post_auth("/fetch-emails")
    assert response.status_code == 401


@patch('server.routers.emails.get_gmail_service')
@patch('server.routers.emails.ml_decide')
def test_fetch_emails_ml_skip(mock_ml_decide, mock_gmail_service, authenticated_client, test_db, sample_user):
    """Test that emails are skipped when ML decides not to create task."""
    mock_service = MagicMock()
    mock_gmail_service.return_value = mock_service
    
    mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [{"id": "test_msg_id"}]
    }
    
    mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
        "id": "test_msg_id",
        "threadId": "test_thread",
        "snippet": "Newsletter",
        "internalDate": str(int(datetime.now(timezone.utc).timestamp() * 1000)),
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Newsletter"},
                {"name": "From", "value": "newsletter@example.com"},
            ],
            "body": {"data": ""},
        }
    }
    
    # ML decides not to create task
    mock_ml_decide.return_value = {
        "should_create": False,
        "confidence": 0.1,
        "title": "Newsletter",
        "notes": "Newsletter content",
        "reasoning": "This is a newsletter, no action needed",
        "category": None,
    }
    
    response = authenticated_client.post_auth(
        "/fetch-emails",
        json={},
        query_string={"max": "1"}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["processed"] == 0  # No tasks created
