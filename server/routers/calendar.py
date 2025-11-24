from flask import Blueprint, session, jsonify
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
                })
        return jsonify({"events": items, "total": len(items)})
    except Exception as e:
        return jsonify({"error": "Failed to fetch calendar events"}), 500


@calendar_bp.route("/calendar-events/<event_id>", methods=["DELETE"])
def delete_calendar_event(event_id: str):
    """Delete a calendar event from Google Calendar and the database."""
    if "credentials" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = get_current_user()
    if not user:
        return jsonify({"error": "Could not determine user"}), 401

    user_id = user.id

    try:
        with db_session() as s:
            # Find the calendar event in the database
            stmt = select(CalendarEvent).where(CalendarEvent.id == int(event_id)).where(CalendarEvent.user_id == user_id)
            calendar_event = s.execute(stmt).scalar_one_or_none()
            
            if not calendar_event:
                return jsonify({"error": "Calendar event not found"}), 404

            # Delete from Google Calendar if we have the google_event_id
            google_event_id = calendar_event.google_event_id
            if google_event_id:
                calendar_service = get_calendar_service()
                if calendar_service:
                    try:
                        calendar_service.events().delete(calendarId="primary", eventId=google_event_id).execute()
                    except Exception as e:
                        # Continue to delete from database even if Google Calendar deletion fails
                        pass

            # Delete from database
            s.delete(calendar_event)

        return jsonify({"message": "Calendar event deleted successfully"})
    except ValueError:
        return jsonify({"error": "Invalid event ID"}), 400
    except Exception as e:
        return jsonify({"error": "Failed to delete calendar event"}), 500

