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
                    "status": "created",
                })
        return jsonify({"tasks": items, "total": len(items)})
    except Exception as e:
        return jsonify({"error": "Failed to fetch tasks"}), 500


@tasks_bp.route("/tasks", methods=["DELETE"])
def delete_tasks():
    """Delete multiple tasks from Google Tasks and the database."""
    if "credentials" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = get_current_user()
    if not user:
        return jsonify({"error": "Could not determine user"}), 401

    user_id = user.id

    try:
        data = request.get_json()
        task_ids = data.get("task_ids", [])
        
        if not task_ids or not isinstance(task_ids, list):
            return jsonify({"error": "Invalid request. Expected 'task_ids' array"}), 400

        tasks_service = get_tasks_service()
        deleted_count = 0
        errors = []

        with db_session() as s:
            for task_id_str in task_ids:
                try:
                    task_id = int(task_id_str)
                    stmt = select(Task).where(Task.id == task_id).where(Task.user_id == user_id)
                    task = s.execute(stmt).scalar_one_or_none()
                    
                    if not task:
                        errors.append(f"Task {task_id} not found")
                        continue

                    metadata = task.provider_metadata or {}
                    provider_task_id = task.provider_task_id
                    tasklist_id = metadata.get("_tasklist_id")

                    if provider_task_id and task.provider == "google_tasks" and tasklist_id and tasks_service:
                        try:
                            delete_google_task(tasks_service, tasklist_id, provider_task_id)
                        except GoogleTasksError:
                            pass

                    s.delete(task)
                    deleted_count += 1
                except ValueError:
                    errors.append(f"Invalid task ID: {task_id_str}")
                except Exception as e:
                    errors.append(f"Error deleting task {task_id_str}: {str(e)}")

        result = {"message": f"Deleted {deleted_count} task(s) successfully", "deleted_count": deleted_count}
        if errors:
            result["errors"] = errors
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "Failed to delete tasks"}), 500

