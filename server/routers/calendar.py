from flask import Blueprint, session, jsonify, request
from server.utils import get_current_user, get_calendar_service
from server.db import db_session, CalendarEvent, Email
from sqlalchemy import select

calendar_bp = Blueprint('calendar', __name__)

@calendar_bp.route("/calendar-events/all")
def api_all_calendar_events():
    if "credentials" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = get_current_user()
    if not user:
        return jsonify({"error": "Could not determine user"}), 401

    user_id = user.id

    try:
        with db_session() as s:
            stmt = (
                select(CalendarEvent, Email)
                .join(Email, Email.id == CalendarEvent.email_id)
                .where(CalendarEvent.user_id == user_id)
                .where(Email.user_id == user_id)
                .order_by(CalendarEvent.created_at.desc())
                .limit(200)
            )
            rows = s.execute(stmt).all()
            items = []
            for row in rows:
                ce, e = row
                items.append({
                    "id": ce.id,
                    "google_event_id": ce.google_event_id,
                    "summary": ce.summary or "Meeting",
                    "location": ce.location,
                    "start_datetime": ce.start_datetime.isoformat() if ce.start_datetime else None,
                    "end_datetime": ce.end_datetime.isoformat() if ce.end_datetime else None,
                    "html_link": ce.html_link,
                    "created_at": ce.created_at.isoformat() if ce.created_at else "",
                    "email_subject": e.subject,
                    "email_sender": e.sender,
                    "email_received_at": e.received_at.isoformat() if e.received_at else "",
                    "status": "created",
                })
        return jsonify({"events": items, "total": len(items)})
    except Exception as e:
        return jsonify({"error": "Failed to fetch calendar events"}), 500


@calendar_bp.route("/calendar-events", methods=["DELETE"])
def delete_calendar_events():
    """Delete multiple calendar events from Google Calendar and the database."""
    if "credentials" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = get_current_user()
    if not user:
        return jsonify({"error": "Could not determine user"}), 401

    user_id = user.id

    try:
        data = request.get_json()
        event_ids = data.get("event_ids", [])
        
        if not event_ids or not isinstance(event_ids, list):
            return jsonify({"error": "Invalid request. Expected 'event_ids' array"}), 400

        calendar_service = get_calendar_service()
        deleted_count = 0
        errors = []

        with db_session() as s:
            for event_id_str in event_ids:
                try:
                    event_id = int(event_id_str)
                    stmt = select(CalendarEvent).where(CalendarEvent.id == event_id).where(CalendarEvent.user_id == user_id)
                    calendar_event = s.execute(stmt).scalar_one_or_none()
                    
                    if not calendar_event:
                        errors.append(f"Event {event_id} not found")
                        continue

                    google_event_id = calendar_event.google_event_id
                    if google_event_id and calendar_service:
                        try:
                            calendar_service.events().delete(calendarId="primary", eventId=google_event_id).execute()
                        except Exception:
                            pass

                    s.delete(calendar_event)
                    deleted_count += 1
                except ValueError:
                    errors.append(f"Invalid event ID: {event_id_str}")
                except Exception as e:
                    errors.append(f"Error deleting event {event_id_str}: {str(e)}")

        result = {"message": f"Deleted {deleted_count} event(s) successfully", "deleted_count": deleted_count}
        if errors:
            result["errors"] = errors
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "Failed to delete calendar events"}), 500

