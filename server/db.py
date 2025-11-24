from __future__ import annotations
import os
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import create_engine, ForeignKey, UniqueConstraint, Integer
from sqlalchemy.orm import registry, mapped_column, Mapped, Session, sessionmaker, relationship
from sqlalchemy import JSON, BigInteger, Text, Boolean, TIMESTAMP
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
    user: Mapped["User"] = relationship("User", back_populates="tasks")
    email: Mapped["Email"] = relationship("Email")

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

def init_db():
    import logging
    logger = logging.getLogger(__name__)
    
    recreate_db = os.getenv("RECREATE_DB", "false").lower() == "true"
    
    if recreate_db:
        logger.info("RECREATE_DB flag is set - dropping and recreating all tables")
        try:
            Base.metadata.drop_all(engine)
            logger.info("Dropped all existing tables")
        except Exception as e:
            logger.warning(f"Error dropping tables (may not exist): {e}")
    
    try:
        Base.metadata.create_all(engine, checkfirst=True)
        logger.info("Database initialization successful")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

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
