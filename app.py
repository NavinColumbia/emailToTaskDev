from __future__ import annotations
import os
import base64
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Tuple

from flask import Flask, request, redirect, session, url_for, jsonify, render_template, flash
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

from dateutil import parser as dateutil_parser


from providers.google_tasks import create_task as create_google_task, GoogleTasksError

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).with_name('.env'), override=False)

from db import db_session, init_db, Email, Task
from ml import ml_decide 






app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-change-me")

CLIENT_SECRETS_FILE = os.getenv("GOOGLE_CLIENT_SECRETS", "client_secret.json")

# SCOPES: Gmail read-only + Google Tasks write
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/calendar.events",
]

REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/oauth2callback")




DEFAULT_PROVIDER = os.getenv("DEFAULT_TASK_PROVIDER", "google_tasks")
DEFAULT_FETCH_LIMIT = int(os.getenv("FETCH_LIMIT", "10"))
TASKS_LIST_TITLE = os.getenv("TASKS_LIST_TITLE", "Email Tasks")

# Ensure DB tables exist at startup
init_db()




def _get_credentials():
    creds_info = session.get("credentials")
    if not creds_info:
        return None
    return Credentials.from_authorized_user_info(info=creds_info, scopes=SCOPES)

def get_gmail_service():
    creds = _get_credentials()
    if not creds:
        return None
    return build("gmail", "v1", credentials=creds)

def get_tasks_service():
    creds = _get_credentials()
    if not creds:
        return None
    return build("tasks", "v1", credentials=creds)

def get_calendar_service():
    creds = _get_credentials()
    if not creds:
        return None
    return build("calendar", "v3", credentials=creds)



def get_header(payload: dict, name: str) -> str | None:
    for header in payload.get("headers", []):
        if header.get("name", "").lower() == name.lower():
            return header.get("value")
    return None

def decode_part_text(part: dict) -> str:
    body = part.get("body", {})
    data = body.get("data")
    if not data:
        return ""
    raw = base64.urlsafe_b64decode(data.encode("utf-8"))
    charset = "utf-8"
    for header in part.get("headers", []):
        if header.get("name", "").lower() == "content-type":
            value = header.get("value", "")
            lower = value.lower()
            if "charset=" in lower:
                charset = lower.split("charset=", 1)[1]
                if ";" in charset:
                    charset = charset.split(";", 1)[0]
                charset = charset.strip().strip('"').strip("'")
                break
    try:
        return raw.decode(charset, errors="replace")
    except Exception:
        return raw.decode("utf-8", errors="replace")

def gather_bodies(payload: dict) -> Tuple[str, str]:
    texts: list[str] = []
    htmls: list[str] = []

    def walk(part: dict):
        mime = (part.get("mimeType") or "").lower()
        if part.get("parts"):
            for child in part["parts"]:
                walk(child)
            return
        if mime.startswith("text/plain"):
            texts.append(decode_part_text(part))
        elif mime.startswith("text/html"):
            htmls.append(decode_part_text(part))

    if payload:
        walk(payload)

    text = next((t for t in texts if t.strip()), "")
    html = next((h for h in htmls if h.strip()), "")
    return text, html

def html_to_text(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    return soup.get_text("\n").strip()

def message_to_payload(message: dict) -> dict:
    payload = message.get("payload", {})
    text_body, html_body = gather_bodies(payload)
    body = text_body or html_to_text(html_body)

    internal = message.get("internalDate")
    received_at = None
    if internal:
        try:
            received_at = datetime.fromtimestamp(int(internal) / 1000, tz=timezone.utc).isoformat()
        except Exception:
            received_at = None

    return {
        "subject": get_header(payload, "Subject") or "(No subject)",
        "sender": get_header(payload, "From") or "",
        "received_at": received_at,
        "body": body.strip(),
        "html": html_body, 
        "snippet": message.get("snippet", ""),
        "thread_id": message.get("threadId", ""),
    }


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
                # support “xh” or plain number
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

    # Page size is capped by Gmail at 100 anyway
    page_size = 100 if max_list is None else min(100, max_list if max_list > 0 else 100)

    while True:
        resp = (
            service.users()
            .messages()
            .list(userId="me", q=q, maxResults=page_size, pageToken=page_token)
            .execute()
        )
        messages = resp.get("messages", [])

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


def get_or_create_email(session, message_id: str, meta: dict | None = None) -> Email:
    e = session.query(Email).filter_by(gmail_message_id=message_id).one_or_none()
    if e:
        return e
    e = Email(
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

def task_exists(session, email_id: int, provider: str) -> bool:
    return session.query(Task.id).filter_by(email_id=email_id, provider=provider).first() is not None




def dispatch_task(provider: str, payload: dict) -> dict:
    if provider == "google_tasks":
        tasks_service = get_tasks_service()
        if not tasks_service:
            raise GoogleTasksError("Not authenticated for Google Tasks")
        return create_google_task(tasks_service, TASKS_LIST_TITLE, payload)

    raise ValueError(f"Unsupported provider '{provider}'")

def create_google_calendar_event(meeting: dict):
    service = get_calendar_service()
    if not service:
        print("Not authenticated for Google Calendar")
        return None

    event = {
        "summary": meeting.get("summary") or "Meeting",
        "location": meeting.get("location"),
        "description": meeting.get("summary"),
        "start": {"dateTime": meeting.get("start_datetime"), "timeZone": "UTC"},
        "end": {"dateTime": meeting.get("end_datetime"), "timeZone": "UTC"},
        "attendees": [{"email": p} for p in meeting.get("participants", [])],
    }

    try:
        created_event = service.events().insert(calendarId="primary", body=event).execute()
        print(f"Created Google Calendar event: {created_event.get('htmlLink')}")
        return created_event
    except Exception as e:
        print(f"Error creating Google Calendar event: {e}")
        return None


@app.route("/")
def index():
    authed = "credentials" in session
    return render_template("home.html", authed=authed)

@app.route("/authorize")
def authorize():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    session["state"] = state
    return redirect(authorization_url)

@app.route("/oauth2callback")
def oauth2callback():
    state = session.get("state")
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI,
    )
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session["credentials"] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }
    flash("Successfully connected to Google (Gmail + Tasks)!", "success")
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.pop("credentials", None)
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("index"))

