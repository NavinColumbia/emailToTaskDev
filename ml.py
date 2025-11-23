"""
ML module for email classification and task generation.
Uses OpenAI API to:
1. Classify whether an email should become a task
2. Generate appropriate task title and body from email content
3. Detect whether an email should lead to a meeting
4. Generate appropriate meeting details from email
"""

from __future__ import annotations
import os
import json
import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import timezone, timedelta
from dateutil import parser as date_parser


try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def clean_html_to_text(html: str) -> str:
    """
    Convert HTML content to clean plain text.
    Handles common email HTML formatting.
    """
    if not html or not html.strip():
        return ""
    
    soup = BeautifulSoup(html, "lxml")
    
    # Remove script and style elements
    for element in soup(["script", "style", "meta", "link"]):
        element.decompose()
    
    # Handle line breaks
    for br in soup.find_all("br"):
        br.replace_with("\n")
    
    # Handle paragraphs
    for p in soup.find_all("p"):
        p.insert_after("\n")
    
    # Handle divs
    for div in soup.find_all("div"):
        div.insert_after("\n")
    
    # Get text and clean up extra whitespace
    text = soup.get_text("\n")
    
    # Clean up multiple newlines
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Clean up spaces
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(line for line in lines if line)
    
    return text.strip()


def prepare_email_content(payload: Dict[str, Any]) -> Dict[str, str]:
    """
    Prepare email content for ML processing.
    Extracts and cleans subject, body, and snippet.
    """
    subject = payload.get("subject", "")
    body = payload.get("body", "")
    html = payload.get("html", "")
    snippet = payload.get("snippet", "")
    
    # If body is empty but html exists, convert html to text
    if not body and html:
        body = clean_html_to_text(html)
    
    # Limit body length for API efficiency (keep first ~2000 chars)
    if len(body) > 2000:
        body = body[:2000] + "..."
    
    return {
        "subject": subject,
        "body": body,
        "snippet": snippet
    }


