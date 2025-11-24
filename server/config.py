import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (parent directory)
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env', override=False)

_project_root = Path(__file__).parent.parent.resolve()
_env_secrets = os.getenv("GOOGLE_CLIENT_SECRETS")
CLIENT_SECRETS_FILE = _env_secrets if _env_secrets and os.path.isabs(_env_secrets) else str(_project_root / (_env_secrets or "client_secret.json"))

REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5173/oauth2callback")
DEFAULT_PROVIDER = os.getenv("DEFAULT_TASK_PROVIDER", "google_tasks")
DEFAULT_FETCH_LIMIT = int(os.getenv("FETCH_LIMIT", "10"))
TASKS_LIST_TITLE = os.getenv("TASKS_LIST_TITLE", "Email Tasks")
FLASK_SECRET = os.getenv("FLASK_SECRET", "dev-change-me")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

