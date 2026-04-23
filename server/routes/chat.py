"""
routes/chat.py — authenticated streaming chat endpoint.

POST /v1/chat
─────────────
• Requires a valid JWT (Bearer token).
• Accepts { message, conversation_id }.
• Loads conversation history from DB (last 20 turns) — client no longer
  needs to send history.
• Persists every user message and assistant reply to the messages table.
• Returns a Server-Sent Events (SSE) stream.

SSE event format
────────────────
  data: {"type": "token",   "content": "<chunk>", "conversation_id": "…"}\n\n
  data: {"type": "done",    "conversation_id": "…"}\n\n
  data: {"type": "error",   "detail": "<msg>",    "conversation_id": "…"}\n\n
"""

import json
import logging
import os
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field as PydField
from sqlmodel import Session, select

from agent.bot import get_bot, route_widget_ctx, request_ctx
from database.database import engine
from models.conversation import Conversation, Message
from schemas.chat import ChatRequest
from security.security import decode_access_token

logger = logging.getLogger(__name__)

router  = APIRouter(prefix="/v1", tags=["chat"])
_bearer = HTTPBearer()

# Maximum number of previous turns loaded from DB as context
_HISTORY_TURNS = 20


# ── auth dependency ────────────────────────────────────────────────────────────


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


# ── DB helpers ─────────────────────────────────────────────────────────────────


def _get_or_create_conversation(
    session: Session,
    conversation_id: str,
    user_id: int,
    first_message: str,
) -> Conversation:
    """Return existing conversation or create a new one."""
    conv = session.get(Conversation, conversation_id)
    if conv:
        if conv.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this conversation.",
            )
        return conv

    # Auto-title from first 80 chars of the opening message
    title = first_message.strip()[:80]
    conv  = Conversation(id=conversation_id, user_id=user_id, title=title)
    session.add(conv)
    session.commit()
    session.refresh(conv)
    logger.info("━━━ [DB] New conversation created: %s  title=%r", conversation_id, title)
    return conv


def _load_history(session: Session, conversation_id: str) -> list:
    """Load the last _HISTORY_TURNS messages as LangChain message objects."""
    rows = session.exec(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(_HISTORY_TURNS)
    ).all()

    # Reverse so oldest-first order for the LLM
    rows = list(reversed(rows))

    messages = []
    for row in rows:
        if row.role == "user":
            messages.append(HumanMessage(content=row.content))
        else:
            messages.append(AIMessage(content=row.content))

    if rows:
        logger.info("━━━ [DB] Loaded %d history turn(s) for conversation %s", len(rows), conversation_id)
    return messages


def _save_message(
    session: Session,
    conversation_id: str,
    role: str,
    content: str,
    tools_used: list[str] | None = None,
    sources_hit: list[str] | None = None,
) -> int:
    """Persist a single message to the DB and return its generated id."""
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        tools_used=json.dumps(tools_used) if tools_used else None,
        sources_hit=json.dumps(sources_hit) if sources_hit else None,
    )
    session.add(msg)

    # Bump conversation updated_at so list endpoint sorts correctly
    conv = session.get(Conversation, conversation_id)
    if conv:
        from datetime import datetime
        conv.updated_at = datetime.utcnow()
        session.add(conv)

    session.commit()
    session.refresh(msg)
    return msg.id


# ── SSE helper ─────────────────────────────────────────────────────────────────


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


# ── Title generation ───────────────────────────────────────────────────────────

_title_llm: ChatOpenAI | None = None

def _get_title_llm() -> ChatOpenAI:
    global _title_llm
    if _title_llm is None:
        api_key = os.getenv("OPENAI_API_KEY")
        _title_llm = ChatOpenAI(model="gpt-5.4", temperature=0.3, streaming=False, openai_api_key=api_key)
    return _title_llm


async def _generate_title(user_message: str, assistant_reply: str) -> str:
    """Generate a short conversation title from the first exchange."""
    try:
        llm = _get_title_llm()
        response = llm.invoke([
            SystemMessage(content=(
                "Generate a very short title (3-6 words) for this conversation. "
                "Return ONLY the title text. No quotes, no punctuation at the end, no explanation."
            )),
            HumanMessage(content=f"User: {user_message[:300]}\nAssistant: {assistant_reply[:300]}"),
        ])
        title = response.content.strip()[:80]
        logger.info("━━━ [TITLE] Generated: %r", title)
        return title
    except Exception as exc:
        logger.warning("━━━ [TITLE] Generation failed: %s", exc)
        return user_message.strip()[:60]


