from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


def _uuid() -> str:
    return str(uuid.uuid4())


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: str = Field(
        default_factory=_uuid,
        primary_key=True,
        max_length=36,
    )
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    )
    title: Optional[str] = Field(default=None, max_length=255)
    share_token: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, unique=True, nullable=True, index=True),
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False,
        ),
    )

    __table_args__ = (
        Index("ix_conversations_user_id_updated_at", "user_id", "updated_at"),
    )


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: str = Field(
        sa_column=Column(
            Text,
            ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    role: str = Field(
        sa_column=Column(
            SAEnum("user", "assistant", name="message_role_enum"),
            nullable=False,
        )
    )
    content: str = Field(sa_column=Column(Text, nullable=False))

    # Tracks which tools the router selected and which DBs returned results.
    # Stored as JSON strings e.g. '["search_pakistan_hs_data"]'
    tools_used: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    sources_hit: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))

    # User-submitted 1–5 star rating for assistant messages (null = unrated).
    # Only assistant messages are rated; a CHECK constraint enforces the range.
    rating: Optional[int] = Field(default=None, sa_column=Column(Integer, nullable=True))

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False),
    )

    __table_args__ = (
        Index("ix_messages_conversation_id_created_at", "conversation_id", "created_at"),
        CheckConstraint("rating IS NULL OR rating BETWEEN 1 AND 5", name="ck_messages_rating_range"),
    )
