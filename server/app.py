from __future__ import annotations
import os
import sys
import base64
import logging
from datetime import datetime, timezone, timedelta
from typing import Tuple
from pathlib import Path

# Add project root to Python path to enable server.* imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from flask import Flask, request, redirect, session, url_for, jsonify, flash, send_from_directory
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

from dateutil import parser as dateutil_parser

from dotenv import load_dotenv

# Load .env from project root (parent directory)
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env', override=False)

from server.providers.google_tasks import create_task as create_google_task, GoogleTasksError
from server.db import db_session, init_db, Email, Task
from server.ml import ml_decide 

app = Flask(__name__, static_folder="../client/dist", template_folder="../client/dist")
app.secret_key = os.getenv("FLASK_SECRET", "dev-change-me")
_project_root = Path(__file__).parent.parent.resolve()
_default_secrets_path = _project_root / "client_secret.json"
_env_secrets = os.getenv("GOOGLE_CLIENT_SECRETS")
CLIENT_SECRETS_FILE = _env_secrets if _env_secrets and os.path.isabs(_env_secrets) else str(_project_root / (_env_secrets or "client_secret.json"))

# SCOPES: Gmail read-only + Google Tasks write
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/tasks",
]

REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/oauth2callback")
DEFAULT_PROVIDER = os.getenv("DEFAULT_TASK_PROVIDER", "google_tasks")
DEFAULT_FETCH_LIMIT = int(os.getenv("FETCH_LIMIT", "10"))
TASKS_LIST_TITLE = os.getenv("TASKS_LIST_TITLE", "Email Tasks")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Ensure DB tables exist at startup
logger.info("Initializing database...")
init_db()
logger.info("Database initialized successfully")

# Request logging middleware
@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.path} - IP: {request.remote_addr}")
    if request.method in ['POST', 'PUT', 'PATCH']:
        logger.debug(f"Request data: {dict(request.values)}")

@app.after_request
def log_response_info(response):
    logger.info(f"Response: {request.method} {request.path} - Status: {response.status_code}")
    return response

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
    page_num = 0

    # Page size is capped by Gmail at 100 anyway
    page_size = 100 if max_list is None else min(100, max_list if max_list > 0 else 100)
    logger.debug(f"Fetching Gmail messages: query='{q}', max_list={max_list}, page_size={page_size}")

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
            logger.debug(f"Gmail API page {page_num}: received {len(messages)} messages")
        except Exception as e:
            logger.error(f"Error fetching Gmail messages (page {page_num}): {e}", exc_info=True)
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
            logger.debug(f"Reached end of Gmail results after {page_num} page(s)")
            break

    logger.debug(f"Total Gmail message IDs collected: {len(ids)}")
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
    logger.debug(f"Dispatching task to provider: {provider}")
    if provider == "google_tasks":
        tasks_service = get_tasks_service()
        if not tasks_service:
            logger.error("Google Tasks service not available - not authenticated")
            raise GoogleTasksError("Not authenticated for Google Tasks")
        logger.debug(f"Creating Google Task with title: {payload.get('subject', 'No title')}")
        return create_google_task(tasks_service, TASKS_LIST_TITLE, payload)

    logger.error(f"Unsupported task provider: {provider}")
    raise ValueError(f"Unsupported provider '{provider}'")

# API endpoint to check auth status
@app.route("/api/auth/status")
def auth_status():
    is_authenticated = "credentials" in session
    logger.info(f"Auth status check: authenticated={is_authenticated}")
    return jsonify({"authenticated": is_authenticated})

# API endpoint to get user info (if needed)
@app.route("/api/user")
def user_info():
    if "credentials" not in session:
        logger.warning("User info requested but not authenticated")
        return jsonify({"error": "Not authenticated"}), 401
    logger.info("User info requested: authenticated")
    return jsonify({"authenticated": True})

# Serve React static assets
@app.route("/assets/<path:filename>")
def serve_react_assets(filename):
    import os
    assets_path = os.path.join(os.path.dirname(__file__), "..", "client", "dist", "assets")
    if os.path.exists(assets_path):
        return send_from_directory(assets_path, filename)
    return "React build not found. Run 'cd client && npm install && npm run build'", 404

