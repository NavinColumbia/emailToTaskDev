import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (parent directory)
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env', override=False)

_google_client_secrets_json = os.getenv("GOOGLE_CLIENT_SECRETS_JSON")
if not _google_client_secrets_json:
    raise ValueError("GOOGLE_CLIENT_SECRETS_JSON environment variable is required")

try:
    CLIENT_SECRETS_CONFIG = json.loads(_google_client_secrets_json)
except json.JSONDecodeError as e:
    raise ValueError(f"Failed to parse GOOGLE_CLIENT_SECRETS_JSON: {e}")

REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5001/oauth2callback")
DEFAULT_PROVIDER = os.getenv("DEFAULT_TASK_PROVIDER", "google_tasks")
DEFAULT_FETCH_LIMIT = int(os.getenv("FETCH_LIMIT", "10"))
TASKS_LIST_TITLE = os.getenv("TASKS_LIST_TITLE", "Email Tasks")
FLASK_SECRET = os.getenv("FLASK_SECRET", "dev-change-me")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

