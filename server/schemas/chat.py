from typing import List, Optional

from pydantic import BaseModel, Field


class ChatHistoryMessage(BaseModel):
    """A single turn in the conversation history sent from the frontend."""

    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    """
    Body sent by the client to POST /v1/chat.

    message         — the user's latest message.
    conversation_id — opaque ID managed by the frontend; echoed back in every
                      SSE event so the client can route chunks correctly.
    history         — prior turns in this conversation (oldest first).
                      Sending history enables multi-turn context awareness.
    """

    message: str
    conversation_id: Optional[str] = None
    history: Optional[List[ChatHistoryMessage]] = []
