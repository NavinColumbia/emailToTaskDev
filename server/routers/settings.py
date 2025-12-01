from flask import Blueprint, session, jsonify, request
from datetime import datetime, timezone
from server.utils import get_current_user, require_auth
from server.db import db_session, UserSettings
from sqlalchemy import select

settings_bp = Blueprint('settings', __name__)


def extract_category_names(raw: list[str] | list[dict] | None) -> list[str]:
    """
    Extract category names from input, accepting both formats.
    
    Args:
        raw: Either a list of strings or a list of dicts with 'name' or 'label' keys
    
    Returns:
        A list of category name strings, ignoring empty names
    """
    if not raw:
        return []
    
    names = []
    for item in raw:
        if isinstance(item, str):
            # Simple string category
            if item.strip():
                names.append(item.strip())
        elif isinstance(item, dict):
            # Rich category object - extract name
            name = item.get("name") or item.get("label") or ""
            if name and isinstance(name, str) and name.strip():
                names.append(name.strip())
    
    return names

@settings_bp.route("/settings", methods=["GET"])
@require_auth
def get_settings():
    """Get user settings."""

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
                    "task_categories": [],
                    "calendar_categories": [],
                    "auto_generate": True,
                })
            
            # Extract category names (handles backward compatibility with old string format)
            # If stored as objects, extract just the names; if stored as strings, use as-is
            task_cats = extract_category_names(user_settings.task_categories)
            cal_cats = extract_category_names(user_settings.calendar_categories)
            
            return jsonify({
                "max": user_settings.max,
                "window": user_settings.window,
                "task_categories": task_cats,
                "calendar_categories": cal_cats,
                "auto_generate": user_settings.auto_generate if user_settings.auto_generate is not None else True,
            })
    except Exception as e:
        return jsonify({"error": "Failed to fetch settings"}), 500

@settings_bp.route("/settings", methods=["PUT", "POST"])
@require_auth
def update_settings():
    """Create or update user settings."""

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
        task_categories_raw = data.get("task_categories")
        calendar_categories_raw = data.get("calendar_categories")
        auto_generate = data.get("auto_generate", True)

        # Extract category names from input (accepts both old and new formats)
        # Old format: ["Work", "Personal"]
        # New format: [{"name": "Work", "description": ""}]
        # Result: ["Work", "Personal"] (array of strings)
        task_categories_normalized = extract_category_names(task_categories_raw) if task_categories_raw is not None else []
        calendar_categories_normalized = extract_category_names(calendar_categories_raw) if calendar_categories_raw is not None else []

        with db_session() as s:
            stmt = select(UserSettings).where(UserSettings.user_id == user_id)
            user_settings = s.execute(stmt).scalar_one_or_none()

            if user_settings:
                # Update existing settings
                user_settings.provider = "google_tasks"
                user_settings.max = max_value
                user_settings.window = window
                user_settings.task_categories = task_categories_normalized
                user_settings.calendar_categories = calendar_categories_normalized
                user_settings.auto_generate = auto_generate if auto_generate is not None else True
                user_settings.updated_at = datetime.now(timezone.utc)
            else:
                # Create new settings
                user_settings = UserSettings(
                    user_id=user_id,
                    provider="google_tasks",
                    max=max_value,
                    window=window,
                    task_categories=task_categories_normalized,
                    calendar_categories=calendar_categories_normalized,
                    auto_generate=auto_generate if auto_generate is not None else True,
                )
                s.add(user_settings)
            
            s.flush()
            
            # Extract values before session closes
            # Extract names again to ensure consistent format (defensive programming)
            result = {
                "max": user_settings.max,
                "window": user_settings.window,
                "task_categories": extract_category_names(user_settings.task_categories),
                "calendar_categories": extract_category_names(user_settings.calendar_categories),
                "auto_generate": user_settings.auto_generate if user_settings.auto_generate is not None else True,
            }

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "Failed to update settings"}), 500

