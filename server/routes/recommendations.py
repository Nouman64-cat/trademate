import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select
from database.database import engine
from models.recommendation import RecommendationResult
from models.interaction import UserInteraction, InteractionType
from models.conversation import Message
from schemas.recommendation import (
    RecommendationFeedback,
    DocumentRecommendationResponse,
    HSCodeRecommendationResponse,
    TariffOptimizationResponse,
    RouteRecommendationResponse
)
from security.security import decode_access_token
from services.hs_code_recommender import HSCodeRecommender
from services.tariff_optimizer import TariffOptimizer
from services.route_recommender import RouteRecommender

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/recommendations", tags=["recommendations"])
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


@router.get("/documents", response_model=DocumentRecommendationResponse)
def get_document_recommendations_endpoint(
    conversation_id: str = Query(..., description="Conversation ID for context"),
    top_k: int = Query(3, ge=1, le=10, description="Number of recommendations"),
    user_id: int = Depends(_get_current_user_id),
):
    """Get document recommendations based on conversation context."""
    try:
        with Session(engine) as session:
            # Get recent messages
            stmt = (
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(5)
            )
            messages = session.exec(stmt).all()

            if not messages:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

            conversation_context = [{"role": msg.role, "content": msg.content} for msg in reversed(messages)]

        from services.document_recommender import DocumentRecommender
        recommender = DocumentRecommender()
        recommendations, rec_id = recommender.recommend(user_id, conversation_id, conversation_context, top_k)

        return DocumentRecommendationResponse(recommendations=recommendations, recommendation_id=rec_id)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("━━━ [API] Document recommendations failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/hs-codes", response_model=HSCodeRecommendationResponse)
def get_hs_code_recommendations_endpoint(
    context_codes: list[str] = Query(None, description="Recently searched HS codes"),
    conversation_id: Optional[str] = Query(None),
    top_k: int = Query(10, ge=1, le=20),
    user_id: int = Depends(_get_current_user_id),
):
    """Get HS code recommendations based on search history."""
    try:
        recommender = HSCodeRecommender()
        recommendations, rec_id = recommender.recommend(user_id, context_codes or [], conversation_id, top_k)
        return HSCodeRecommendationResponse(recommendations=recommendations, recommendation_id=rec_id)
    except Exception as exc:
        logger.error("━━━ [API] HS code recommendations failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/tariff-optimization", response_model=TariffOptimizationResponse)
def get_tariff_optimization_endpoint(
    hs_code: str = Query(...),
    cargo_value_usd: float = Query(..., ge=0),
    source: str = Query("PK", pattern="^(PK|US)$"),
    max_alternatives: int = Query(5, ge=1, le=10),
    conversation_id: Optional[str] = Query(None),
    user_id: int = Depends(_get_current_user_id),
):
    """Find alternative HS codes with lower tariff rates."""
    try:
        optimizer = TariffOptimizer()
        alternatives, rec_id = optimizer.find_alternatives(hs_code, cargo_value_usd, user_id, conversation_id, source, max_alternatives)
        return TariffOptimizationResponse(alternatives=alternatives, recommendation_id=rec_id)
    except Exception as exc:
        logger.error("━━━ [API] Tariff optimization failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/routes", response_model=RouteRecommendationResponse)
def get_route_recommendations_endpoint(
    origin_city: str = Query(...),
    destination_city: str = Query(...),
    cargo_type: str = Query(...),
    cargo_value_usd: float = Query(..., ge=0),
    hs_code: Optional[str] = Query(None),
    cargo_volume_cbm: Optional[float] = Query(None, ge=0),
    cargo_weight_kg: Optional[float] = Query(None, ge=0),
    container_count: int = Query(1, ge=1),
    conversation_id: Optional[str] = Query(None),
    top_k: int = Query(3, ge=1, le=10),
    user_id: int = Depends(_get_current_user_id),
):
    """Get personalized route recommendations."""
    try:
        recommender = RouteRecommender()
        recommendations, rec_id = recommender.recommend_routes(
            user_id, origin_city, destination_city, cargo_type, cargo_value_usd,
            conversation_id, hs_code, cargo_volume_cbm, cargo_weight_kg, container_count, top_k
        )
        return RouteRecommendationResponse(routes=recommendations, recommendation_id=rec_id)
    except Exception as exc:
        logger.error("━━━ [API] Route recommendations failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/{recommendation_id}/feedback")
def submit_feedback(
    recommendation_id: int,
    body: RecommendationFeedback,
    user_id: int = Depends(_get_current_user_id),
):
    """Submit user feedback for a recommendation."""
    with Session(engine) as session:
        rec = session.get(RecommendationResult, recommendation_id)
        if not rec or rec.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")

        # Update recommendation result with feedback
        rec.selected_item_id = body.selected_item_id
        rec.selection_rank = body.selection_rank
        rec.was_helpful = body.was_helpful

        session.add(rec)

        # Log as an interaction for ML training
        interaction = UserInteraction(
            user_id=user_id,
            interaction_type=InteractionType.recommendation_click,
            conversation_id=rec.conversation_id,
            message_id=rec.message_id,
            document_id=body.selected_item_id if rec.recommendation_type == "document" else None,
            hs_code=body.selected_item_id if rec.recommendation_type == "hs_code" else None,
            route_id=body.selected_item_id if rec.recommendation_type == "route" else None,
            rank_position=body.selection_rank,
            metadata_json=f'{{"recommendation_id": {recommendation_id}, "was_helpful": {str(body.was_helpful).lower()}}}'
        )
        session.add(interaction)

        session.commit()
        logger.info(f"━━━ [FEEDBACK] Logged for recommendation {recommendation_id} from user {user_id}")

    return {"status": "success"}
