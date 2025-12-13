#!/usr/bin/env python3
"""
Test script for ML classification and task generation.
Usage: python3 test_ml.py
"""

from server.ml import ml_decide, clean_html_to_text
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (in project root)
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

# Test email samples
test_emails = [
    {
        "name": "Action Item Email",
        "payload": {
            "subject": "RE: Review the Q4 budget report by Friday",
            "sender": "manager@company.com",
            "body": "Hi team,\n\nCan you please review the attached Q4 budget report and send me your feedback by end of day Friday? We need to finalize the numbers before the board meeting next week.\n\nThanks,\nManager",
            "snippet": "Hi team, Can you please review the attached Q4 budget...",
        }
    },
    {
        "name": "Newsletter Email",
        "payload": {
            "subject": "Weekly Tech Newsletter - Latest Updates",
            "sender": "newsletter@techblog.com",
            "body": "Check out this week's top stories in tech:\n\n1. New JavaScript framework released\n2. AI trends in 2025\n3. Best practices for cloud deployment\n\nRead more at our website.",
            "snippet": "Check out this week's top stories in tech...",
        }
    },
    {
        "name": "Meeting Invitation",
        "payload": {
            "subject": "Meeting: Project Kickoff - Thursday 2pm",
            "sender": "calendar@company.com",
            "body": "You've been invited to attend the Project Kickoff meeting.\n\nWhen: Thursday, Nov 7, 2025 at 2:00 PM\nWhere: Conference Room B\n\nPlease review the project brief before attending.",
            "snippet": "You've been invited to attend the Project Kickoff meeting...",
        }
    },
    {
        "name": "HTML Email",
        "payload": {
            "subject": "Payment Due: Invoice #12345",
            "sender": "billing@service.com",
            "body": "",
            "html": """
            <html>
                <body>
                    <h1>Invoice Due</h1>
                    <p>Your invoice #12345 is due on <strong>November 15, 2025</strong>.</p>
                    <p>Amount: <strong>$150.00</strong></p>
                    <p>Please make payment by the due date to avoid late fees.</p>
                    <br/>
                    <p>Thank you for your business!</p>
                </body>
            </html>
            """,
            "snippet": "Your invoice #12345 is due on November 15, 2025...",
        }
    },
    {
        "name": "Spam/Marketing",
        "payload": {
            "subject": "🎉 SPECIAL OFFER: 50% OFF Everything!",
            "sender": "deals@shopping.com",
            "body": "Limited time only! Get 50% off on all products. Shop now and save big! Click here to redeem your exclusive offer.",
            "snippet": "Limited time only! Get 50% off on all products...",
        }
    },
]


def test_classification():
    """Test the ML classification on sample emails."""
    
    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  WARNING: OPENAI_API_KEY not set in environment variables.")
        print("The classifier will use fallback behavior (create all tasks).\n")
    else:
        print(f"✓ OpenAI API key found (starts with: {api_key[:10]}...)\n")
    
    print("=" * 80)
    print("Testing ML Email Classification")
    print("=" * 80)
    print()
    
    for i, test_case in enumerate(test_emails, 1):
        name = test_case["name"]
        payload = test_case["payload"]
        
        print(f"\n📧 Test {i}: {name}")
        print("-" * 80)
        print(f"From: {payload['sender']}")
        print(f"Subject: {payload['subject']}")
        
        # Show body or HTML preview
        if payload.get('body'):
            body_preview = payload['body'][:100] + "..." if len(payload['body']) > 100 else payload['body']
            print(f"Body: {body_preview}")
        elif payload.get('html'):
            clean_text = clean_html_to_text(payload['html'])
            text_preview = clean_text[:100] + "..." if len(clean_text) > 100 else clean_text
            print(f"Body (from HTML): {text_preview}")
        
        print()
        
        # Classify
        result = ml_decide(payload)
        
        # Display results
        should_create = result.get("should_create", True)
        confidence = result.get("confidence", 0.5)
        
        if should_create:
            print(f"✅ DECISION: CREATE TASK (Confidence: {confidence:.0%})")
            print(f"   Title: {result.get('title', 'N/A')}")
            notes = result.get('notes', 'N/A')
            notes_preview = notes[:150] + "..." if len(notes) > 150 else notes
            print(f"   Notes: {notes_preview}")
        else:
            print(f"❌ DECISION: SKIP (Confidence: {confidence:.0%})")
        
        reasoning = result.get('reasoning', '')
        if reasoning:
            print(f"   Reasoning: {reasoning}")

        meeting_info = result.get("meeting")
        if meeting_info:
            print(f"   Meeting block: {meeting_info}")

        print()
    
    print("=" * 80)
    print("Testing Complete!")
    print("=" * 80)


if __name__ == "__main__":
    test_classification()