# ── streaming agent runner ─────────────────────────────────────────────────────


async def _stream_agent(
    message: str,
    conversation_id: str,
    user_id: int,
) -> AsyncGenerator[str, None]:
    try:
        with Session(engine) as session:
            # Ensure conversation exists
            _get_or_create_conversation(session, conversation_id, user_id, message)

            # Load history from DB
            history_messages = _load_history(session, conversation_id)

            # First message in this conversation → title needs to be generated
            is_first_message = len(history_messages) == 0

            # Save the incoming user message immediately
            _save_message(session, conversation_id, "user", message)

        graph = get_bot()

        # Build message list: history + new user message
        messages = history_messages + [HumanMessage(content=message)]
        initial_state = {"messages": messages}

        tools_called: list[str] = []
        reply_chunks: list[str] = []

        # Per-request widget store: evaluate_shipping_routes tool appends here
        widget_store: list = []
        token = route_widget_ctx.set(widget_store)
        
        ctx_token = request_ctx.set({
            "user_id": user_id,
            "conversation_id": conversation_id,
        })

        async for chunk, metadata in graph.astream(initial_state, stream_mode="messages"):
            # Track tool calls for logging + persistence
            node = metadata.get("langgraph_node", "")
            if node == "tools" and hasattr(chunk, "name") and chunk.name:
                if chunk.name not in tools_called:
                    tools_called.append(chunk.name)
                    logger.info("━━━ [TOOL CALL] → %s", chunk.name)

            # Forward AI token chunks to client
            if (
                isinstance(chunk, AIMessageChunk)
                and chunk.content
                and isinstance(chunk.content, str)
            ):
                reply_chunks.append(chunk.content)
                yield _sse({
                    "type": "token",
                    "content": chunk.content,
                    "conversation_id": conversation_id,
                })

        # Restore context vars
        route_widget_ctx.reset(token)
        request_ctx.reset(ctx_token)

        # Persist the full assistant reply
        full_reply = "".join(reply_chunks)
        assistant_message_id: int | None = None
        if full_reply:
            with Session(engine) as session:
                assistant_message_id = _save_message(
                    session,
                    conversation_id,
                    "assistant",
                    full_reply,
                    tools_used=tools_called or None,
                    sources_hit=tools_called or None,
                )

        if tools_called:
            logger.info("━━━ [DONE]    Sources used: %s", ", ".join(tools_called))
        else:
            logger.warning(
                "━━━ [DONE]    ⚠ No tools called — LLM answered from training knowledge only."
            )

        # Tell the client the DB id of the assistant message so it can wire up
        # rating submission (PATCH /v1/messages/{id}/rating).
        if assistant_message_id is not None:
            yield _sse({
                "type": "message_saved",
                "message_id": assistant_message_id,
                "conversation_id": conversation_id,
            })

            # ── Recommendation System Integration (Phase 2) ──────────────────────
            # Generate personalized recommendations based on conversation context

            # 1. Document Recommendations (if conversation about compliance/regulations)
            try:
                from services.document_recommender import DocumentRecommender

                # Build conversation context for document recommender
                with Session(engine) as session:
                    recent_msgs = session.exec(
                        select(Message)
                        .where(Message.conversation_id == conversation_id)
                        .order_by(Message.created_at.desc())
                        .limit(5)
                    ).all()

                    conversation_context = [
                        {"role": msg.role, "content": msg.content}
                        for msg in reversed(recent_msgs)
                    ]

                doc_recommender = DocumentRecommender()
                doc_recs, doc_rec_id = doc_recommender.recommend(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    conversation_context=conversation_context,
                    top_k=3
                )

                if doc_recs:
                    yield _sse({
                        "type": "document_recommendations",
                        "recommendations": [r.model_dump() for r in doc_recs],
                        "recommendation_id": doc_rec_id,
                        "conversation_id": conversation_id,
                    })
                    logger.info("━━━ [REC] Sent %d document recommendations", len(doc_recs))

            except Exception as exc:
                logger.warning("━━━ [REC] Document recommendations failed: %s", exc)

            # 2. HS Code Recommendations (if user searched HS codes)
            if any(tool in tools_called for tool in ["search_pakistan_hs_data", "search_us_hs_data"]):
                try:
                    from services.hs_code_recommender import HSCodeRecommender

                    # Extract recently searched HS codes from interaction history
                    context_codes: list[str] = []
                    with Session(engine) as session:
                        from models.interaction import UserInteraction, InteractionType
                        recent_searches = session.exec(
                            select(UserInteraction.hs_code)
                            .where(
                                UserInteraction.user_id == user_id,
                                UserInteraction.interaction_type == InteractionType.search_hs_code,
                                UserInteraction.hs_code.is_not(None)
                            )
                            .order_by(UserInteraction.created_at.desc())
                            .limit(5)
                        ).all()
                        context_codes = [code for code in recent_searches if code]

                    hs_recommender = HSCodeRecommender()
                    hs_recs, hs_rec_id = hs_recommender.recommend(
                        user_id=user_id,
                        context_hs_codes=context_codes,
                        conversation_id=conversation_id,
                        top_k=5
                    )

                    if hs_recs:
                        yield _sse({
                            "type": "hs_code_recommendations",
                            "recommendations": [r.model_dump() for r in hs_recs],
                            "recommendation_id": hs_rec_id,
                            "conversation_id": conversation_id,
                        })
                        logger.info("━━━ [REC] Sent %d HS code recommendations", len(hs_recs))

                except Exception as exc:
                    logger.warning("━━━ [REC] HS code recommendations failed: %s", exc)

            # 3. Tariff Optimization (if specific HS code discussed and cargo value mentioned)
            # Extract HS code from recent interactions
            try:
                from services.tariff_optimizer import TariffOptimizer
                import re

                # Try to extract HS code from message (regex search first)
                from agent.bot import _PK_CODE_RE, _US_CODE_RE
                
                current_hs_code: str | None = None
                cargo_value: float | None = None
                
                # Check for HS codes in message, avoiding numbers with commas (like 10,000)
                hs_matches = re.findall(r'\b\d{4}(?:\.\d{2})+\b|\b\d{6,12}\b', message)
                if hs_matches:
                    current_hs_code = hs_matches[0].replace('.', '')
                else:
                    # Extract from recent interactions if no match in message
                    with Session(engine) as session:
                        from models.interaction import UserInteraction, InteractionType
                        recent_hs = session.exec(
                            select(UserInteraction)
                            .where(
                                UserInteraction.user_id == user_id,
                                UserInteraction.conversation_id == conversation_id,
                                UserInteraction.interaction_type.in_([
                                    InteractionType.search_hs_code,
                                    InteractionType.view_hs_code
                                ])
                            )
                            .order_by(UserInteraction.created_at.desc())
                            .limit(1)
                        ).first()

                        if recent_hs and recent_hs.hs_code:
                            current_hs_code = recent_hs.hs_code

                # Try to extract cargo value from message (simple regex)
                # Look for patterns like "$1000", "1000 USD", "value of 1000"
                value_patterns = [
                    r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $1,000.00
                    r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|usd|dollars?)',  # 1000 USD
                    r'value\s+of\s+(\d+(?:,\d{3})*(?:\.\d{2})?)',  # value of 1000
                    r'value\s+of\s+\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', # value of $1000
                ]
                for pattern in value_patterns:
                    match = re.search(pattern, message, re.IGNORECASE)
                    if match:
                        try:
                            cargo_value = float(match.group(1).replace(',', ''))
                            break
                        except ValueError:
                            pass

                # Only recommend tariff alternatives if we have both HS code and value
                if current_hs_code and cargo_value and cargo_value > 0:
                    optimizer = TariffOptimizer()
                    alternatives, tariff_rec_id = optimizer.find_alternatives(
                        hs_code=current_hs_code,
                        cargo_value_usd=cargo_value,
                        user_id=user_id,
                        conversation_id=conversation_id,
                        source="PK",
                        max_alternatives=3
                    )

                    if alternatives:
                        yield _sse({
                            "type": "tariff_alternatives",
                            "alternatives": [a.model_dump() for a in alternatives],
                            "recommendation_id": tariff_rec_id,
                            "conversation_id": conversation_id,
                        })
                        logger.info("━━━ [REC] Sent %d tariff alternatives", len(alternatives))

            except Exception as exc:
                logger.warning("━━━ [REC] Tariff optimization failed: %s", exc)

            # 4. Route Recommendations (if route evaluation tool was called)
            if "evaluate_shipping_routes" in tools_called and widget_store:
                try:
                    from services.route_recommender import RouteRecommender

                    # Extract route parameters from the widget data
                    # widget_store contains route evaluation results
                    if widget_store and len(widget_store) > 0:
                        widget_data = widget_store[0]  # Use first widget data

                        # Extract parameters from widget metadata
                        origin = widget_data.get("origin_city", "")
                        destination = widget_data.get("destination_city", "")
                        cargo_type = widget_data.get("cargo_type", "general")
                        cargo_value = widget_data.get("cargo_value_usd", 10000)
                        cost_weight = widget_data.get("cost_weight", 0.5)

                        if origin and destination:
                            route_recommender = RouteRecommender()
                            route_recs, route_rec_id = route_recommender.recommend_routes(
                                user_id=user_id,
                                origin_city=origin,
                                destination_city=destination,
                                cargo_type=cargo_type,
                                cargo_value_usd=cargo_value,
                                cost_weight=cost_weight,
                                conversation_id=conversation_id,
                                top_k=3
                            )

                            if route_recs:
                                yield _sse({
                                    "type": "route_recommendations",
                                    "routes": [r.model_dump() for r in route_recs],
                                    "recommendation_id": route_rec_id,
                                    "conversation_id": conversation_id,
                                })
                                logger.info("━━━ [REC] Sent %d route recommendations", len(route_recs))

                except Exception as exc:
                    logger.warning("━━━ [REC] Route recommendations failed: %s", exc)

        yield _sse({"type": "done", "conversation_id": conversation_id})

        # If the route tool was called, emit one widget event per result.
        # The tool may be called multiple times (e.g. air vs sea comparison,
        # or two-destination query) — all results must be sent.
        for i, widget_data in enumerate(widget_store):
            yield _sse({
                "type": "widget",
                "widget_type": "route_evaluation",
                "data": widget_data,
                "conversation_id": conversation_id,
            })
        if widget_store:
            logger.info(
                "━━━ [WIDGET] Sent %d route_evaluation widget(s) for conv %s",
                len(widget_store), conversation_id,
            )

        # Generate and stream title only for the first message
        if is_first_message and full_reply:
            title = await _generate_title(message, full_reply)
            # Persist title to DB
            with Session(engine) as session:
                conv = session.get(Conversation, conversation_id)
                if conv:
                    conv.title = title
                    session.add(conv)
                    session.commit()
            # Send title event to frontend
            yield _sse({"type": "title", "title": title, "conversation_id": conversation_id})

    except Exception as exc:
        logger.exception("Agent error for conversation %s", conversation_id)
        yield _sse({"type": "error", "detail": str(exc), "conversation_id": conversation_id})