@app.route("/fetch-emails")
def fetch_emails_page():
    if "credentials" not in session:
        flash("Please log in with Google first.", "warning")
        return redirect(url_for("authorize"))
    return render_template("fetch_emails.html")

@app.route("/no-emails-found")
def no_emails_found():
    if "credentials" not in session:
        return redirect(url_for("authorize"))
    # Optional flash messages via ?message=no_results|error
    if request.args.get("message") == "no_results":
        flash("Still no emails found. Try a different search.", "warning")
    elif request.args.get("message") == "error":
        error_msg = request.args.get("error", "An unknown error occurred")
        flash(f"Error: {error_msg}", "error")
    return render_template("no_emails_found.html")

@app.route("/email-results")
def email_results():
    if "credentials" not in session:
        return redirect(url_for("authorize"))
    results_data = session.get("email_results")
    if not results_data:
        flash("No results found. Please process emails first.", "warning")
        return redirect(url_for("fetch_emails_page"))
    session.pop("email_results", None)
    return render_template(
        "email_results.html",
        processed_count=results_data["processed_count"],
        query=results_data["query"],
        created_tasks=results_data["created_tasks"]
    )

@app.route("/view-all-results")
def view_all_results():
    if "credentials" not in session:
        return redirect(url_for("authorize"))

    with db_session() as s:
        rows = (
            s.query(Task, Email)
            .join(Email, Email.id == Task.email_id)
            .order_by(Task.created_at.desc())
            .limit(200)
            .all()
        )
        items = []
        for t, e in rows:
            md = t.provider_metadata or {}
            items.append({
                "provider": t.provider,
                "provider_task_id": t.provider_task_id,
                "created_at": t.created_at.isoformat() if t.created_at else "",
                "email_subject": e.subject,
                "email_sender": e.sender,
                "email_received_at": e.received_at.isoformat() if e.received_at else "",
                "task_title": md.get("title"),
                "task_link": md.get("selfLink"),
                "task_due": md.get("due"),
            })
    return render_template("all_results.html", tasks_history=items, total_tasks=len(items))

@app.route("/api/fetch-emails", methods=["POST", "GET"])
def fetch_emails():
    service = get_gmail_service()
    if not service:
        return jsonify({"error": "Not authenticated. Please log in first."}), 401

    provider = request.values.get("provider", DEFAULT_PROVIDER)
    window = request.values.get("window")  # e.g., 7d
    custom_query = request.values.get("q")
    max_msgs = get_optional_int_param("max", minimum=1)

    since_hours = request.values.get("since_hours")
    since_iso = request.values.get("since")
    dry_run = (request.values.get("dry_run", "false").lower() == "true")

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

    ids = gmail_list_ids(service, q=query, max_list=max_msgs, min_internal_ms=min_internal_ms)

    created_tasks = []
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

            # ML Classification and Task Generation
            ml_result = ml_decide(payload)
            should_create = ml_result.get("should_create", True)
            confidence = ml_result.get("confidence", 0.5)
            reasoning = ml_result.get("reasoning", "")

            #create meeting if necessary
            meeting_info = ml_result.get("meeting")
            if meeting_info and meeting_info.get("is_meeting"):
                create_google_calendar_event(meeting_info)
            
            # Store email with ML metadata
            email_row = get_or_create_email(s, message_id, payload)
            
            # Skip if ML decides not to create task
            if not should_create:
                # Mark as processed but don't create task
                if not email_row.first_processed_at:
                    email_row.first_processed_at = datetime.now(timezone.utc)
                email_row.last_processed_at = datetime.now(timezone.utc)
                email_row.processed = True
                # Log the skip decision
                print(f"Skipping email '{payload.get('subject')}' - Confidence: {confidence:.2f}, Reason: {reasoning}")
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
            if task_exists(s, email_row.id, provider):
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
            except GoogleTasksError as err:
                if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                    return jsonify({"error": str(err)}), 400
                else:
                    flash(f"Task provider error: {str(err)}", "error")
                    return redirect(url_for("fetch_emails_page"))
            except ValueError as err:
                if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                    return jsonify({"error": str(err)}), 400
                else:
                    flash(f"Error: {str(err)}", "error")
                    return redirect(url_for("fetch_emails_page"))

            # Record task in DB
            t = Task(
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
        "considered": considered
    }

    # HTML redirect to results page with flash
    if request.accept_mimetypes.accept_html:
        if len(created_tasks) == 0 and already_processed_count == 0:
            flash("No emails found with the current search criteria.", "warning")
            return redirect(url_for("no_emails_found"))
        elif len(created_tasks) == 0 and already_processed_count > 0:
            flash(f"Found {already_processed_count} emails, but they were already processed. No new tasks created.", "info")
            return redirect(url_for("fetch_emails_page"))
        else:
            flash(f"Successfully processed {len(created_tasks)} emails!", "success")
            session["email_results"] = {
                "processed_count": len(created_tasks),
                "query": query,
                "created_tasks": created_tasks
            }
            return redirect(url_for("email_results"))

    return jsonify(result)


if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    port = int(os.getenv("PORT", 5000))
    app.run("127.0.0.1", port, debug=True)
