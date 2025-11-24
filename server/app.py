from __future__ import annotations
import os
import sys
import logging
from pathlib import Path
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = FLASK_SECRET
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Enable CORS for all routes
CORS(app, supports_credentials=True, origins=['http://localhost:5173', 'http://127.0.0.1:5173', 'https://taskflow-82031.web.app'])

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

@app.route('/')
def index():
    return "Hello, World!"

if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    port = int(os.getenv("PORT", 5001))
    logger.info(f"Starting Flask server on localhost:{port}")
    logger.info(f"Debug mode: True")
    app.run("localhost", port, debug=True)
