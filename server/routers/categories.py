from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, session, jsonify, request
from sqlalchemy import select

from server.utils import get_current_user
from server.db import db_session, UserCategory

categories_bp = Blueprint("categories", __name__)


@categories_bp.route("/categories", methods=["GET"])
def list_categories():
    """
    List all categories for the current user.
    This is read-only; used by the frontend to show/choose categories.
    """
    if "credentials" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = get_current_user()
    if not user:
        return jsonify({"error": "Could not determine user"}), 401

    with db_session() as s:
        stmt = (
            select(UserCategory)
            .where(UserCategory.user_id == user.id)
            .order_by(UserCategory.created_at.asc())
        )
        rows = s.execute(stmt).scalars().all()

        return jsonify(
            {
                "categories": [
                    {
                        "id": c.id,
                        "name": c.name,
                        "slug": c.slug,
                        "color": c.color,
                        "description": c.description,
                    }
                    for c in rows
                ]
            }
        )


@categories_bp.route("/categories", methods=["POST"])
def create_category():
    """
    Create a new category for the current user.

    Expected JSON body:
    {
      "name": "Work – Sev2 Incidents",
      "slug": "work-sev2incidents",   # optional
      "color": "#FF0000",             # optional
      "description": "For urgent Sev2 prod issues"  # optional
    }
    """
    if "credentials" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    user = get_current_user()
    if not user:
        return jsonify({"error": "Could not determine user"}), 401

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    slug = (data.get("slug") or "").strip()
    color = (data.get("color") or None) or None
    description = (data.get("description") or "").strip() or None

    if not name:
        return jsonify({"error": "Field 'name' is required"}), 400

    # Simple slug fallback if not supplied
    if not slug:
        slug = name.lower().replace(" ", "-")
    slug = slug[:64]

    now = datetime.now(timezone.utc)

    with db_session() as s:
        # Enforce uniqueness per user + slug
        stmt = (
            select(UserCategory)
            .where(UserCategory.user_id == user.id)
            .where(UserCategory.slug == slug)
        )
        existing = s.execute(stmt).scalar_one_or_none()
        if existing:
            return (
                jsonify(
                    {
                        "error": "Category with this slug already exists",
                        "category": {
                            "id": existing.id,
                            "name": existing.name,
                            "slug": existing.slug,
                            "color": existing.color,
                            "description": existing.description,
                        },
                    }
                ),
                409,
            )

        cat = UserCategory(
            user_id=user.id,
            name=name,
            slug=slug,
            color=color,
            description=description,
            created_at=now,
            updated_at=now,
        )
        s.add(cat)
        s.flush()  # get cat.id

        return (
            jsonify(
                {
                    "id": cat.id,
                    "name": cat.name,
                    "slug": cat.slug,
                    "color": cat.color,
                    "description": cat.description,
                }
            ),
            201,
        )
