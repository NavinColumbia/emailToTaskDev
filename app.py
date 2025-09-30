import os
import re
import json
import base64
import datetime as dt
from urllib.parse import urlsplit, urlunsplit, parse_qsl

from flask import Flask, request, redirect, session, url_for, jsonify
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

# Optional: if you install bleach for stronger HTML sanitizing
try:
    import bleach
    BLEACH = True
except Exception:
    BLEACH = False

# -----------------------------
# Flask App Configuration
# -----------------------------
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-change-me")

CLIENT_SECRETS_FILE = os.getenv("GOOGLE_CLIENT_SECRETS", "client_secret.json")
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
]
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/oauth2callback")

# In-memory store (dev only)
emails_db = []  # list of normalized email dicts

# -----------------------------
# Google / Gmail helpers
# -----------------------------

def get_gmail_service():
    creds_info = session.get("credentials")
    if not creds_info:
        return None
    credentials = Credentials.from_authorized_user_info(info=creds_info, scopes=SCOPES)
    return build("gmail", "v1", credentials=credentials)


def gmail_list_ids(service, q: str, max_list: int = 100):
    """List message IDs for a given Gmail search query (paginated)."""
    ids = []
    page_token = None
    while True:
        resp = (
            service.users()
            .messages()
            .list(userId="me", q=q, maxResults=min(100, max_list), pageToken=page_token)
            .execute()
        )
        for m in resp.get("messages", []):
            ids.append(m["id"])
            if len(ids) >= max_list:
                return ids
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return ids


# -----------------------------
# MIME decoding & cleaning
# -----------------------------

ZERO_WIDTH_RE = re.compile(
    "[\u200B\u200C\u200D\u2060\uFEFF\u034F\u00AD]"  # ZWSP, ZWNJ, ZWJ, WJ, BOM, CGJ, soft hyphen
)
MULTISPACE_RE = re.compile(r"[ \t\x0b\x0c\r\f]+")

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "gclid",
    "fbclid",
    "mc_eid",
    "mkt_tok",
    "si",
    "lid",
}

ALLOWED_TAGS = [
    "p",
    "br",
    "ul",
    "ol",
    "li",
    "b",
    "strong",
    "i",
    "em",
    "u",
    "a",
    "blockquote",
    "code",
    "pre",
    "hr",
    "h1",
    "h2",
    "h3",
    "h4",
]
ALLOWED_ATTRS = {"a": ["href", "title"]}


def strip_invisible(s: str) -> str:
    if not s:
        return s
    s = ZERO_WIDTH_RE.sub("", s)
    # collapse weird whitespace runs, but preserve newlines
    s = re.sub(r"\s+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = MULTISPACE_RE.sub(" ", s)
    return s.strip()


def strip_tracking_query(url: str) -> str:
    try:
        parts = urlsplit(url)
        q = [(k, v) for (k, v) in parse_qsl(parts.query, keep_blank_values=True) if k not in TRACKING_PARAMS]
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "&".join(f"{k}={v}" for k, v in q), parts.fragment))
    except Exception:
        return url


