from flask import Blueprint, session, jsonify, request
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateutil_parser
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from server.utils import get_current_user, get_calendar_service, require_auth
from server.db import db_session, CalendarEvent, Email
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

calendar_bp = Blueprint('calendar', __name__)

@calendar_bp.route("/calendar-events/all")
@require_auth
def api_all_calendar_events():

    user = get_current_user()
    if not user:
        return jsonify({"error": "Could not determine user"}), 401

    user_id = user.id

    # Get optional query parameters
    category = request.values.get("category")
    sort = request.values.get("sort")

    try:
        with db_session() as s:
            stmt = (
                select(CalendarEvent, Email)
                .join(Email, Email.id == CalendarEvent.email_id)
                .where(CalendarEvent.user_id == user_id)
                .where(Email.user_id == user_id)
            )
            
            # Apply category filter if provided
            if category:
                stmt = stmt.where(CalendarEvent.category == category)
            
            # Apply sorting
            if sort == "category":
                # Order by category ascending, then by start_datetime (or created_at) descending
                # Events with start_datetime will be sorted by start_datetime, 
                # events without will use created_at as the secondary sort
                stmt = stmt.order_by(
                    CalendarEvent.category.asc(),
                    CalendarEvent.start_datetime.desc().nulls_last(),
                    CalendarEvent.created_at.desc()
                )
            else:
                stmt = stmt.order_by(CalendarEvent.created_at.desc())
            
            stmt = stmt.limit(200)
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
                    "status": ce.status or "created",
                    "category": ce.category,
                })
        return jsonify({"events": items, "total": len(items)})
    except Exception as e:
        return jsonify({"error": "Failed to fetch calendar events"}), 500


@calendar_bp.route("/calendar-events", methods=["DELETE"])
@require_auth
def delete_calendar_events():
    """Delete multiple calendar events from Google Calendar and the database."""

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


def resolve_client_timezone(timezone_name: str | None):
    if not timezone_name:
        return timezone.utc
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        logger.warning("Unknown timezone '%s', defaulting to UTC", timezone_name)
        return timezone.utc


def parse_datetime_with_timezone(value: str | None, tzinfo):
    if not value:
        return None
    try:
        dt = dateutil_parser.isoparse(value)
    except Exception:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tzinfo)
    return dt


def timezone_name_from_dt(dt: datetime):
    tz = dt.tzinfo
    if isinstance(tz, ZoneInfo):
        return tz.key
    if tz:
        name = getattr(tz, "zone", None)
        if name:
            return name
        return tz.tzname(None) or "UTC"
    return "UTC"


def create_google_calendar_event(meeting: dict, client_timezone: str | None):
    """
    Create a Google Calendar event for a meeting.
    Use the client's timezone to interpret naive meeting times so the
    wall-clock time remains consistent.
    """
    calendar_service = get_calendar_service()
    if not calendar_service:
        return None

    raw_start = meeting.get("start_datetime")
    raw_end = meeting.get("end_datetime")
    user_tz = resolve_client_timezone(client_timezone)
    now_utc = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    start_obj = parse_datetime_with_timezone(raw_start, user_tz)
    if start_obj is None:
        start_obj = now_utc.astimezone(user_tz)
    else:
        if start_obj.tzinfo is None:
            start_obj = start_obj.replace(tzinfo=user_tz)

    start_obj_utc = start_obj.astimezone(timezone.utc)
    if start_obj_utc < now_utc:
        start_obj = now_utc.astimezone(start_obj.tzinfo or user_tz)

    end_obj = parse_datetime_with_timezone(raw_end, user_tz)
    if end_obj:
        if end_obj.tzinfo is None:
            end_obj = end_obj.replace(tzinfo=user_tz)
        end_obj = end_obj.astimezone(start_obj.tzinfo or user_tz)
        if end_obj <= start_obj:
            end_obj = start_obj + timedelta(hours=1)
    else:
        end_obj = start_obj + timedelta(hours=1)

    start_dt = start_obj.isoformat()
    end_dt = end_obj.isoformat()
    event_timezone = timezone_name_from_dt(start_obj)

    event = {
        "summary": meeting.get("summary") or "Meeting",
        "location": meeting.get("location"),
        "description": meeting.get("summary"),
        "start": {"dateTime": start_dt, "timeZone": event_timezone},
        "end": {"dateTime": end_dt, "timeZone": event_timezone},
        "attendees": [{"email": p} for p in meeting.get("participants", []) if p],
    }

    try:
        created_event = calendar_service.events().insert(calendarId="primary", body=event).execute()
        return created_event
    except Exception as e:
        logger.error(
            f"Calendar event creation FAILED - Summary: '{event.get('summary', 'N/A')}' | "
            f"Error: {str(e)}"
        )
        return None


@calendar_bp.route("/calendar-events/confirm", methods=["POST"])
@require_auth
def confirm_calendar_events():
    """Confirm and create pending calendar events in Google Calendar."""
    
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
        if not calendar_service:
            return jsonify({"error": "Not authenticated for Google Calendar"}), 401

        confirmed_count = 0
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
                    
                    if calendar_event.status != "pending":
                        errors.append(f"Event {event_id} is not pending (status: {calendar_event.status})")
                        continue

                    # Get event metadata
                    metadata = calendar_event.provider_metadata or {}
                    client_timezone = metadata.get("client_timezone")
                    
                    # Create event in Google Calendar
                    try:
                        created_event = create_google_calendar_event(metadata, client_timezone)
                        if created_event:
                            calendar_event.google_event_id = created_event.get("id")
                            calendar_event.html_link = created_event.get("htmlLink")
                            
                            # Update datetime fields from created event
                            event_timezone_str = created_event.get("start", {}).get("timeZone")
                            event_tz = resolve_client_timezone(event_timezone_str) if event_timezone_str else timezone.utc
                            
                            if created_event.get("start", {}).get("dateTime"):
                                try:
                                    parsed_start = dateutil_parser.isoparse(created_event["start"]["dateTime"])
                                    if parsed_start.tzinfo is None:
                                        parsed_start = parsed_start.replace(tzinfo=event_tz)
                                    calendar_event.start_datetime = parsed_start.astimezone(timezone.utc)
                                except Exception:
                                    pass
                            if created_event.get("end", {}).get("dateTime"):
                                try:
                                    parsed_end = dateutil_parser.isoparse(created_event["end"]["dateTime"])
                                    if parsed_end.tzinfo is None:
                                        parsed_end = parsed_end.replace(tzinfo=event_tz)
                                    calendar_event.end_datetime = parsed_end.astimezone(timezone.utc)
                                except Exception:
                                    pass
                            
                            calendar_event.provider_metadata = created_event
                            calendar_event.status = "created"
                            confirmed_count += 1
                        else:
                            errors.append(f"Error creating event {event_id} in Google Calendar")
                            continue
                    except Exception as e:
                        errors.append(f"Error creating event {event_id} in Google Calendar: {str(e)}")
                        continue
                        
                except ValueError:
                    errors.append(f"Invalid event ID: {event_id_str}")
                except Exception as e:
                    errors.append(f"Error confirming event {event_id_str}: {str(e)}")

        result = {"message": f"Confirmed {confirmed_count} event(s) successfully", "confirmed_count": confirmed_count}
        if errors:
            result["errors"] = errors
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "Failed to confirm calendar events"}), 500

