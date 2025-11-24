from flask import Blueprint, session, jsonify, redirect, request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from server.config import CLIENT_SECRETS_FILE, REDIRECT_URI, FRONTEND_URL
from server.utils import SCOPES, get_or_create_user, get_gmail_service
from server.db import db_session
import logging
import os

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/auth/status")
def auth_status():
    is_authenticated = "credentials" in session
    logger.info(f"Auth status check: authenticated={is_authenticated}")
    return jsonify({"authenticated": is_authenticated})

@auth_bp.route("/user")
def user_info():
    if "credentials" not in session:
        logger.warning("User info requested but not authenticated")
        return jsonify({"error": "Not authenticated"}), 401
    logger.info("User info requested: authenticated")
    return jsonify({"authenticated": True})

@auth_bp.route("/authorize")
def authorize():
    logger.info("OAuth authorization initiated")
    logger.info(f"Using redirect URI: {REDIRECT_URI}")
    logger.info(f"Client secrets file: {CLIENT_SECRETS_FILE}")
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
        logger.info(f"OAuth flow started, redirecting to authorization URL: {authorization_url[:100]}...")
        return redirect(authorization_url)
    except Exception as e:
        logger.error(f"Error initiating OAuth flow: {e}", exc_info=True)
        raise

@auth_bp.route("/oauth2callback")
def oauth2callback():
    logger.info("OAuth callback received")
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
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
        # Get and create user in database
        gmail_service = build("gmail", "v1", credentials=credentials)
        try:
            profile = gmail_service.users().getProfile(userId="me").execute()
            user_email = profile.get("emailAddress")
            if user_email:
                session["user_email"] = user_email
                with db_session() as s:
                    get_or_create_user(s, user_email)
                logger.info(f"OAuth authentication successful for user: {user_email}")
        except Exception as e:
            logger.warning(f"Could not fetch user email during OAuth: {e}")
        logger.info("OAuth authentication successful, credentials stored in session")
        frontend_url = os.getenv("FRONTEND_URL", FRONTEND_URL)
        logger.info(f"FRONTEND_URL env var: {os.getenv('FRONTEND_URL')}, config default: {FRONTEND_URL}, using: {frontend_url}")
        logger.info(f"Redirecting to frontend: {frontend_url}")
        return redirect(f"{frontend_url}/")
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}", exc_info=True)
        raise

@auth_bp.route("/logout", methods=["POST"])
def logout():
    logger.info("User logout requested")
    session.pop("credentials", None)
    session.pop("user_email", None)
    logger.info("User logged out successfully")
    return jsonify({"success": True, "message": "Logged out successfully"})

