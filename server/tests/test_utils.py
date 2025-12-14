"""
Tests for utility functions.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from server.utils import (
    encode_jwt,
    decode_jwt,
    get_jwt_from_request,
    message_to_payload,
    get_or_create_user,
)


def test_encode_decode_jwt():
    """Test JWT encoding and decoding."""
    email = "test@example.com"
    token = encode_jwt(email)
    assert token is not None
    
    payload = decode_jwt(token)
    assert payload is not None
    assert payload["email"] == email


def test_decode_expired_jwt():
    """Test decoding expired JWT."""
    from datetime import timedelta
    import jwt
    from server.config import FLASK_SECRET
    
    # Create expired token
    payload = {
        "email": "test@example.com",
        "exp": datetime.now(timezone.utc) - timedelta(days=1),
        "iat": datetime.now(timezone.utc) - timedelta(days=2),
    }
    token = jwt.encode(payload, FLASK_SECRET, algorithm="HS256")
    
    result = decode_jwt(token)
    assert result is None


def test_message_to_payload():
    """Test converting Gmail message to payload."""
    message = {
        "id": "test_id",
        "threadId": "test_thread",
        "snippet": "Test snippet",
        "internalDate": str(int(datetime.now(timezone.utc).timestamp() * 1000)),
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Test Subject"},
                {"name": "From", "value": "sender@example.com"},
            ],
            "body": {"data": ""},
        }
    }
    
    payload = message_to_payload(message)
    assert payload["subject"] == "Test Subject"
    assert payload["sender"] == "sender@example.com"
    assert payload["snippet"] == "Test snippet"
    assert payload["thread_id"] == "test_thread"


def test_get_or_create_user(test_db):
    """Test getting or creating a user."""
    with test_db() as s:
        # Create new user
        user1 = get_or_create_user(s, "newuser@example.com")
        assert user1.email == "newuser@example.com"
        
        # Get existing user
        user2 = get_or_create_user(s, "newuser@example.com")
        assert user2.id == user1.id
        assert user2.email == user1.email


def test_get_header():
    """Test getting header from payload."""
    from server.utils import get_header
    
    payload = {
        "headers": [
            {"name": "Subject", "value": "Test Subject"},
            {"name": "From", "value": "sender@example.com"},
        ]
    }
    
    assert get_header(payload, "Subject") == "Test Subject"
    assert get_header(payload, "From") == "sender@example.com"
    assert get_header(payload, "To") is None
    assert get_header(payload, "subject") == "Test Subject"  # Case insensitive


def test_html_to_text():
    """Test converting HTML to text."""
    from server.utils import html_to_text
    
    html = "<p>Test paragraph</p><br>Line break"
    text = html_to_text(html)
    assert "Test paragraph" in text
    assert "Line break" in text
