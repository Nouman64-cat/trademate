"""
routes/chat.py — authenticated streaming chat endpoint.

POST /v1/chat
─────────────
• Requires a valid JWT (Bearer token).  Uses the same _get_current_user_id
  dependency pattern as routes/auth.py so there is one canonical place to
  change auth logic.
• Accepts a JSON body matching ChatRequest (message + optional history +
  optional conversation_id).
• Returns a Server-Sent Events (SSE) stream so the frontend can render tokens
  as they arrive, exactly matching the simulateStream() contract already in
  the Next.js chatStore.

SSE event format
────────────────
  data: {"type": "token",        "content": "<chunk>", "conversation_id": "…"}\n\n
  data: {"type": "done",         "conversation_id": "…"}\n\n
  data: {"type": "error",        "detail": "<msg>",    "conversation_id": "…"}\n\n
"""

import json
import logging
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langchain_core.messages import AIMessageChunk, HumanMessage

from agent.graph import get_graph
from schemas.chat import ChatRequest
from security.security import decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["chat"])
_bearer = HTTPBearer()


# ── auth dependency (mirrors auth.py) ─────────────────────────────────────────


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


# ── SSE streaming helper ───────────────────────────────────────────────────────


def _sse(data: dict) -> str:
    """Encode a dict as a single SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


async def _stream_agent(
    message: str,
    history: list,
    conversation_id: str,
) -> AsyncGenerator[str, None]:
    """
    Run the LangGraph agent and yield SSE-formatted token chunks.

    LangGraph stream_mode="messages" yields (AIMessageChunk, metadata) tuples
    during the generate node.  We forward only the content string of each
    chunk so the frontend receives one SSE event per token.
    """
    try:
        graph = get_graph()

        # Build the full message list: history turns first, then the new user message.
        messages = []
        for turn in history:
            if turn.role == "user":
                messages.append(HumanMessage(content=turn.content))
            else:
                # Import AIMessage lazily to keep the top-level imports minimal.
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=turn.content))

        messages.append(HumanMessage(content=message))

        initial_state = {"messages": messages, "context": ""}

        async for chunk, metadata in graph.astream(
            initial_state,
            stream_mode="messages",
        ):
            # Only forward AI token chunks that carry text content.
            if (
                isinstance(chunk, AIMessageChunk)
                and chunk.content
                and isinstance(chunk.content, str)
            ):
                yield _sse(
                    {
                        "type": "token",
                        "content": chunk.content,
                        "conversation_id": conversation_id,
                    }
                )

        yield _sse({"type": "done", "conversation_id": conversation_id})

    except Exception as exc:
        logger.exception("Agent error for conversation %s", conversation_id)
        yield _sse(
            {
                "type": "error",
                "detail": str(exc),
                "conversation_id": conversation_id,
            }
        )


# ── route ──────────────────────────────────────────────────────────────────────


@router.post("/chat")
async def chat(
    body: ChatRequest,
    user_id: int = Depends(_get_current_user_id),
):
    """
    Authenticated streaming chat endpoint.

    The JWT is validated before any LLM work starts.  If the token is missing
    or expired FastAPI returns 401 before the streaming response opens.
    """
    conversation_id = body.conversation_id or str(uuid.uuid4())
    history = body.history or []

    logger.info(
        "Chat request — user_id=%d  conversation_id=%s  history_turns=%d",
        user_id,
        conversation_id,
        len(history),
    )

    return StreamingResponse(
        _stream_agent(body.message, history, conversation_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",   # disable nginx proxy buffering
        },
    )
