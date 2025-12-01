from flask import Blueprint, session, jsonify, redirect, request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from server.config import CLIENT_SECRETS_CONFIG, REDIRECT_URI, FRONTEND_URL
from server.utils import SCOPES, get_or_create_user, encode_jwt
from server.db import db_session
import os
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

def _create_flow():
    """Create OAuth flow from config dict (from environment variable)."""
    return Flow.from_client_config(
        CLIENT_SECRETS_CONFIG,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

@auth_bp.route("/auth/status")
def auth_status():
    from server.utils import get_jwt_from_request, decode_jwt
    token = get_jwt_from_request()
    if not token:
        return jsonify({"authenticated": False})
    
    payload = decode_jwt(token)
    if not payload:
        return jsonify({"authenticated": False})
    
    return jsonify({"authenticated": True})

@auth_bp.route("/user")
def user_info():
    from server.utils import get_jwt_from_request, decode_jwt
    token = get_jwt_from_request()
    if not token:
        return jsonify({"error": "Not authenticated"}), 401
    
    payload = decode_jwt(token)
    if not payload:
        return jsonify({"error": "Invalid or expired token"}), 401
    
    return jsonify({"authenticated": True})

@auth_bp.route("/authorize")
def authorize():
    try:
        flow = _create_flow()
        
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        session["state"] = state
        return redirect(authorization_url)
    except Exception as e:
        raise

@auth_bp.route("/oauth2callback")
def oauth2callback():
    try:
        flow = _create_flow()
        if os.getenv('FLASK_ENV') == 'production':
            auth_response_url = REDIRECT_URI
            if request.query_string:
                auth_response_url += '?' + request.query_string.decode('utf-8')
        else:
            auth_response_url = request.url
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        flow.fetch_token(authorization_response=auth_response_url)
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
                logger.info(f"User authenticated: {user_email}")
                
                # Generate JWT token
                jwt_token = encode_jwt(user_email)
                session["jwt_token"] = jwt_token
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
        # Mark session as modified to ensure it's saved
        session.modified = True
        frontend_url = os.getenv("FRONTEND_URL", FRONTEND_URL)
        logger.info(f"Redirecting to frontend: {frontend_url}")
        logger.info(f"Session after auth - has credentials: {'credentials' in session}, has user_email: {'user_email' in session}")
        
        # Redirect with JWT token as query parameter for frontend to pick up
        jwt_token = session.get("jwt_token", "")
        redirect_url = f"{frontend_url}/"
        if jwt_token:
            redirect_url = f"{frontend_url}/?token={jwt_token}"
        
        response = redirect(redirect_url)
        logger.info(f"Response headers - Set-Cookie present: {'Set-Cookie' in str(response.headers)}")
        return response
    except Exception as e:
        raise

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("credentials", None)
    session.pop("user_email", None)
    session.pop("jwt_token", None)
    return jsonify({"success": True, "message": "Logged out successfully"})

