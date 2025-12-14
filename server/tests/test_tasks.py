"""
Tests for task routes.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


def test_get_all_tasks_unauthenticated(client):
    """Test getting tasks without authentication."""
    response = client.get("/tasks/all")
    assert response.status_code == 401


def test_get_all_tasks_authenticated(authenticated_client, test_db, sample_user, sample_email, sample_task):
    """Test getting all tasks with authentication."""
    response = authenticated_client.get_auth("/tasks/all")
    assert response.status_code == 200
    data = response.get_json()
    assert "tasks" in data
    assert "total" in data
    assert len(data["tasks"]) >= 1


def test_get_all_tasks_with_category_filter(authenticated_client, test_db, sample_user, sample_email):
    """Test getting tasks with category filter."""
    # Create tasks with different categories
    with test_db() as s:
        from server.db import Task, Email
        from sqlalchemy import select
        
        # Create email
        email = Email(
            user_id=sample_user,
            gmail_message_id="test_msg_1",
            subject="Test 1",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        s.add(email)
        s.flush()
        
        # Create task with category
        task1 = Task(
            user_id=sample_user,
            email_id=email.id,
            provider="google_tasks",
            category="Work",
            status="created",
            created_at=datetime.now(timezone.utc),
        )
        s.add(task1)
        s.flush()
    
    response = authenticated_client.get_auth("/tasks/all?category=Work")
    assert response.status_code == 200
    data = response.get_json()
    assert all(task["category"] == "Work" for task in data["tasks"])


def test_delete_tasks_unauthenticated(client):
    """Test deleting tasks without authentication."""
    response = client.delete("/tasks", json={"task_ids": [1]})
    assert response.status_code == 401


def test_delete_tasks_authenticated(authenticated_client, test_db, sample_user, sample_email, sample_task):
    """Test deleting tasks with authentication."""
    with patch('server.routers.tasks.get_tasks_service') as mock_service:
        mock_service.return_value = None
        
        response = authenticated_client.delete_auth(
            "/tasks",
            json={"task_ids": [sample_task]}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["deleted_count"] == 1


def test_delete_tasks_invalid_request(authenticated_client):
    """Test deleting tasks with invalid request."""
    response = authenticated_client.delete_auth("/tasks", json={})
    assert response.status_code == 400


def test_confirm_tasks_unauthenticated(client):
    """Test confirming tasks without authentication."""
    response = client.post("/tasks/confirm", json={"task_ids": [1]})
    assert response.status_code == 401


def test_confirm_tasks_authenticated(authenticated_client, test_db):
    """Test confirming pending tasks."""
    # Use get_or_create_user to ensure we use the same user that get_current_user() will find
    with test_db() as s:
        from server.db import Task, Email
        from server.utils import get_or_create_user
        
        # Get or create user (same way route handlers do it)
        user = get_or_create_user(s, "test@example.com")
        
        email = Email(
            user_id=user.id,
            gmail_message_id="test_msg_pending",
            subject="Pending Task",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        s.add(email)
        s.flush()
        
        task = Task(
            user_id=user.id,
            email_id=email.id,
            provider="google_tasks",
            status="pending",
            provider_metadata={
                "payload": {
                    "subject": "Test Task",
                    "body": "Test body",
                }
            },
            created_at=datetime.now(timezone.utc),
        )
        s.add(task)
        s.flush()
        task_id = task.id
    
    with patch('server.routers.tasks.get_tasks_service') as mock_service:
        mock_tasks_service = MagicMock()
        mock_service.return_value = mock_tasks_service
        
        # Mock tasklist creation
        mock_tasks_service.tasklists.return_value.list.return_value.execute.return_value = {
            "items": []
        }
        mock_tasks_service.tasklists.return_value.insert.return_value.execute.return_value = {
            "id": "test_list_id"
        }
        
        # Mock task creation
        mock_tasks_service.tasks.return_value.insert.return_value.execute.return_value = {
            "id": "new_task_id",
            "title": "Test Task",
            "status": "needsAction",
        }
        
        response = authenticated_client.post_auth(
            "/tasks/confirm",
            json={"task_ids": [task_id]}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["confirmed_count"] == 1
