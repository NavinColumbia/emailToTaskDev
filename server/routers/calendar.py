from flask import Blueprint, session, jsonify
from server.utils import get_current_user
from server.db import db_session, CalendarEvent, Email
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

calendar_bp = Blueprint('calendar', __name__)

@calendar_bp.route("/calendar-events/all")
def api_all_calendar_events():
    logger.info("Fetching all calendar events")
    if "credentials" not in session:
        logger.warning("All calendar events requested but not authenticated")
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
            logger.info(f"Retrieved {len(items)} calendar events from database")
        return jsonify({"events": items, "total": len(items)})
    except Exception as e:
        logger.error(f"Error fetching all calendar events: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch calendar events"}), 500

