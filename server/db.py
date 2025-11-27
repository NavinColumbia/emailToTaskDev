from __future__ import annotations
import os
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import create_engine, ForeignKey, UniqueConstraint, Integer
from sqlalchemy.orm import registry, mapped_column, Mapped, Session, sessionmaker, relationship
from sqlalchemy import JSON, BigInteger, Text, Boolean, TIMESTAMP
from sqlalchemy.exc import OperationalError
from pathlib import Path

# Use /tmp for Cloud Run (ephemeral) or allow override via env var
db_dir = Path(os.getenv("DB_DIR", "/tmp"))
db_path = db_dir / "taskflow.db"
DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
mapper_registry = registry()
Base = mapper_registry.generate_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    emails: Mapped[list["Email"]] = relationship("Email", back_populates="user")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="user")
    calendar_events: Mapped[list["CalendarEvent"]] = relationship("CalendarEvent", back_populates="user")
    settings: Mapped["UserSettings | None"] = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    categories: Mapped[list["UserCategory"]] = relationship("UserCategory", back_populates="user", cascade="all, delete-orphan")


class Email(Base):
    __tablename__ = "emails"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    gmail_message_id: Mapped[str] = mapped_column(Text, nullable=False)
    gmail_thread_id: Mapped[str | None] = mapped_column(Text)
    subject: Mapped[str | None] = mapped_column(Text)
    sender: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    snippet: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    first_processed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    last_processed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="emails")
    category_links: Mapped[list["EmailCategory"]] = relationship(
        "EmailCategory",
        back_populates="email",
        cascade="all, delete-orphan",
    )
    
    __table_args__ = (
        UniqueConstraint('user_id', 'gmail_message_id', name='uq_user_email_message'),
    )


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    email_id: Mapped[int] = mapped_column(Integer, ForeignKey("emails.id"), nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    provider_task_id: Mapped[str | None] = mapped_column(Text)
    provider_metadata: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
        # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tasks")
    email: Mapped["Email"] = relationship("Email")
    category_links: Mapped[list["TaskCategory"]] = relationship(
        "TaskCategory",
        back_populates="task",
        cascade="all, delete-orphan",
    )


class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    email_id: Mapped[int] = mapped_column(Integer, ForeignKey("emails.id"), nullable=False)
    google_event_id: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    start_datetime: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    end_datetime: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    html_link: Mapped[str | None] = mapped_column(Text)
    provider_metadata: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="calendar_events")
    email: Mapped["Email"] = relationship("Email")

class UserSettings(Base):
    __tablename__ = "user_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    provider: Mapped[str] = mapped_column(Text, nullable=False, default="google_tasks")
    max: Mapped[int | None] = mapped_column(Integer)
    window: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="settings")

class UserCategory(Base):
    """
    Per-user category (e.g. 'personal', 'work-sev2', etc.).
    Can later be mapped to Gmail labels or used only internally.
    """
    __tablename__ = "user_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)

    # Machine-friendly stable key (e.g. "work-sev2incidents")
    slug: Mapped[str] = mapped_column(Text, nullable=False)

    # Human-facing label (e.g. "Work – Sev2 Incidents")
    name: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional color or tag (frontend can ignore or use later)
    color: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="categories")
    email_links: Mapped[list["EmailCategory"]] = relationship(
        "EmailCategory",
        back_populates="category",
        cascade="all, delete-orphan",
    )
    task_links: Mapped[list["TaskCategory"]] = relationship(
        "TaskCategory",
        back_populates="category",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "slug", name="uq_user_category_slug"),
    )


class EmailCategory(Base):
    """
    Many-to-many link between Email and UserCategory.
    """
    __tablename__ = "email_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email_id: Mapped[int] = mapped_column(Integer, ForeignKey("emails.id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_categories.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    email: Mapped["Email"] = relationship("Email", back_populates="category_links")
    category: Mapped["UserCategory"] = relationship("UserCategory", back_populates="email_links")

    __table_args__ = (
        UniqueConstraint("email_id", "category_id", name="uq_email_category"),
    )


class TaskCategory(Base):
    """
    Many-to-many link between Task and UserCategory.
    """
    __tablename__ = "task_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_categories.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    task: Mapped["Task"] = relationship("Task", back_populates="category_links")
    category: Mapped["UserCategory"] = relationship("UserCategory", back_populates="task_links")

    __table_args__ = (
        UniqueConstraint("task_id", "category_id", name="uq_task_category"),
    )



def init_db():
    recreate_db = os.getenv("RECREATE_DB", "false").lower() == "true"
    
    if recreate_db:
        try:
            Base.metadata.drop_all(engine)
        except Exception as e:
            pass
    
    try:
        Base.metadata.create_all(engine, checkfirst=True)
    except OperationalError:
        pass

@contextmanager
def db_session() -> Session:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