# Serve React app for all frontend routes (SPA fallback)
@app.route("/")
@app.route("/fetch-emails")
@app.route("/email-results")
@app.route("/view-all-results")
@app.route("/no-emails-found")
def serve_react_app():
    import os
    dist_path = os.path.join(os.path.dirname(__file__), "..", "client", "dist")
    index_path = os.path.join(dist_path, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(dist_path, "index.html")
    # Show helpful message if React build doesn't exist
    return """
    <html>
        <head><title>Taskflow - Setup Required</title></head>
        <body style="font-family: system-ui; padding: 2rem; max-width: 600px; margin: 0 auto;">
            <h1>React Frontend Not Built</h1>
            <p>Please build the React frontend by running:</p>
            <pre style="background: #f5f5f5; padding: 1rem; border-radius: 4px;">
cd client
npm install
npm run build
            </pre>
            <p>Then restart the Flask server.</p>
        </body>
    </html>
    """, 503

@app.route("/authorize")
def authorize():
    logger.info("OAuth authorization initiated")
    try:
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
        logger.info(f"OAuth flow started, redirecting to authorization URL")
    return redirect(authorization_url)
    except Exception as e:
        logger.error(f"Error initiating OAuth flow: {e}", exc_info=True)
        raise

@app.route("/oauth2callback")
def oauth2callback():
    logger.info("OAuth callback received")
    try:
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
        logger.info("OAuth authentication successful, credentials stored in session")
    return redirect("/")
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}", exc_info=True)
        raise

@app.route("/api/logout", methods=["POST"])
def logout():
    logger.info("User logout requested")
    session.pop("credentials", None)
    logger.info("User logged out successfully")
    return jsonify({"success": True, "message": "Logged out successfully"})

# API endpoint for all results
@app.route("/api/tasks/all")
def api_all_results():
    logger.info("Fetching all tasks")
    if "credentials" not in session:
        logger.warning("All tasks requested but not authenticated")
        return jsonify({"error": "Not authenticated"}), 401

    try:
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
        logger.info(f"Retrieved {len(items)} tasks from database")
    return jsonify({"tasks": items, "total": len(items)})
    except Exception as e:
        logger.error(f"Error fetching all tasks: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch tasks"}), 500

@app.route("/api/fetch-emails", methods=["POST", "GET"])
def fetch_emails():
    logger.info("Fetch emails request received")
    service = get_gmail_service()
    if not service:
        logger.warning("Fetch emails requested but not authenticated")
        return jsonify({"error": "Not authenticated. Please log in first."}), 401

    provider = request.values.get("provider", DEFAULT_PROVIDER)
    window = request.values.get("window")  # e.g., 7d
    custom_query = request.values.get("q")
    max_msgs = get_optional_int_param("max", minimum=1)

    since_hours = request.values.get("since_hours")
    since_iso = request.values.get("since")
    dry_run = (request.values.get("dry_run", "false").lower() == "true")
    
    logger.info(f"Fetch emails params: provider={provider}, window={window}, max={max_msgs}, "
                f"since_hours={since_hours}, since={since_iso}, q={custom_query}, dry_run={dry_run}")

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
            logger.debug(f"Processing email {considered}/{len(ids)}: {subject[:50]}...")

            # ML Classification and Task Generation
            logger.debug(f"Running ML classification for email: {subject}")
            ml_result = ml_decide(payload)
            should_create = ml_result.get("should_create", True)
            confidence = ml_result.get("confidence", 0.5)
            reasoning = ml_result.get("reasoning", "")
            
            # Store email with ML metadata
            email_row = get_or_create_email(s, message_id, payload)
            
            # Skip if ML decides not to create task
            if not should_create:
                # Mark as processed but don't create task
                if not email_row.first_processed_at:
                    email_row.first_processed_at = datetime.now(timezone.utc)
                email_row.last_processed_at = datetime.now(timezone.utc)
                email_row.processed = True
                logger.info(f"Skipping email '{subject}' - ML decision: confidence={confidence:.2f}, reason={reasoning}")
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
                logger.debug(f"Email '{subject}' already processed for provider {provider}, skipping")
                continue

            if dry_run:
                logger.info(f"DRY RUN: Would create task for email '{subject}'")
                created_tasks.append({
                    "message_id": message_id,
                    "provider": provider,
                    "task": {"status": "dry_run", "title": payload.get("subject", "")},
                })
                continue

            try:
                logger.info(f"Creating task for email '{subject}' with provider {provider}")
                task = dispatch_task(provider, payload)
                logger.info(f"Task created successfully: {task.get('id', 'unknown')} - {task.get('title', 'no title')}")
            except Exception as err:
                logger.error(f"Error creating task for email '{subject}': {err}", exc_info=True)
                return jsonify({"error": f"Error creating task: {str(err)}"}), 400

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
    
    logger.info(f"Email processing complete: {len(created_tasks)} tasks created, "
                f"{already_processed_count} already processed, {len(ids)} total found, "
                f"{considered} considered")

    return jsonify(result)


if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting Flask server on 127.0.0.1:{port}")
    logger.info(f"Debug mode: True")
    app.run("127.0.0.1", port, debug=True)
