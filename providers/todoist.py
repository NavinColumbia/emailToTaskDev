"""Todoist task creation helper."""

import os
from typing import Any, Dict

import requests

API_BASE = "https://api.todoist.com/rest/v2"


class TodoistError(RuntimeError):
    """Raised when the Todoist API returns an error."""


def _auth_headers() -> Dict[str, str]:
    token = os.getenv("TODOIST_API_TOKEN")
    if not token:
        raise TodoistError("TODOIST_API_TOKEN is not set")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def create_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    headers = _auth_headers()

    subject = (payload.get("subject") or "Email task").strip()
    body = (payload.get("body") or payload.get("snippet") or "").strip()
    sender = (payload.get("sender") or "").strip()

    description_parts = []
    if sender:
        description_parts.append(f"Forwarded from: {sender}")
    if body:
        description_parts.append(body)

    data: Dict[str, Any] = {"content": subject}
    if description_parts:
        data["description"] = "\n\n".join(description_parts)

    response = requests.post(
        f"{API_BASE}/tasks",
        headers=headers,
        json=data,
        timeout=10,
    )

    if response.status_code >= 400:
        raise TodoistError(
            f"Todoist API error {response.status_code}: {response.text.strip()}"
        )

    try:
        return response.json()
    except ValueError:
        return {"status": "created", "content": subject}