# ── route ──────────────────────────────────────────────────────────────────────


class RatingRequest(BaseModel):
    rating: int = PydField(ge=1, le=5, description="Star rating from 1 (worst) to 5 (best).")


class RatingResponse(BaseModel):
    message_id: int
    rating: int


@router.patch("/messages/{message_id}/rating", response_model=RatingResponse)
def rate_message(
    message_id: int,
    body: RatingRequest,
    user_id: int = Depends(_get_current_user_id),
) -> RatingResponse:
    """Submit or update a 1–5 star rating on an assistant message.

    Only the conversation owner may rate, and only assistant messages are
    ratable (user's own messages return 400).
    """
    with Session(engine) as session:
        msg = session.get(Message, message_id)
        if msg is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

        conv = session.get(Conversation, msg.conversation_id)
        if conv is None or conv.user_id != user_id:
            # Same response for both to avoid leaking message existence
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        if msg.role != "assistant":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only assistant messages can be rated.",
            )

        msg.rating = body.rating
        session.add(msg)
        session.commit()
        session.refresh(msg)

    logger.info("[RATING] user_id=%d  message_id=%d  rating=%d", user_id, message_id, body.rating)
    return RatingResponse(message_id=msg.id, rating=msg.rating)


@router.post("/chat")
async def chat(
    body: ChatRequest,
    user_id: int = Depends(_get_current_user_id),
):
    conversation_id = body.conversation_id or str(uuid.uuid4())

    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("━━━ [REQUEST] user_id=%d  conv=%s", user_id, conversation_id)
    logger.info("━━━ [QUERY]   %r", body.message[:200])

    return StreamingResponse(
        _stream_agent(body.message, conversation_id, user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
