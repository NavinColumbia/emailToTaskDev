from flask import Blueprint, session, jsonify, request
from server.utils import get_current_user, get_tasks_service
from server.db import db_session, Task, Email
from server.providers.google_tasks import delete_task as delete_google_task, GoogleTasksError
from sqlalchemy import select

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route("/tasks/all")
def api_all_results():
    if "credentials" not in session:
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
                    "id": t.id,
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
        return jsonify({"tasks": items, "total": len(items)})
    except Exception as e:
        return jsonify({"error": "Failed to fetch tasks"}), 500


@tasks_bp.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id: str):
    """Delete a task from Google Tasks and the database."""
    if "credentials" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = get_current_user()
    if not user:
        return jsonify({"error": "Could not determine user"}), 401

    user_id = user.id

    try:
        with db_session() as s:
            # Find the task in the database
            stmt = select(Task).where(Task.id == int(task_id)).where(Task.user_id == user_id)
            task = s.execute(stmt).scalar_one_or_none()
            
            if not task:
                return jsonify({"error": "Task not found"}), 404

            # Get task metadata to find tasklist_id and provider_task_id
            metadata = task.provider_metadata or {}
            provider_task_id = task.provider_task_id
            tasklist_id = metadata.get("_tasklist_id")

            if not provider_task_id:
                s.delete(task)
                return jsonify({"message": "Task deleted from database"})

            # Delete from Google Tasks if we have the necessary info
            if task.provider == "google_tasks" and tasklist_id:
                tasks_service = get_tasks_service()
                if not tasks_service:
                    return jsonify({"error": "Not authenticated for Google Tasks"}), 401
                
                try:
                    delete_google_task(tasks_service, tasklist_id, provider_task_id)
                except GoogleTasksError as e:
                    # Continue to delete from database even if Google Tasks deletion fails
                    pass

            # Delete from database
            s.delete(task)

        return jsonify({"message": "Task deleted successfully"})
    except ValueError:
        return jsonify({"error": "Invalid task ID"}), 400
    except Exception as e:
        return jsonify({"error": "Failed to delete task"}), 500

