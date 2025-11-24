"""Google Tasks provider."""

from __future__ import annotations
import logging
from typing import Any, Dict, Optional
from googleapiclient.discovery import Resource

logger = logging.getLogger(__name__)
MAX_NOTES_LEN = 8000


class GoogleTasksError(RuntimeError):
    """Raised when Google Tasks API is unavailable or errors occur."""


def _truncate(s: str, limit: int = MAX_NOTES_LEN) -> str:
    if not s:
        return ""
    if len(s) <= limit:
        return s
    head = s[: int(limit * 0.7)]
    tail = s[-int(limit * 0.2) :]
    return f"{head}\n...\n{tail}"


def _get_or_create_tasklist(service: Resource, title: str) -> str:
    """Return tasklist id with given title. create it if missing."""
    logger.debug(f"Getting or creating tasklist: '{title}'")
    try:
        req = service.tasklists().list(maxResults=100)
        while req is not None:
            resp = req.execute()
            tasklists = resp.get("items", [])
            logger.debug(f"Found {len(tasklists)} tasklist(s)")
            for tl in tasklists:
                if tl.get("title") == title:
                    logger.debug(f"Found existing tasklist '{title}' with id: {tl['id']}")
                    return tl["id"]
            req = service.tasklists().list_next(req, resp)
        logger.info(f"Tasklist '{title}' not found, creating new one")
        created = service.tasklists().insert(body={"title": title}).execute()
        logger.info(f"Created new tasklist '{title}' with id: {created['id']}")
        return created["id"]
    except Exception as e:
        logger.error(f"Error accessing Google Tasks API: {e}", exc_info=True)
        raise GoogleTasksError(f"Error accessing Google Tasks: {str(e)}")


def create_task(
    tasks_service: Resource,
    tasklist_title: str,
    payload: Dict[str, Any],
    tasklist_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a Google Task in the chosen list (by title or explicit id).
    Payload fields consumed: subject, body/snippet, sender, due (RFC3339 date or datetime).
    Returns a dict with key fields from the created Task.
    """
    if tasks_service is None:
        logger.error("Google Tasks service is not initialized")
        raise GoogleTasksError("Google Tasks service is not initialized")

    subject = (payload.get("subject") or "Email task").strip()
    body = (payload.get("body") or payload.get("snippet") or "").strip()
    sender = (payload.get("sender") or "").strip()

    logger.debug(f"Creating Google Task: title='{subject}', sender='{sender}', has_due={bool(payload.get('due'))}")

    notes_parts = []
    if sender:
        notes_parts.append(f"From: {sender}")
    if body:
        notes_parts.append(body)
    notes = _truncate("\n\n".join(notes_parts))

    task_body: Dict[str, Any] = {"title": subject}
    if notes:
        task_body["notes"] = notes
    if payload.get("due"):
        task_body["due"] = payload["due"]  # e.g., "2025-10-28T18:00:00Z" or "2025-10-28"

    try:
        if not tasklist_id:
            list_id = _get_or_create_tasklist(tasks_service, tasklist_title or "Tasks")
        else:
            list_id = tasklist_id
            logger.debug(f"Using provided tasklist_id: {list_id}")

        logger.debug(f"Inserting task into tasklist {list_id}")
        created = tasks_service.tasks().insert(tasklist=list_id, body=task_body).execute()
        logger.info(f"Google Task created successfully: id={created.get('id')}, title='{created.get('title')}'")
    except Exception as e:
        logger.error(f"Error creating Google Task: {e}", exc_info=True)
        raise GoogleTasksError(f"Error creating task: {str(e)}")
    web_url = f"https://tasks.google.com/"
    return {
        "id": created.get("id"),
        "title": created.get("title"),
        "status": created.get("status"),
        "due": created.get("due"),
        "selfLink": created.get("selfLink"),
        "webLink": web_url,
        "_tasklist_id": list_id,
    }


def delete_task(
    tasks_service: Resource,
    tasklist_id: str,
    task_id: str,
) -> None:
    """
    Delete a Google Task from the specified tasklist.
    """

    try:
        logger.debug(f"Deleting task {task_id} from tasklist {tasklist_id}")
        tasks_service.tasks().delete(tasklist=tasklist_id, task=task_id).execute()
        logger.info(f"Google Task deleted successfully: id={task_id}")
    except Exception as e:
        logger.error(f"Error deleting Google Task: {e}", exc_info=True)
        raise GoogleTasksError(f"Error deleting task: {str(e)}")
