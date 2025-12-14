"""
Tests for ML classification functions.
"""
import pytest
from unittest.mock import patch, MagicMock
from server.ml import (
    clean_html_to_text,
    prepare_email_content,
    classify_and_generate_task,
    ml_decide,
)


def test_clean_html_to_text():
    """Test cleaning HTML to plain text."""
    html = """
    <html>
        <head><title>Test</title></head>
        <body>
            <p>Paragraph 1</p>
            <p>Paragraph 2</p>
            <br>
            <div>Div content</div>
        </body>
    </html>
    """
    
    text = clean_html_to_text(html)
    assert "Paragraph 1" in text
    assert "Paragraph 2" in text
    assert "Div content" in text
    assert "<html>" not in text
    assert "<p>" not in text


def test_prepare_email_content():
    """Test preparing email content for ML."""
    payload = {
        "subject": "Test Subject",
        "body": "Test body content",
        "html": "<p>HTML content</p>",
        "snippet": "Test snippet",
    }
    
    content = prepare_email_content(payload)
    assert content["subject"] == "Test Subject"
    assert content["body"] == "Test body content"
    assert content["snippet"] == "Test snippet"


def test_prepare_email_content_html_only():
    """Test preparing email content when only HTML is available."""
    payload = {
        "subject": "Test Subject",
        "html": "<p>HTML content</p>",
        "snippet": "Test snippet",
    }
    
    content = prepare_email_content(payload)
    assert content["subject"] == "Test Subject"
    assert "HTML content" in content["body"] or len(content["body"]) > 0


def test_prepare_email_content_long_body():
    """Test preparing email content with long body (truncation)."""
    long_body = "x" * 3000
    payload = {
        "subject": "Test Subject",
        "body": long_body,
    }
    
    content = prepare_email_content(payload)
    assert len(content["body"]) <= 2002  # 2000 + "..."


@patch('server.ml.OpenAI')
def test_classify_and_generate_task_with_openai(mock_openai_class):
    """Test email classification with OpenAI."""
    # Mock OpenAI client
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Mock API response
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(
            message=MagicMock(
                content='{"should_create": true, "confidence": 0.9, "title": "Test Task", "notes": "Test notes", "category": null, "reasoning": "Test reasoning", "meeting": {"is_meeting": false, "summary": "", "location": "", "start_datetime": "", "end_datetime": "", "participants": [], "category": null}}'
            )
        )]
    )
    
    payload = {
        "subject": "Please review this",
        "body": "This needs your attention",
        "sender": "boss@example.com",
    }
    
    result = classify_and_generate_task(
        payload,
        api_key="test-key",
        model="gpt-4o-mini"
    )
    
    assert result["should_create"] is True
    assert result["confidence"] == 0.9
    assert "title" in result


def test_classify_and_generate_task_no_openai():
    """Test email classification without OpenAI (fallback)."""
    payload = {
        "subject": "Test Subject",
        "body": "Test body",
    }
    
    # Temporarily disable OpenAI
    with patch('server.ml.OPENAI_AVAILABLE', False):
        result = classify_and_generate_task(payload, api_key=None)
        assert result["should_create"] is True
        assert result["title"] == "Test Subject"
        assert "reasoning" in result


def test_classify_and_generate_task_no_api_key():
    """Test email classification without API key (fallback)."""
    payload = {
        "subject": "Test Subject",
        "body": "Test body",
    }
    
    result = classify_and_generate_task(payload, api_key=None)
    assert result["should_create"] is True
    assert result["title"] == "Test Subject"


def test_ml_decide():
    """Test main ML decision function."""
    payload = {
        "subject": "Test Subject",
        "body": "Test body",
        "sender": "test@example.com",
    }
    
    with patch('server.ml.classify_and_generate_task') as mock_classify:
        mock_classify.return_value = {
            "should_create": True,
            "confidence": 0.8,
            "title": "Test Task",
            "notes": "Test notes",
            "category": None,
            "reasoning": "Test",
            "meeting": None,
        }
        
        result = ml_decide(payload)
        assert result["should_create"] is True
        assert result["confidence"] == 0.8


def test_ml_decide_with_categories():
    """Test ML decision with category filters."""
    payload = {
        "subject": "Work Task",
        "body": "Please complete this work task",
        "sender": "boss@example.com",
    }
    
    with patch('server.ml.classify_and_generate_task') as mock_classify:
        mock_classify.return_value = {
            "should_create": True,
            "confidence": 0.9,
            "title": "Work Task",
            "notes": "Complete this task",
            "category": "Work",
            "reasoning": "Work-related task",
            "meeting": None,
        }
        
        result = ml_decide(
            payload,
            task_categories=["Work", "Personal"],
            calendar_categories=["Meetings"]
        )
        assert result["should_create"] is True
        assert result["category"] == "Work"
