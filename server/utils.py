from __future__ import annotations
import base64
from datetime import datetime, timezone, timedelta
from typing import Tuple
from functools import wraps
from flask import session, request, jsonify
import jwt
from server.config import FLASK_SECRET
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
from sqlalchemy import select
from server.db import db_session, User

# SCOPES: Gmail read-only + Google Tasks write
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/calendar.events",
]

def encode_jwt(user_email: str) -> str:
    """Create a JWT token for a user."""
    payload = {
        "email": user_email,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, FLASK_SECRET, algorithm="HS256")

def decode_jwt(token: str) -> dict | None:
    """Decode and verify a JWT token."""
    try:
        return jwt.decode(token, FLASK_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_jwt_from_request() -> str | None:
    """Extract JWT token from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None

def require_auth(f):
    """Decorator to require JWT authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_jwt_from_request()
        if not token:
            return jsonify({"error": "Not authenticated"}), 401
        
        payload = decode_jwt(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        user_email = payload.get("email")
        if not user_email:
            return jsonify({"error": "Invalid token"}), 401
        
        # Store user_email in request context for use in the route
        request.user_email = user_email
        return f(*args, **kwargs)
    return decorated_function

def _get_credentials():
    if request and hasattr(request, 'user_email') and request.user_email:
        with db_session() as s:
            stmt = select(User).where(User.email == request.user_email)
            user = s.execute(stmt).scalar_one_or_none()
            if user and user.google_token:
                creds_info = {
                    "token": user.google_token,
                    "refresh_token": user.google_refresh_token,
                    "token_uri": user.google_token_uri,
                    "client_id": user.google_client_id,
                    "client_secret": user.google_client_secret,
                    "scopes": user.google_scopes,
                }
                return Credentials.from_authorized_user_info(info=creds_info, scopes=SCOPES)

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

def get_or_create_user(session, email: str) -> User:
    """Get or create a user by email address."""
    stmt = select(User).where(User.email == email)
    user = session.execute(stmt).scalar_one_or_none()
    if user:
        return user
    user = User(
        email=email,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(user)
    session.flush()
    return user

def get_current_user() -> User | None:
    """Get the current authenticated user from JWT."""
    if not hasattr(request, 'user_email'):
        return None
    
    user_email = request.user_email
    with db_session() as s:
        user = get_or_create_user(s, user_email)
        _ = user.id
        s.expunge(user)
        return user

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

