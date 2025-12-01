from flask import Blueprint, session, jsonify, request
from server.utils import get_current_user, get_tasks_service, require_auth
from server.db import db_session, Task, Email
from server.providers.google_tasks import delete_task as delete_google_task, create_task as create_google_task, GoogleTasksError
from server.config import TASKS_LIST_TITLE
from sqlalchemy import select

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route("/tasks/all")
@require_auth
def api_all_results():

    user = get_current_user()
    if not user:
        return jsonify({"error": "Could not determine user"}), 401

    # Extract user_id before the session closes to avoid detached instance error
    user_id = user.id

    # Get optional query parameters
    category = request.values.get("category")
    sort = request.values.get("sort")

    try:
        with db_session() as s:
            stmt = (
                select(Task, Email)
                .join(Email, Email.id == Task.email_id)
                .where(Task.user_id == user_id)
                .where(Email.user_id == user_id)
            )
            
            # Apply category filter if provided
            if category:
                stmt = stmt.where(Task.category == category)
            
            # Apply sorting
            if sort == "category":
                stmt = stmt.order_by(Task.category.asc(), Task.created_at.desc())
            else:
                stmt = stmt.order_by(Task.created_at.desc())
            
            stmt = stmt.limit(200)
            rows = s.execute(stmt).all()
            items = []
            for row in rows:
                t, e = row
                md = t.provider_metadata or {}
                # For pending tasks, title is in metadata directly; for created tasks, it's in provider response
                task_title = md.get("title")
                if not task_title and t.status == "pending":
                    # For pending tasks, check if there's a payload with subject
                    payload = md.get("payload", {})
                    task_title = payload.get("subject") or e.subject
                task_link = md.get("webLink") or md.get("selfLink")
                task_due = md.get("due")
                items.append({
                    "id": t.id,
                    "provider": t.provider,
                    "provider_task_id": t.provider_task_id,
                    "created_at": t.created_at.isoformat() if t.created_at else "",
                    "email_subject": e.subject,
                    "email_sender": e.sender,
                    "email_received_at": e.received_at.isoformat() if e.received_at else "",
                    "task_title": task_title,
                    "task_link": task_link,
                    "task_due": task_due,
                    "status": t.status or "created",
                    "category": t.category,
                })
        return jsonify({"tasks": items, "total": len(items)})
    except Exception as e:
        return jsonify({"error": "Failed to fetch tasks"}), 500


@tasks_bp.route("/tasks", methods=["DELETE"])
@require_auth
def delete_tasks():
    """Delete multiple tasks from Google Tasks and the database."""

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


@tasks_bp.route("/tasks/confirm", methods=["POST"])
@require_auth
def confirm_tasks():
    """Confirm and create pending tasks in Google Tasks."""
    
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
        if not tasks_service:
            return jsonify({"error": "Not authenticated for Google Tasks"}), 401

        confirmed_count = 0
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
                    
                    if task.status != "pending":
                        errors.append(f"Task {task_id} is not pending (status: {task.status})")
                        continue

                    # Get task metadata
                    metadata = task.provider_metadata or {}
                    payload = metadata.get("payload", {})
                    
                    # Create task in Google Tasks
                    try:
                        created_task = create_google_task(tasks_service, TASKS_LIST_TITLE, payload)
                        task.provider_task_id = created_task.get("id") if isinstance(created_task, dict) else None
                        task.provider_metadata = created_task if isinstance(created_task, dict) else metadata
                        task.status = "created"
                        confirmed_count += 1
                    except GoogleTasksError as e:
                        errors.append(f"Error creating task {task_id} in Google Tasks: {str(e)}")
                        continue
                        
                except ValueError:
                    errors.append(f"Invalid task ID: {task_id_str}")
                except Exception as e:
                    errors.append(f"Error confirming task {task_id_str}: {str(e)}")

        result = {"message": f"Confirmed {confirmed_count} task(s) successfully", "confirmed_count": confirmed_count}
        if errors:
            result["errors"] = errors
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "Failed to confirm tasks"}), 500

