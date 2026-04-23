import json
import logging
from typing import Optional, Any
from sqlmodel import Session
from database.database import engine
from models.interaction import UserInteraction, InteractionType

logger = logging.getLogger(__name__)

def log_interaction(
    user_id: int,
    interaction_type: InteractionType,
    conversation_id: Optional[str] = None,
    message_id: Optional[int] = None,
    hs_code: Optional[str] = None,
    route_id: Optional[str] = None,
    document_id: Optional[str] = None,
    query: Optional[str] = None,
    similarity_score: Optional[float] = None,
    rank_position: Optional[int] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """Log a user interaction to the database."""
    try:
        with Session(engine) as session:
            interaction = UserInteraction(
                user_id=user_id,
                interaction_type=interaction_type,
                conversation_id=conversation_id,
                message_id=message_id,
                hs_code=hs_code,
                route_id=route_id,
                document_id=document_id,
                query=query,
                similarity_score=similarity_score,
                rank_position=rank_position,
                metadata_json=json.dumps(metadata) if metadata else None,
            )
            session.add(interaction)
            session.commit()
            logger.info(f"━━━ [INTERACTION] Logged: {interaction_type.value} for user {user_id}")
    except Exception as exc:
        logger.warning(f"━━━ [INTERACTION] Failed to log interaction: {exc}")
