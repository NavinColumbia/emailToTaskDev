from flask import Blueprint, session, request, jsonify
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateutil_parser
import logging
from server.utils import get_gmail_service, get_current_user, message_to_payload
from server.config import DEFAULT_PROVIDER, TASKS_LIST_TITLE
from server.db import db_session, Email, Task, CalendarEvent
from server.ml import ml_decide
from server.providers.google_tasks import create_task as create_google_task, GoogleTasksError

emails_bp = Blueprint('emails', __name__)
logger = logging.getLogger(__name__)

def get_optional_int_param(name: str, minimum: int | None = None, maximum: int | None = None) -> int | None:
    raw = request.values.get(name, None)
    if raw in (None, "", "null", "undefined"):
        return None
    try:
        val = int(raw)
    except (TypeError, ValueError):
        return None
    if minimum is not None and val < minimum:
        val = minimum
    if maximum is not None and val > maximum:
        val = maximum
    return val

def parse_since_to_utc(since_hours: str | None, since_iso: str | None):
    """
    Return a UTC-aware datetime cutoff or None.
    Accepts:
      - since_hours: "24", "24h", "1.5h", "90m" (minutes), ""
      - since_iso: ISO 8601 like "2025-10-28T12:30:00Z" or "2025-10-28 12:30:00-04:00"
    If both provided, since_hours takes precedence.
    """
    # Handle hours/minutes first
    if since_hours:
        s = since_hours.strip().lower()
        if s:
            try:
                # support "xh" or plain number
                if s.endswith("h"):
                    hours = float(s[:-1])
                    return datetime.now(timezone.utc) - timedelta(hours=hours)
                if s.endswith("m"):
                    minutes = float(s[:-1])
                    return datetime.now(timezone.utc) - timedelta(minutes=minutes)
                # plain number => hours
                hours = float(s)
                return datetime.now(timezone.utc) - timedelta(hours=hours)
            except ValueError:
                pass  # fall through to since_iso

    # Handle explicit ISO datetime
    if since_iso:
        s = since_iso.strip()
        if s:
            try:
                dt = dateutil_parser.isoparse(s)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                pass

    return None

def gmail_list_ids(service, q: str, max_list: int | None = 50, min_internal_ms: int | None = None) -> list[str]:
    """
    List message IDs matching query.
    - max_list=None => fetch all pages (no cap; beware quota/time).
    - min_internal_ms => precise filter on internalDate (UTC ms).
    """
    ids: list[str] = []
    page_token = None
    page_num = 0

    # Page size is capped by Gmail at 100 anyway
    page_size = 100 if max_list is None else min(100, max_list if max_list > 0 else 100)

    while True:
        page_num += 1
        try:
            resp = (
                service.users()
                .messages()
                .list(userId="me", q=q, maxResults=page_size, pageToken=page_token)
                .execute()
            )
            messages = resp.get("messages", [])
        except Exception as e:
            raise

        if min_internal_ms is None:
            ids.extend(m["id"] for m in messages)
        else:
            # metadata call to read internalDate for precise cutoff
            for m in messages:
                meta = (
                    service.users()
                    .messages()
                    .get(userId="me", id=m["id"], format="metadata", metadataHeaders=[])
                    .execute()
                )
                internal_ms = int(meta.get("internalDate", 0))
                if internal_ms >= min_internal_ms:
                    ids.append(m["id"])

        # Stop if we reached requested max
        if max_list is not None and len(ids) >= max_list:
            return ids[:max_list]

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return ids

