from flask import Blueprint, session, jsonify
from server.utils import get_current_user
from server.db import db_session, Task, Email
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route("/tasks/all")
def api_all_results():
    logger.info("Fetching all tasks")
    if "credentials" not in session:
        logger.warning("All tasks requested but not authenticated")
        return jsonify({"error": "Not authenticated"}), 401

    user = get_current_user()
    if not user:
        return jsonify({"error": "Could not determine user"}), 401

    # Extract user_id before the session closes to avoid detached instance error
    user_id = user.id

    try:
        with db_session() as s:
            stmt = (
                select(Task, Email)
                .join(Email, Email.id == Task.email_id)
                .where(Task.user_id == user_id)
                .where(Email.user_id == user_id)
                .order_by(Task.created_at.desc())
                .limit(200)
            )
            rows = s.execute(stmt).all()
            items = []
            for row in rows:
                t, e = row
                md = t.provider_metadata or {}
                items.append({
                    "provider": t.provider,
                    "provider_task_id": t.provider_task_id,
                    "created_at": t.created_at.isoformat() if t.created_at else "",
                    "email_subject": e.subject,
                    "email_sender": e.sender,
                    "email_received_at": e.received_at.isoformat() if e.received_at else "",
                    "task_title": md.get("title"),
                    "task_link": md.get("webLink") or md.get("selfLink"),
                    "task_due": md.get("due"),
                })
            logger.info(f"Retrieved {len(items)} tasks from database")
        return jsonify({"tasks": items, "total": len(items)})
    except Exception as e:
        logger.error(f"Error fetching all tasks: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch tasks"}), 500