def sanitize_html(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")

    # Drop scripts/styles/noscript/forms/svg and tiny tracking pixels
    for tag in soup(["script", "style", "noscript", "svg", "form", "iframe", "object", "embed"]):
        tag.decompose()

    # Remove all images (or keep and filter). Here: remove to avoid pixels.
    for img in soup.find_all("img"):
        try:
            # Drop obvious 1x1 or display:none trackers
            w = int(img.get("width") or 0)
            h = int(img.get("height") or 0)
            if w <= 1 or h <= 1:
                img.decompose()
                continue
        except Exception:
            pass
        img.decompose()

    # Rewrite links: strip tracking params & javascript: schemes
    for a in soup.find_all("a"):
        href = a.get("href")
        if href:
            href = href.strip()
            if href.lower().startswith("javascript:"):
                a.attrs.pop("href", None)
            else:
                a["href"] = strip_tracking_query(href)
        # prune noisy attributes
        for attr in list(a.attrs.keys()):
            if attr not in ("href", "title"):
                del a[attr]

    # Unwrap spans/divs with no semantic value
    for tag in soup.find_all(["span", "font", "div"]):
        if not tag.attrs:
            tag.unwrap()

    clean_html = str(soup)

    if BLEACH:
        clean_html = bleach.clean(
            clean_html,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRS,
            strip=True,
        )
    return clean_html


def html_to_text(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")

    # replace <br> with newlines
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # add newlines before block elements to keep structure
    for block in soup.find_all(["p", "div", "ul", "ol", "li", "blockquote", "pre", "h1", "h2", "h3", "h4", "hr"]):
        block.insert_before("\n")

    text = soup.get_text(" ")
    return strip_invisible(text)


def decode_part_bytes(part) -> bytes:
    data = part.get("body", {}).get("data")
    if not data:
        return b""
    # Gmail uses base64url
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def part_charset(part) -> str:
    # Try to detect charset from headers like: Content-Type: text/plain; charset="UTF-8"
    headers = {h["name"].lower(): h["value"] for h in part.get("headers", []) if h.get("name") and h.get("value")}
    ctype = headers.get("content-type", part.get("mimeType", ""))
    m = re.search(r"charset=([\w\-:]+)", ctype, re.I)
    if m:
        return m.group(1).strip().strip('"').strip("'")
    return "utf-8"


def decode_part_text(part) -> str:
    raw = decode_part_bytes(part)
    if not raw:
        return ""
    enc = part_charset(part)
    try:
        return raw.decode(enc, errors="replace")
    except Exception:
        # fallback
        for alt in ("utf-8", "latin-1"):
            try:
                return raw.decode(alt, errors="replace")
            except Exception:
                pass
    return raw.decode("utf-8", errors="replace")


def walk_parts(payload):
    """
    Walk MIME tree and return aggregated text/plain and text/html bodies.
    Preference: if multipart/alternative, keep the richest version available.
    """
    texts = []
    htmls = []

    def _walk(p):
        mime = (p.get("mimeType") or "").lower()
        body = p.get("body", {})
        if p.get("parts"):
            # multipart/* container
            for ch in p["parts"]:
                _walk(ch)
            return
        # leaf
        if mime.startswith("text/plain") and ("data" in body or body.get("size", 0) > 0):
            texts.append(decode_part_text(p))
        elif mime.startswith("text/html") and ("data" in body or body.get("size", 0) > 0):
            htmls.append(decode_part_text(p))
        else:
            # ignore attachments or unknown leaf types here
            pass

    _walk(payload)

    # Combine parts; prefer the longest sensible piece (avoid duplicates)
    text = "\n\n".join([t for t in texts if t and t.strip()])
    html = "\n\n".join([h for h in htmls if h and h.strip()])
    return text.strip(), html.strip()


def extract_headers(payload):
    headers = {}
    for h in payload.get("headers", []):
        n, v = h.get("name"), h.get("value")
        if not n or not v:
            continue
        if n in {"Date", "Subject", "From", "To", "Cc", "Bcc", "Message-Id"}:
            headers[n] = v
    return headers


def extract_links(html: str):
    links = []
    if not html:
        return links
    soup = BeautifulSoup(html, "lxml")
    for a in soup.find_all("a"):
        href = a.get("href")
        if href:
            links.append(strip_tracking_query(href))
    # de-dup preserve order
    seen = set()
    uniq = []
    for u in links:
        if u not in seen:
            uniq.append(u)
            seen.add(u)
    return uniq


def normalize_message(msg):
    payload = msg.get("payload", {})
    text_raw, html_raw = walk_parts(payload)

    # Fallback: if neither, try top-level body
    if not text_raw and not html_raw and payload.get("body", {}).get("data"):
        guess = decode_part_text(payload)
        if (payload.get("mimeType", "").lower() or "").startswith("text/html"):
            html_raw = guess
        else:
            text_raw = guess

    # Clean & sanitize
    html_clean = sanitize_html(html_raw) if html_raw else ""
    text_clean = strip_invisible(text_raw) if text_raw else html_to_text(html_clean)

    headers = extract_headers(payload)

    obj = {
        "id": msg.get("id"),
        "threadId": msg.get("threadId"),
        "internalDate": dt.datetime.utcfromtimestamp(int(msg.get("internalDate", "0")) / 1000.0).isoformat() + "Z"
        if msg.get("internalDate")
        else None,
        "labelIds": msg.get("labelIds", []),
        "snippet": msg.get("snippet", ""),
        "headers": headers,
        "body": {
            "text_clean": text_clean,
            "html_clean": html_clean,
            # Optionally include raw versions for debugging (commented by default)
            # "text_raw": text_raw,
            # "html_raw": html_raw,
        },
        "links": extract_links(html_raw or ""),
    }
    return obj


# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def index():
    if "credentials" in session:
        return (
            "You are logged in! "
            '<a href="/fetch-emails">Fetch Emails</a> or '
            '<a href="/stored">View Stored</a> or '
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

    # Query params
    window = request.args.get("window", "1d")  # e.g., 1d, 7d, 1m
    include_promotions = request.args.get("include_promotions", "false").lower() in {"1", "true", "yes"}
    max_msgs = int(request.args.get("max", 25))

    base_q = f"newer_than:{window} in:inbox"
    if not include_promotions:
        base_q += " -category:social -category:promotions -category:updates -category:forums"

    q = request.args.get("q", base_q)

    ids = gmail_list_ids(service, q=q, max_list=max_msgs)

    global emails_db
    emails_db.clear()

    fetched = 0
    for mid in ids:
        msg = service.users().messages().get(userId="me", id=mid, format="full").execute()
        norm = normalize_message(msg)
        emails_db.append(norm)
        fetched += 1

    return jsonify({
        "message": f"Fetched and stored {fetched} emails.",
        "query": q,
        "data": emails_db,
    })


@app.route("/stored")
def stored():
    return jsonify({"count": len(emails_db), "data": emails_db})


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # dev only
    port = int(os.getenv("PORT", 5000))
    app.run("127.0.0.1", port, debug=True)
