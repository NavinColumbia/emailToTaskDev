from __future__ import annotations
import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from flask import Flask, request
from flask_cors import CORS

# Add project root to Python path to enable server.* imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from server.config import FLASK_SECRET
from server.db import init_db
from server.routers import auth, tasks, calendar, emails, settings

# Configure logging
log_dir = Path(project_root) / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "app.log"

# Set up logging with file handler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = FLASK_SECRET
# For cross-domain cookies (frontend and backend on different domains)
if os.getenv('FLASK_ENV') == 'production':
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_DOMAIN'] = None
else:
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_PATH'] = '/'

# Enable CORS for all routes
CORS(app, supports_credentials=True, origins=['http://localhost:5173', 'http://127.0.0.1:5173', 'https://taskflow-474913.web.app'])

# Register blueprints
app.register_blueprint(auth.auth_bp)
app.register_blueprint(tasks.tasks_bp)
app.register_blueprint(calendar.calendar_bp)
app.register_blueprint(emails.emails_bp)
app.register_blueprint(settings.settings_bp)

# Ensure DB tables exist at startup
logger.info("Initializing database...")
init_db()
logger.info("Database initialized successfully")

@app.route('/')
def index():
    return "Hello, World!"

if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    port = int(os.getenv("PORT", 5001))
    logger.info(f"Starting Flask server on localhost:{port}")
    logger.info(f"Debug mode: {os.getenv('FLASK_ENV') != 'production'}")
    app.run("localhost", port, debug=True)