def get_or_create_email(session, user_id: int, message_id: str, meta: dict | None = None) -> Email:
    e = session.query(Email).filter_by(user_id=user_id, gmail_message_id=message_id).one_or_none()
    if e:
        return e
    e = Email(
        user_id=user_id,
        gmail_message_id=message_id,
        gmail_thread_id=(meta or {}).get("thread_id"),
        subject=(meta or {}).get("subject"),
        sender=(meta or {}).get("sender"),
        received_at=(dateutil_parser.isoparse(meta["received_at"]) if meta and meta.get("received_at") else None),
        snippet=(meta or {}).get("snippet"),
        body=(meta or {}).get("body"),
        processed=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(e)
    session.flush()
    return e

def task_exists(session, user_id: int, email_id: int, provider: str) -> bool:
    return session.query(Task.id).filter_by(user_id=user_id, email_id=email_id, provider=provider).first() is not None

def dispatch_task(provider: str, payload: dict) -> dict:
    from server.utils import get_tasks_service
    if provider == "google_tasks":
        tasks_service = get_tasks_service()
        if not tasks_service:
            raise GoogleTasksError("Not authenticated for Google Tasks")
        return create_google_task(tasks_service, TASKS_LIST_TITLE, payload)

    raise ValueError(f"Unsupported provider '{provider}'")

def create_google_calendar_event(meeting: dict):
    """
    Create a Google Calendar event for a meeting.
    Automatically uses start/end times from the meeting dict, or
    attempts to infer them from the email body or summary.
    """
    from server.utils import get_calendar_service
    service = get_calendar_service()
    if not service:
        return None

    raw_start = meeting.get("start_datetime")
    raw_end = meeting.get("end_datetime")
    now_utc = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    # Parse supplied start time or fall back to now
    if raw_start:
        try:
            start_obj = dateutil_parser.isoparse(raw_start)
        except Exception:
            start_obj = now_utc
    else:
        start_obj = now_utc

    # Never schedule meetings in the past
    if start_obj < now_utc:
        start_obj = now_utc

    start_dt = start_obj.isoformat()

    # Parse end time or default to one hour after start
    if raw_end:
        try:
            end_obj = dateutil_parser.isoparse(raw_end)
        except Exception:
            end_obj = start_obj + timedelta(hours=1)
    else:
        end_obj = start_obj + timedelta(hours=1)

    if end_obj <= start_obj:
        end_obj = start_obj + timedelta(hours=1)

    end_dt = end_obj.isoformat()

    event = {
        "summary": meeting.get("summary") or "Meeting",
        "location": meeting.get("location"),
        "description": meeting.get("summary"),
        "start": {"dateTime": start_dt, "timeZone": "UTC"},
        "end": {"dateTime": end_dt, "timeZone": "UTC"},
        "attendees": [{"email": p} for p in meeting.get("participants", []) if p],
    }

    try:
        created_event = service.events().insert(calendarId="primary", body=event).execute()
        return created_event
    except Exception as e:
        logger.error(
            f"Calendar event creation FAILED - Summary: '{event.get('summary', 'N/A')}' | "
            f"Error: {str(e)}"
        )
        return None

@emails_bp.route("/fetch-emails", methods=["POST", "GET"])
def fetch_emails():
    logger.info("Fetch emails request received")
    service = get_gmail_service()
    if not service:
        logger.warning("Fetch emails failed: Not authenticated")
        return jsonify({"error": "Not authenticated. Please log in first."}), 401

    user = get_current_user()
    if not user:
        logger.warning("Fetch emails failed: Could not determine user")
        return jsonify({"error": "Could not determine user"}), 401

    provider = request.values.get("provider", DEFAULT_PROVIDER)
    window = request.values.get("window")  # e.g., 7d
    custom_query = request.values.get("q")
    max_msgs = get_optional_int_param("max", minimum=1)

    since_hours = request.values.get("since_hours")
    since_iso = request.values.get("since")
    dry_run = (request.values.get("dry_run", "false").lower() == "true")
    
    logger.info(
        f"Fetch emails params: provider={provider}, window={window}, max={max_msgs}, "
        f"since_hours={since_hours}, since={since_iso}, q={custom_query}, dry_run={dry_run}"
    )

    # Build Gmail query
    query_parts = []
    if custom_query:
        query_parts.append(custom_query)

    # Coarse time narrowing
    since_dt = parse_since_to_utc(since_hours, since_iso)
    min_internal_ms = None
    if since_dt:
        y, m, d = since_dt.date().year, since_dt.date().month, since_dt.date().day
        query_parts.append(f"after:{y}/{m:02d}/{d:02d}")
        min_internal_ms = int(since_dt.timestamp() * 1000)
    elif window:
        query_parts.append(f"newer_than:{window}")

    query = " ".join(query_parts) or "in:inbox"
    logger.info(f"Gmail query: {query}")
    logger.info(f"Fetching email IDs from Gmail (max={max_msgs})...")
    ids = gmail_list_ids(service, q=query, max_list=max_msgs, min_internal_ms=min_internal_ms)
    logger.info(f"Found {len(ids)} email(s) matching query")

    created_tasks = []
    created_calendar_events = []
    already_processed_count = 0
    considered = 0

    with db_session() as s:
        for message_id in ids:
            considered += 1
            full_msg = (
                service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            # precise guard if since_dt provided
            if since_dt:
                internal_ms = int(full_msg.get("internalDate", 0))
                if internal_ms < int(since_dt.timestamp() * 1000):
                    continue

            payload = message_to_payload(full_msg)
            subject = payload.get("subject", "(No subject)")
            sender = payload.get("sender", "Unknown")
            message_id_short = message_id[:20] + "..." if len(message_id) > 20 else message_id

            # Log email being processed
            logger.info(
                f"Processing email - ID: {message_id_short} | "
                f"Subject: '{subject}' | "
                f"Sender: '{sender}' | "
                f"Received: {payload.get('received_at', 'N/A')}"
            )

            # ML Classification and Task Generation
            ml_result = ml_decide(payload)
            should_create = ml_result.get("should_create", True)
            confidence = ml_result.get("confidence", 0.5)
            reasoning = ml_result.get("reasoning", "")
            
            # Log classification decision
            logger.info(
                f"Email classification result - ID: {message_id_short} | "
                f"Subject: '{subject}' | "
                f"Should create task: {should_create} | "
                f"Confidence: {confidence:.2f}"
            )

            # Store email with ML metadata
            email_row = get_or_create_email(s, user.id, message_id, payload)
            
            #create meeting if necessary
            meeting_info = ml_result.get("meeting")
            calendar_event = None
            if meeting_info and meeting_info.get("is_meeting"):
                logger.info(
                    f"Creating calendar event - Email ID: {message_id_short} | "
                    f"Subject: '{subject}' | "
                    f"Meeting Summary: '{meeting_info.get('summary', 'N/A')}'"
                )
                calendar_event = create_google_calendar_event(meeting_info)
                if calendar_event:
                    logger.info(
                        f"Calendar event created successfully - Email ID: {message_id_short} | "
                        f"Event ID: {calendar_event.get('id')} | "
                        f"Summary: '{calendar_event.get('summary', 'N/A')}'"
                    )
                    # Save calendar event to database
                    start_dt = None
                    end_dt = None
                    if calendar_event.get("start", {}).get("dateTime"):
                        try:
                            start_dt = dateutil_parser.isoparse(calendar_event["start"]["dateTime"])
                        except Exception:
                            pass
                    if calendar_event.get("end", {}).get("dateTime"):
                        try:
                            end_dt = dateutil_parser.isoparse(calendar_event["end"]["dateTime"])
                        except Exception:
                            pass
                    
                    cal_event = CalendarEvent(
                        user_id=user.id,
                        email_id=email_row.id,
                        google_event_id=calendar_event.get("id"),
                        summary=calendar_event.get("summary", "Meeting"),
                        location=calendar_event.get("location"),
                        start_datetime=start_dt,
                        end_datetime=end_dt,
                        html_link=calendar_event.get("htmlLink"),
                        provider_metadata=calendar_event,
                    )
                    s.add(cal_event)
                    
                    created_calendar_events.append({
                        "summary": calendar_event.get("summary", "Meeting"),
                        "htmlLink": calendar_event.get("htmlLink"),
                        "start": calendar_event.get("start", {}).get("dateTime"),
                        "location": calendar_event.get("location"),
                    })
                else:
                    logger.warning(
                        f"Calendar event creation failed - Email ID: {message_id_short} | "
                        f"Subject: '{subject}' | "
                        f"Meeting Summary: '{meeting_info.get('summary', 'N/A')}'"
                    )
            
            # Skip if ML decides not to create task
            if not should_create:
                logger.info(
                    f"Email skipped (ML decision) - ID: {message_id_short} | "
                    f"Subject: '{subject}' | "
                    f"Reasoning: {reasoning[:100]}{'...' if len(reasoning) > 100 else ''}"
                )
                # Mark as processed but don't create task
                if not email_row.first_processed_at:
                    email_row.first_processed_at = datetime.now(timezone.utc)
                email_row.last_processed_at = datetime.now(timezone.utc)
                email_row.processed = True
                continue

            # Use ML-generated title and notes
            subject = (ml_result.get("title") or payload.get("subject") or "Email task").strip()
            notes = (ml_result.get("notes") or payload.get("body") or payload.get("snippet") or "").strip()
            due = ml_result.get("due")  # RFC3339 string or None (can be extended in ml.py)

            # Update payload with ML-enhanced content
            payload["subject"] = subject
            payload["body"] = notes
            if due:
                payload["due"] = due

            # Dedupe per provider
            if task_exists(s, user.id, email_row.id, provider):
                logger.info(
                    f"Email already processed - ID: {message_id_short} | "
                    f"Subject: '{subject}' | "
                    f"Provider: {provider}"
                )
                already_processed_count += 1
                continue

            if dry_run:
                created_tasks.append({
                    "message_id": message_id,
                    "provider": provider,
                    "task": {"status": "dry_run", "title": payload.get("subject", "")},
                })
                continue

            try:
                task = dispatch_task(provider, payload)
                task_id = task.get("id") if isinstance(task, dict) else None
                task_title = task.get("title") if isinstance(task, dict) else subject
                
                logger.info(
                    f"Task created successfully - Email ID: {message_id_short} | "
                    f"Subject: '{subject}' | "
                    f"Task ID: {task_id} | "
                    f"Task Title: '{task_title}' | "
                    f"Provider: {provider} | "
                    f"Confidence: {confidence:.2f}"
                )
            except Exception as err:
                logger.error(
                    f"Task creation FAILED - Email ID: {message_id_short} | "
                    f"Subject: '{subject}' | "
                    f"Provider: {provider} | "
                    f"Error: {str(err)}"
                )
                return jsonify({"error": f"Error creating task: {str(err)}"}), 400

            # Record task in DB
            t = Task(
                user_id=user.id,
                email_id=email_row.id,
                provider=provider,
                provider_task_id=(task.get("id") if isinstance(task, dict) else None),
                provider_metadata=task if isinstance(task, dict) else None,
            )
            s.add(t)

            # Mark email processed
            now = datetime.now(timezone.utc)
            if not email_row.first_processed_at:
                email_row.first_processed_at = now
            email_row.last_processed_at = now
            email_row.processed = True

            created_tasks.append({
                "message_id": message_id,
                "provider": provider,
                "task": task,
            })

    result = {
        "processed": len(created_tasks),
        "query": query,
        "created": created_tasks,
        "total_found": len(ids),
        "already_processed": already_processed_count,
        "considered": considered,
        "calendar_events": created_calendar_events
    }

    logger.info(
        f"Email processing complete: {len(created_tasks)} tasks created, "
        f"{already_processed_count} already processed, {len(ids)} total found, {considered} considered"
    )

    return jsonify(result)

