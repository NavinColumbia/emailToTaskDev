from __future__ import annotations
import os
import json
import base64
from datetime import datetime, timezone

from flask import Flask, request, redirect, session, url_for, jsonify, render_template, flash
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from providers.todoist import create_task as create_todoist_task, TodoistError

load_dotenv(override=False)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-change-me")

CLIENT_SECRETS_FILE = os.getenv("GOOGLE_CLIENT_SECRETS", "client_secret.json")
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/oauth2callback")

FORWARD_LABEL = os.getenv("GMAIL_FORWARD_LABEL", "todoist-forward")
PROCESSED_STORE = os.getenv("PROCESSED_STORE", "processed.json")
TASKS_STORE = os.getenv("TASKS_STORE", "tasks_history.json")
DEFAULT_PROVIDER = os.getenv("DEFAULT_TASK_PROVIDER", "todoist")
DEFAULT_FETCH_LIMIT = int(os.getenv("FETCH_LIMIT", "10"))


def get_gmail_service():
    creds_info = session.get("credentials")
    if not creds_info:
        return None
    credentials = Credentials.from_authorized_user_info(info=creds_info, scopes=SCOPES)
    return build("gmail", "v1", credentials=credentials)


def gmail_list_ids(service, q: str, max_list: int = 50):
    ids = []
    page_token = None
    while True:
        resp = (
            service.users()
            .messages()
            .list(userId="me", q=q, maxResults=min(100, max_list), pageToken=page_token)
            .execute()
        )
        ids.extend(m["id"] for m in resp.get("messages", []))
        if len(ids) >= max_list:
            return ids[:max_list]
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return ids


def load_processed_ids() -> set[str]:
    if not os.path.exists(PROCESSED_STORE):
        return set()
    try:
        with open(PROCESSED_STORE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return set(data if isinstance(data, list) else [])
    except Exception:
        return set()


def save_processed_ids(message_ids: set[str]) -> None:
    with open(PROCESSED_STORE, "w", encoding="utf-8") as fh:
        json.dump(sorted(message_ids), fh, indent=2)


def load_tasks_history() -> list[dict]:
    if not os.path.exists(TASKS_STORE):
        return []
    try:
        with open(TASKS_STORE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_tasks_history(tasks: list[dict]) -> None:
    with open(TASKS_STORE, "w", encoding="utf-8") as fh:
        json.dump(tasks, fh, indent=2)


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


def gather_bodies(payload: dict) -> tuple[str, str]:
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
        "snippet": message.get("snippet", ""),
    }


def dispatch_task(provider: str, payload: dict) -> dict:
    if provider == "todoist":
        return create_todoist_task(payload)
    raise ValueError(f"Unsupported provider '{provider}'")


@app.route("/")
def index():
    return render_template("home.html")


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
    flash("Successfully connected to Gmail!", "success")
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
    
    # Check if this is a redirect from a failed search
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
    
    # Get data from session
    results_data = session.get("email_results")
    if not results_data:
        flash("No results found. Please process emails first.", "warning")
        return redirect(url_for("fetch_emails_page"))
    
    # Clear the results from session after displaying
    session.pop("email_results", None)
    
    return render_template("email_results.html", 
                         processed_count=results_data["processed_count"],
                         query=results_data["query"],
                         created_tasks=results_data["created_tasks"])


def migrate_existing_processed_tasks():
    """Migrate existing processed tasks to task history if not already present"""
    processed_ids = load_processed_ids()
    tasks_history = load_tasks_history()
    
    # Get existing message IDs from task history
    existing_message_ids = {task.get("message_id") for task in tasks_history}
    
    # Find processed IDs that don't have task history entries
    missing_ids = processed_ids - existing_message_ids
    
    if missing_ids:
        # Create placeholder entries for missing tasks
        for message_id in missing_ids:
            placeholder_task = {
                "message_id": message_id,
                "provider": DEFAULT_PROVIDER,
                "task": {
                    "content": "Previously processed email",
                    "subject": "Previously processed email",
                    "sender": "Unknown"
                },
                "created_at": datetime.now(timezone.utc).isoformat(),
                "query": "Previously processed (migrated)"
            }
            tasks_history.append(placeholder_task)
        
        # Save updated task history
        save_tasks_history(tasks_history)
        print(f"Migrated {len(missing_ids)} existing processed tasks to task history")


@app.route("/view-all-results")
def view_all_results():
    if "credentials" not in session:
        return redirect(url_for("authorize"))
    
    # Migrate existing processed tasks to task history
    migrate_existing_processed_tasks()
    
    # Load all tasks from history
    tasks_history = load_tasks_history()
    
    # Sort by creation date (newest first)
    tasks_history.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return render_template("all_results.html", 
                         tasks_history=tasks_history,
                         total_tasks=len(tasks_history))


@app.route("/api/fetch-emails", methods=["POST", "GET"])
def fetch_emails():
    service = get_gmail_service()
    if not service:
        return jsonify({"error": "Not authenticated. Please log in first."}), 401

    provider = request.values.get("provider", DEFAULT_PROVIDER)
    label = request.values.get("label", FORWARD_LABEL)
    window = request.values.get("window")
    custom_query = request.values.get("q")  # Support custom Gmail queries
    max_msgs = int(request.values.get("max", DEFAULT_FETCH_LIMIT))

    if custom_query:
        # Use custom query if provided
        query = custom_query
        if window:
            query += f" newer_than:{window}"
    else:
        # Build query from label and window
        query_parts = [f"label:{label}"] if label else []
        if window:
            query_parts.append(f"newer_than:{window}")
        query = " ".join(query_parts) or "in:inbox"

    ids = gmail_list_ids(service, q=query, max_list=max_msgs)

    processed_ids = load_processed_ids()
    created_tasks = []
    already_processed_count = 0

    for message_id in ids:
        if message_id in processed_ids:
            already_processed_count += 1
            continue

        msg = (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        payload = message_to_payload(msg)

        try:
            task = dispatch_task(provider, payload)
        except TodoistError as err:
            return jsonify({"error": str(err)}), 400
        except ValueError as err:
            return jsonify({"error": str(err)}), 400

        processed_ids.add(message_id)
        created_tasks.append({
            "message_id": message_id,
            "provider": provider,
            "task": task,
        })

    save_processed_ids(processed_ids)

    # Save task history
    if created_tasks:
        tasks_history = load_tasks_history()
        for task in created_tasks:
            task_entry = {
                "message_id": task["message_id"],
                "provider": task["provider"],
                "task": task["task"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "query": query
            }
            tasks_history.append(task_entry)
        save_tasks_history(tasks_history)

    result = {
        "processed": len(created_tasks),
        "query": query,
        "created": created_tasks,
        "total_found": len(ids),
        "already_processed": already_processed_count,
    }
    
    # Handle different scenarios for web requests
    if request.accept_mimetypes.accept_html:
        if len(created_tasks) == 0 and already_processed_count == 0:
            # No emails found at all
            flash("No emails found with the current search criteria.", "warning")
            return redirect(url_for("no_emails_found"))
        elif len(created_tasks) == 0 and already_processed_count > 0:
            # Emails found but already processed - stay on fetch_emails page
            flash(f"Found {already_processed_count} emails, but they were already processed. No new tasks created.", "info")
            return redirect(url_for("fetch_emails_page"))
        else:
            # New emails were processed
            flash(f"Successfully processed {len(created_tasks)} emails!", "success")
            # Store results in session for the results page
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