def classify_and_generate_task(
    payload: Dict[str, Any],
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini"
) -> Dict[str, Any]:
    """
    Main function to classify email and generate task details and meetings.
    
    Args:
        payload: Email payload containing subject, body, html, snippet, sender
        api_key: OpenAI API key (falls back to OPENAI_API_KEY env var)
        model: OpenAI model to use (default: gpt-4o-mini for cost efficiency)
    
    Returns:
        Dictionary with:
        - should_create: bool - whether to create a task
        - confidence: float - confidence score (0-1)
        - title: str - generated task title
        - notes: str - generated task description/body
        - reasoning: str - explanation of classification decision
        - meeting: dictoniary indicating if it should create a meeting, location, start and end time and participants.
    """
    if not OPENAI_AVAILABLE:
        # Fallback: create task with original content
        return {
            "should_create": True,
            "confidence": 0.5,
            "title": payload.get("subject", "Email Task"),
            "notes": payload.get("body", payload.get("snippet", "")),
            "reasoning": "OpenAI library not available, using default behavior"
        }
    
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Fallback: create task with original content
        return {
            "should_create": True,
            "confidence": 0.5,
            "title": payload.get("subject", "Email Task"),
            "notes": payload.get("body", payload.get("snippet", "")),
            "reasoning": "No OpenAI API key configured, using default behavior"
        }
    
    email_content = prepare_email_content(payload)
    sender = payload.get("sender", "Unknown")
    
    # Build prompt for classification and generation
    prompt = f"""
You are an intelligent email assistant that helps users manage their tasks and meetings by analyzing emails.

Instructions:

1. Determine if the email represents:
   a) a task to be created
   b) a meeting invitation

2. If it's a task:
   - Generate a concise task title (3-8 words)
   - Generate detailed task notes (2-4 sentences)
   - Provide a confidence score (0.0-1.0)
   - Explain your reasoning

3. If it's a meeting:
   - Detect if it is indeed a meeting (is_meeting: true/false)
   - Extract meeting details:
       * summary: meeting title
       * location: physical or virtual link (leave empty if unknown)
       * start_datetime: RFC3339 UTC start time (leave empty if unknown)
       * end_datetime: RFC3339 UTC end time (leave empty if unknown)
       * participants: list of email addresses (leave empty list if unknown)
   - Use context clues like "meeting", "invite", "agenda", "call", "Zoom", "conference", "link"

Email Details:
From: {sender}
Subject: {email_content['subject']}

Body:
{email_content['body'] or email_content['snippet']}

Classification Guidelines:
- CREATE TASK for emails that contain:
  * Action items or requests
  * Reminders or deadlines
  * Meeting invitations requiring preparation
  * Bills or payments due
  * Follow-up items
  * Tasks delegated to you
  * Important information that needs review or response

- DO NOT CREATE TASK for emails that are:
  * Pure newsletters or marketing
  * Automated notifications with no action needed
  * Spam or promotional content
  * Social media notifications
  * Purely informational with no action required
  * "FYI only" messages
  * Auto-replies or out-of-office messages

Respond ONLY with valid JSON in this exact format:
{{
  "should_create": true/false,
  "confidence": 0.0-1.0,
  "title": "Concise task title (3-8 words)",
  "notes": "Detailed task description with key information",
  "reasoning": "Brief explanation of decision",
  "meeting": {{
      "is_meeting": true/false,
      "summary": "",
      "location": "",
      "start_datetime": "",
      "end_datetime": "",
      "participants": []
  }}
}}

For task title:
- Make it actionable (start with a verb if appropriate)
- Keep it under 60 characters
- Remove "RE:", "FWD:", etc. prefixes

For task notes:
- Include key details, dates, or requirements
- Keep it concise but informative (2-4 sentences max)
- Extract actionable information from the email body
"""


    result: Dict[str, Any] = {}
    try:
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful email classification assistant. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent classification
            max_tokens=500,
            response_format={"type": "json_object"}  # Ensures JSON response
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        # Validate meeting field
        meeting_info = result.get("meeting")
        if meeting_info and meeting_info.get("is_meeting"):
            # If start_datetime is missing, attempt to extract it from the email body
            if not meeting_info.get("start_datetime"):
                start_dt, end_dt = extract_meeting_datetime(payload.get("body") or "")
                if start_dt:
                    meeting_info["start_datetime"] = start_dt
                    meeting_info["end_datetime"] = end_dt

      
        # Validate and sanitize response
        return {
            "should_create": bool(result.get("should_create", True)),
            "confidence": float(result.get("confidence", 0.5)),
            "title": str(result.get("title", email_content["subject"]))[:200],  # Limit length
            "notes": str(result.get("notes", email_content["body"] or email_content["snippet"]))[:2000],
            "reasoning": str(result.get("reasoning", ""))[:500],
            "meeting": result.get("meeting")
        }
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse OpenAI response as JSON: {e}")
        # Fallback to creating task
        return {
            "should_create": True,
            "confidence": 0.5,
            "title": email_content["subject"],
            "notes": email_content["body"] or email_content["snippet"],
            "reasoning": "JSON parsing failed, using fallback"
        }
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        # Fallback to creating task
        return {
            "should_create": True,
            "confidence": 0.5,
            "title": email_content["subject"],
            "notes": email_content["body"] or email_content["snippet"],
            "reasoning": f"API error: {str(e)}",
            "meeting": result.get("meeting") if isinstance(result, dict) else None
        }


def batch_classify_emails(
    payloads: list[Dict[str, Any]],
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini"
) -> list[Dict[str, Any]]:
    """
    Classify multiple emails in batch (sequentially).
    Can be extended to use async for better performance.
    
    Args:
        payloads: List of email payloads
        api_key: OpenAI API key
        model: OpenAI model to use
    
    Returns:
        List of classification results
    """
    results = []
    for payload in payloads:
        result = classify_and_generate_task(payload, api_key=api_key, model=model)
        results.append(result)
    return results


# Convenience function for app.py
def ml_decide(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for email classification.
    Uses environment variables for configuration.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    result = classify_and_generate_task(payload, api_key=api_key, model=model)
    
    meeting_info = result.get("meeting")
    if meeting_info:
        required_keys = ["is_meeting", "summary", "start_datetime", "end_datetime"]
        if not all(k in meeting_info for k in required_keys):
            result["meeting"] = None
    return result
