"""
Tests for authentication routes.
"""
import pytest
from unittest.mock import patch, MagicMock
from server.utils import encode_jwt, decode_jwt


def test_encode_decode_jwt():
    """Test JWT encoding and decoding."""
    email = "test@example.com"
    token = encode_jwt(email)
    assert token is not None
    
    payload = decode_jwt(token)
    assert payload is not None
    assert payload["email"] == email


def test_decode_invalid_jwt():
    """Test decoding invalid JWT."""
    payload = decode_jwt("invalid_token")
    assert payload is None


def test_auth_status_unauthenticated(client):
    """Test auth status endpoint without authentication."""
    response = client.get("/auth/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data["authenticated"] is False


def test_auth_status_authenticated(authenticated_client):
    """Test auth status endpoint with authentication."""
    response = authenticated_client.get_auth("/auth/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data["authenticated"] is True


def test_user_info_unauthenticated(client):
    """Test user info endpoint without authentication."""
    response = client.get("/user")
    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data


def test_user_info_authenticated(authenticated_client):
    """Test user info endpoint with authentication."""
    response = authenticated_client.get_auth("/user")
    assert response.status_code == 200
    data = response.get_json()
    assert data["authenticated"] is True


@patch('server.routers.auth._create_flow')
def test_authorize_route(mock_create_flow, client):
    """Test authorize route redirects to Google OAuth."""
    mock_flow = MagicMock()
    mock_flow.authorization_url.return_value = (
        "https://accounts.google.com/o/oauth2/auth?test=1",
        "test_state"
    )
    mock_create_flow.return_value = mock_flow
    
    response = client.get("/authorize", follow_redirects=False)
    # Should redirect to Google OAuth
    assert response.status_code in [302, 307]


def test_logout_route(client):
    """Test logout route."""
    response = client.post("/logout")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
