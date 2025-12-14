from __future__ import annotations
import os
import json
import re
import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def clean_html_to_text(html: str) -> str:
    if not html or not html.strip():
        return ""
    
    soup = BeautifulSoup(html, "lxml")
    
    for element in soup(["script", "style", "meta", "link"]):
        element.decompose()
    
    for br in soup.find_all("br"):
        br.replace_with("\n")
    
    for p in soup.find_all("p"):
        p.insert_after("\n")
    
    for div in soup.find_all("div"):
        div.insert_after("\n")
    
    text = soup.get_text("\n")
    
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
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
    
    if not body and html:
        body = clean_html_to_text(html)
    
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
    model: str = "gpt-4o-mini",
    task_categories: list[str] | None = None,
    calendar_categories: list[str] | None = None,
) -> Dict[str, Any]:
    """
    Main function to classify email and generate task details and meetings.
    """
    subject = payload.get("subject", "(No subject)")
    
    if not OPENAI_AVAILABLE:
        logger.warning(
            f"Classification skipped - Subject: '{subject}' | "
            f"Reason: OpenAI library not available, using default behavior"
        )
        return {
            "should_create": True,
            "confidence": 0.5,
            "title": payload.get("subject", "Email Task"),
            "notes": payload.get("body", payload.get("snippet", "")),
            "reasoning": "OpenAI library not available, using default behavior"
        }
    
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning(
            f"Classification skipped - Subject: '{subject}' | "
            f"Reason: No OpenAI API key configured, using default behavior"
        )
        return {
            "should_create": True,
            "confidence": 0.5,
            "title": payload.get("subject", "Email Task"),
            "notes": payload.get("body", payload.get("snippet", "")),
            "reasoning": "No OpenAI API key configured, using default behavior"
        }
    
    email_content = prepare_email_content(payload)
    sender = payload.get("sender", "Unknown")
    subject = email_content.get("subject", "(No subject)")
    
    # Format categories as blocks for prompt
    if task_categories:
        task_categories_block = "Available Task Categories:\n" + "\n".join(
            f"  - {cat}" for cat in task_categories if cat and isinstance(cat, str)
        )
    else:
        task_categories_block = "Available Task Categories: None"
    
    if calendar_categories:
        calendar_categories_block = "Available Calendar Categories:\n" + "\n".join(
            f"  - {cat}" for cat in calendar_categories if cat and isinstance(cat, str)
        )
    else:
        calendar_categories_block = "Available Calendar Categories: None"
    
    logger.info(f"Processing email for classification - Subject: '{subject}', Sender: '{sender}'")
    prompt = f"""
You are an intelligent email assistant that helps users manage their tasks and meetings by analyzing emails.

{task_categories_block}

{calendar_categories_block}

Instructions:

1. Determine if the email represents:
   a) a task to be created
   b) a meeting invitation

2. If it's a task:
    - Generate a concise task title (3-8 words)
    - Generate detailed task notes (2-4 sentences)
    - Provide a confidence score (0.0-1.0)
    - For the "category" field in your response: You MUST select one of the category names from the Available Task Categories list above, or null if none fit.
      IMPORTANT: Use the exact category name as shown (the text after the "- " and before the colon, if present).
      Do not include descriptions or any additional text - only the category name itself.
    - Explain your reasoning


3. If it's a meeting:
   - Detect if it is indeed a meeting (is_meeting: true/false)
   - Extract meeting details:
       * summary: meeting title
       * location: physical or virtual link (leave empty if unknown)
        * start_datetime: RFC3339 UTC start time (leave empty if unknown)
        * end_datetime: RFC3339 UTC end time (leave empty if unknown)
        * participants: list of email addresses (leave empty list if unknown)
        * category: For the meeting["category"] field in your response: You MUST select one of the category names from the Available Calendar Categories list above, or null if none fit.
          IMPORTANT: Use the exact category name as shown (the text after the "- " and before the colon, if present).
          Do not include descriptions or any additional text - only the category name itself.
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
  "category": "Exact category name from Available Task Categories list, or null",
  "reasoning": "Brief explanation of decision",
  "meeting": {{
      "is_meeting": true/false,
      "summary": "",
      "location": "",
      "start_datetime": "",
      "end_datetime": "",
      "start_datetime": "",
      "end_datetime": "",
      "participants": [],
      "category": "Exact category name from Available Calendar Categories list, or null"
  }}
}}

CRITICAL: For both "category" fields:
- Use the EXACT category name as listed in the Available Categories sections above
- Do NOT include descriptions, colons, or any additional text
- Use null if no category fits

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
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        should_create = bool(result.get("should_create", True))
        confidence = float(result.get("confidence", 0.5))
        reasoning = str(result.get("reasoning", ""))[:500]
        title = str(result.get("title", email_content["subject"]))[:200]
        meeting_info = result.get("meeting")
        
        classification_status = "SUCCESS" if should_create else "SKIPPED"
        logger.info(
            f"Email classification completed - Subject: '{subject}' | "
            f"Decision: {classification_status} | "
            f"Confidence: {confidence:.2f} | "
            f"Reasoning: {reasoning[:100]}{'...' if len(reasoning) > 100 else ''}"
        )
        
        if meeting_info and meeting_info.get("is_meeting"):
            logger.info(
                f"Meeting detected in email - Subject: '{subject}' | "
                f"Summary: '{meeting_info.get('summary', 'N/A')}' | "
                f"Start: {meeting_info.get('start_datetime', 'N/A')}"
            )
        
        return {
            "should_create": should_create,
            "confidence": confidence,
            "title": title,
            "notes": str(result.get("notes", email_content["body"] or email_content["snippet"]))[:2000],
            "category": result.get("category"),
            "reasoning": reasoning,
            "meeting": meeting_info,
        }
        
    except json.JSONDecodeError as e:
        logger.error(
            f"Classification FAILED (JSON parsing error) - Subject: '{subject}' | "
            f"Error: {str(e)} | Using fallback behavior"
        )
        return {
            "should_create": True,
            "confidence": 0.5,
            "title": email_content["subject"],
            "notes": email_content["body"] or email_content["snippet"],
            "reasoning": "JSON parsing failed, using fallback"
        }
    except Exception as e:
        logger.error(
            f"Classification FAILED (API error) - Subject: '{subject}' | "
            f"Error: {str(e)} | Using fallback behavior"
        )
        return {
            "should_create": True,
            "confidence": 0.5,
            "title": email_content["subject"],
            "notes": email_content["body"] or email_content["snippet"],
            "reasoning": f"API error: {str(e)}",
            "meeting": result.get("meeting") if isinstance(result, dict) else None,
        }


def ml_decide(
    payload: Dict[str, Any],
    task_categories: list[str] | None = None,
    calendar_categories: list[str] | None = None,
) -> Dict[str, Any]:
    """
    Main entry point for email classification.
    Uses environment variables for configuration.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    result = classify_and_generate_task(
        payload, 
        api_key=api_key, 
        model=model,
        task_categories=task_categories,
        calendar_categories=calendar_categories
    )
    
    meeting_info = result.get("meeting")
    if meeting_info:
        required_keys = ["is_meeting", "summary", "start_datetime", "end_datetime"]
        if not all(k in meeting_info for k in required_keys):
            result["meeting"] = None
    return result
