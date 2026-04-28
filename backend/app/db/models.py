from __future__ import annotations

import enum
from datetime import datetime, date

from sqlalchemy import Text

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Provider(str, enum.Enum):
    gmail = "gmail"
    yahoo = "yahoo"


class AnalysisStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, index=True)
    provider: Mapped[Provider] = mapped_column(Enum(Provider))
    email: Mapped[str] = mapped_column(String, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(back_populates="account")
    processed_ranges: Mapped[list["ProcessedRange"]] = relationship(back_populates="account")
    messages: Mapped[list["EmailMessage"]] = relationship(back_populates="account")

    __table_args__ = (UniqueConstraint("username", "provider", "email", name="uq_account_identity"),)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("email_accounts.id"), index=True)

    start_date: Mapped[date] = mapped_column(Date)
    end_date_exclusive: Mapped[date] = mapped_column(Date)

    status: Mapped[AnalysisStatus] = mapped_column(Enum(AnalysisStatus), default=AnalysisStatus.pending, index=True)
    emails_processed: Mapped[int] = mapped_column(Integer, default=0)
    total_emails: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    inbox_only: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    account: Mapped["EmailAccount"] = relationship(back_populates="analysis_runs")
    messages: Mapped[list["EmailMessage"]] = relationship(back_populates="analysis_run")


class EmailMessage(Base):
    __tablename__ = "email_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("email_accounts.id"), index=True)
    analysis_run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"), index=True, nullable=True)

    # Deterministic per account; later this becomes provider message id.
    external_id: Mapped[str] = mapped_column(String, index=True)

    received_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    sender_email: Mapped[str] = mapped_column(String, index=True)
    sender_name: Mapped[str | None] = mapped_column(String, nullable=True)
    subject: Mapped[str] = mapped_column(String)

    # JSON object of selected RFC822 headers (lowercase keys), for debugging / sender attribution.
    header_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped[str] = mapped_column(String, index=True)

    account: Mapped["EmailAccount"] = relationship(back_populates="messages")
    analysis_run: Mapped["AnalysisRun"] = relationship(back_populates="messages")

    __table_args__ = (
        UniqueConstraint("account_id", "external_id", name="uq_message_external_id"),
    )


class ProcessedRange(Base):
    __tablename__ = "processed_ranges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("email_accounts.id"), index=True)
    analysis_run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"), index=True, nullable=True)

    start_date: Mapped[date] = mapped_column(Date)
    end_date_exclusive: Mapped[date] = mapped_column(Date)
    emails_count: Mapped[int] = mapped_column(Integer, default=0)
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    account: Mapped["EmailAccount"] = relationship(back_populates="processed_ranges")

    __table_args__ = (
        UniqueConstraint("account_id", "start_date", "end_date_exclusive", name="uq_processed_range"),
    )


class OAuthProvider(str, enum.Enum):
    gmail = "gmail"
    yahoo = "yahoo"


class OAuthState(Base):
    __tablename__ = "oauth_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[OAuthProvider] = mapped_column(Enum(OAuthProvider), index=True)
    state: Mapped[str] = mapped_column(String, unique=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("email_accounts.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class OAuthCredential(Base):
    __tablename__ = "oauth_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[OAuthProvider] = mapped_column(Enum(OAuthProvider), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("email_accounts.id"), index=True)

    access_token_enc: Mapped[str] = mapped_column(Text)
    refresh_token_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_type: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("provider", "account_id", name="uq_oauth_credential_provider_account"),
    )

