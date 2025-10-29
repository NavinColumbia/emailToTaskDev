from __future__ import annotations
import os
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import registry, mapped_column, Mapped, Session, sessionmaker
from sqlalchemy import JSON, BigInteger, Text, Boolean, TIMESTAMP

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
mapper_registry = registry()
Base = mapper_registry.generate_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

class Email(Base):
    __tablename__ = "emails"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    gmail_message_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
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

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    provider_task_id: Mapped[str | None] = mapped_column(Text)
    provider_metadata: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

def init_db():
    Base.metadata.create_all(engine)

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
