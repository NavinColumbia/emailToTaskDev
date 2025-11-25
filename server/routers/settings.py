from flask import Blueprint, session, jsonify, request
from datetime import datetime, timezone
from server.utils import get_current_user
from server.db import db_session, UserSettings
from sqlalchemy import select

settings_bp = Blueprint('settings', __name__)

@settings_bp.route("/settings", methods=["GET"])
def get_settings():
    """Get user settings."""
    if "credentials" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = get_current_user()
    if not user:
        return jsonify({"error": "Could not determine user"}), 401

    user_id = user.id

    try:
        with db_session() as s:
            stmt = select(UserSettings).where(UserSettings.user_id == user_id)
            user_settings = s.execute(stmt).scalar_one_or_none()
            
            if not user_settings:
                # Return default settings if none exist
                return jsonify({
                    "max": 10,
                    "window": "1d",
                })
            
            return jsonify({
                "max": user_settings.max,
                "window": user_settings.window,
                })
    except Exception as e:
        return jsonify({"error": "Failed to fetch settings"}), 500

@settings_bp.route("/settings", methods=["PUT", "POST"])
def update_settings():
    """Create or update user settings."""
    if "credentials" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = get_current_user()
    if not user:
        return jsonify({"error": "Could not determine user"}), 401

    user_id = user.id

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        max_value = data.get("max")
        window = data.get("window", "")

        with db_session() as s:
            stmt = select(UserSettings).where(UserSettings.user_id == user_id)
            user_settings = s.execute(stmt).scalar_one_or_none()

            if user_settings:
                # Update existing settings
                user_settings.provider = "google_tasks"
                user_settings.max = max_value
                user_settings.window = window
                user_settings.updated_at = datetime.now(timezone.utc)
            else:
                # Create new settings
                user_settings = UserSettings(
                    user_id=user_id,
                    provider="google_tasks",
                    max=max_value,
                    window=window,
                )
                s.add(user_settings)
            
            s.flush()
            
            # Extract values before session closes
            result = {
                "max": user_settings.max,
                "window": user_settings.window,
            }

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "Failed to update settings"}), 500

