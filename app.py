from __future__ import annotations
import os
import json
import base64
from datetime import datetime, timezone

from flask import Flask, request, redirect, session, url_for, jsonify
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
    if "credentials" in session:
        return (
            "You are logged in! "
            '<a href="/fetch-emails">Fetch Emails</a> or '
            '<a href="/logout">Logout</a>'
        )
    return 'Welcome! <a href="/authorize">Login with Google</a>'


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
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.pop("credentials", None)
    return redirect(url_for("index"))


@app.route("/fetch-emails", methods=["POST", "GET"])
def fetch_emails():
    service = get_gmail_service()
    if not service:
        return redirect(url_for("authorize"))

    provider = request.args.get("provider", DEFAULT_PROVIDER)
    label = request.args.get("label", FORWARD_LABEL)
    window = request.args.get("window")
    max_msgs = int(request.args.get("max", DEFAULT_FETCH_LIMIT))

    query_parts = [f"label:{label}"] if label else []
    if window:
        query_parts.append(f"newer_than:{window}")
    query = " ".join(query_parts) or "in:inbox"

    ids = gmail_list_ids(service, q=query, max_list=max_msgs)

    processed_ids = load_processed_ids()
    created_tasks = []

    for message_id in ids:
        if message_id in processed_ids:
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

    return jsonify(
        {
            "processed": len(created_tasks),
            "query": query,
            "created": created_tasks,
        }
    )


if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    port = int(os.getenv("PORT", 5000))
    app.run("127.0.0.1", port, debug=True)
