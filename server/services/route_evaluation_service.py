import json
import logging
from typing import Optional
from sqlmodel import Session
from database.database import engine
from models.route_evaluation_history import RouteEvaluationHistory

logger = logging.getLogger(__name__)

def log_route_evaluation(
    user_id: int,
    origin_city: str,
    destination_city: str,
    cargo_type: str,
    cargo_value_usd: float,
    hs_code: Optional[str],
    cargo_volume_cbm: Optional[float],
    cargo_weight_kg: Optional[float],
    container_count: int,
    cost_weight: float,
    routes_count: int,
    cheapest_route_id: str,
    fastest_route_id: str,
    balanced_route_id: str,
    full_response: dict,
    conversation_id: Optional[str] = None,
    message_id: Optional[int] = None,
    selected_route_id: Optional[str] = None,
) -> None:
    """Log a route evaluation request and response to the database."""
    try:
        with Session(engine) as session:
            history = RouteEvaluationHistory(
                user_id=user_id,
                conversation_id=conversation_id,
                message_id=message_id,
                origin_city=origin_city,
                destination_city=destination_city,
                cargo_type=cargo_type,
                cargo_value_usd=cargo_value_usd,
                hs_code=hs_code,
                cargo_volume_cbm=cargo_volume_cbm,
                cargo_weight_kg=cargo_weight_kg,
                container_count=container_count,
                cost_weight=cost_weight,
                routes_count=routes_count,
                cheapest_route_id=cheapest_route_id,
                fastest_route_id=fastest_route_id,
                balanced_route_id=balanced_route_id,
                selected_route_id=selected_route_id,
                full_response_json=json.dumps(full_response),
            )
            session.add(history)
            session.commit()
            logger.info(f"━━━ [ROUTE_EVAL] Logged: {origin_city}→{destination_city} ({cargo_type}) for user {user_id}")
    except Exception as exc:
        logger.warning(f"━━━ [ROUTE_EVAL] Failed to log route evaluation: {exc}")
