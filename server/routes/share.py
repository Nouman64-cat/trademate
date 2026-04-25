"""
routes/share.py — shareable conversation link endpoints.

POST /v1/conversations/{id}/share  → generate (or return existing) share token (auth required)
GET  /v1/shared/{token}            → fetch shared conversation messages (no auth required)
"""

import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlmodel import Session, select

from database.database import engine
from models.conversation import Conversation, Message
from security.security import decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["share"])
_bearer = HTTPBearer()


def _get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> int:
    payload = decode_access_token(credentials.credentials)
    try:
        return int(payload["id"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )


class ShareOut(BaseModel):
    share_token: str


class SharedMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: str


class SharedConversationOut(BaseModel):
    title: str | None
    messages: list[SharedMessageOut]


@router.post("/conversations/{conversation_id}/share", response_model=ShareOut)
def create_share_link(
    conversation_id: str,
    user_id: int = Depends(_get_current_user_id),
):
    """Generate a share token for a conversation. Idempotent — returns existing token if already set."""
    with Session(engine) as session:
        conv = session.get(Conversation, conversation_id)
        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        if conv.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        if not conv.share_token:
            conv.share_token = str(uuid.uuid4())
            session.add(conv)
            session.commit()
            session.refresh(conv)

        return ShareOut(share_token=conv.share_token)


@router.get("/shared/{token}", response_model=SharedConversationOut)
def get_shared_conversation(token: str):
    """Public endpoint — no auth required. Returns conversation messages for the given share token."""
    with Session(engine) as session:
        conv = session.exec(
            select(Conversation).where(Conversation.share_token == token)
        ).first()
        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared conversation not found")

        rows = session.exec(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.asc())
        ).all()

    logger.info("[DB] get_shared_conversation → token=%s  messages=%d", token, len(rows))
    return SharedConversationOut(
        title=conv.title,
        messages=[
            SharedMessageOut(
                id=r.id,
                role=r.role,
                content=r.content,
                created_at=r.created_at.isoformat(),
            )
            for r in rows
        ],
    )
