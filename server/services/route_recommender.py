"""
Route Recommender Service
─────────────────────────

Phase 1: Preference heuristics (Use UserPreference table + simple rules)
Phase 2: ML Preference Learning (LightGBM after 500+ route evaluations)

Algorithm (Phase 1):
1. Load user preferences from UserPreference table
2. Use typical_cost_weight if available, else default to 0.5
3. Call existing route_engine with predicted cost_weight
4. Boost preferred carriers
5. Add personalized explanations
"""

import json
import logging
from typing import Optional
from sqlmodel import Session, select
from database.database import engine
from models.recommendation import RecommendationResult, RecommendationType
from models.user_preference import UserPreference
from schemas.recommendation import RouteRecommendation
from services.route_engine import evaluate_routes
from schemas.routes import RouteEvaluationRequest

logger = logging.getLogger(__name__)


class RouteRecommender:
    """Recommends optimal shipping routes based on user preferences."""

    def __init__(self):
        self.ml_model = None  # Future: load LightGBM model from S3

    def recommend_routes(
        self,
        user_id: int,
        origin_city: str,
        destination_city: str,
        cargo_type: str,
        cargo_value_usd: float,
        conversation_id: Optional[str] = None,
        hs_code: Optional[str] = None,
        cargo_volume_cbm: Optional[float] = None,
        cargo_weight_kg: Optional[float] = None,
        container_count: int = 1,
        cost_weight: Optional[float] = None,
        top_k: int = 3
    ) -> tuple[list[RouteRecommendation], int]:
        """
        Generate personalized route recommendations.

        Args:
            user_id: User ID
            origin_city, destination_city, cargo_type: Route parameters
            cargo_value_usd: Cargo value
            conversation_id: Optional conversation ID
            hs_code: Optional HS code
            cargo_volume_cbm, cargo_weight_kg, container_count: Optional cargo details
            top_k: Number of routes to recommend

        Returns:
            Tuple of (recommendations, recommendation_id)
        """
        try:
            # 1. Load user preferences
            preferences = self._get_user_preferences(user_id)

            # 2. Determine cost_weight (0=fastest, 1=cheapest)
            if cost_weight is None:
                if preferences and preferences.typical_cost_weight is not None:
                    cost_weight = preferences.typical_cost_weight
                else:
                    cost_weight = 0.5  # Default: balanced
            
            reason_prefix = "Based on your preference for"
            if cost_weight > 0.7:
                reason_prefix += " cost-effective routes"
            elif cost_weight < 0.3:
                reason_prefix += " fast delivery"
            else:
                reason_prefix = "Balanced cost and transit time"

            logger.info("━━━ [ROUTE_REC] Using cost_weight=%.2f for user %d", cost_weight, user_id)

            # 3. Call existing route_engine
            request = RouteEvaluationRequest(
                origin_city=origin_city,
                destination_city=destination_city,
                cargo_type=cargo_type,
                cargo_value_usd=cargo_value_usd,
                hs_code=hs_code,
                cargo_volume_cbm=cargo_volume_cbm,
                cargo_weight_kg=cargo_weight_kg,
                container_count=container_count,
                cost_weight=cost_weight
            )

            response = evaluate_routes(request, user_id=user_id, conversation_id=conversation_id)

            if not response.routes:
                logger.info("━━━ [ROUTE_REC] No routes found")
                return [], 0

            # 4. Convert to RouteRecommendation format
            recommendations = []
            for i, route in enumerate(response.routes[:top_k]):
                # Determine badge
                badge = None
                if route.tag == "cheapest":
                    badge = "Best value"
                elif route.tag == "fastest":
                    badge = "Fastest"
                elif route.tag == "balanced":
                    badge = "Recommended for you"

                # Check if this carrier is preferred
                is_preferred_carrier = (
                    preferences and
                    preferences.preferred_carriers and
                    route.carrier in json.loads(preferences.preferred_carriers)
                )

                if is_preferred_carrier:
                    badge = "Your preferred carrier"

                recommendations.append(RouteRecommendation(
                    route_id=route.id,
                    origin=route.origin_port,
                    destination=str(route.destination_ports[0]) if route.destination_ports else "N/A",
                    mode=route.mode,
                    carrier=route.carriers[0] if route.carriers else "N/A",
                    total_cost_usd=route.cost.total_min,
                    transit_days=int(route.transit.total_min),
                    score=1.0 - (route.score / 100.0), # Convert score to 0-1 range
                    reason=f"{reason_prefix}. {route.name}",
                    badge=badge
                ))

            # 5. Log recommendation
            rec_id = self._log_recommendation(
                user_id=user_id,
                conversation_id=conversation_id,
                recommendations=recommendations,
                context={
                    "origin": origin_city,
                    "destination": destination_city,
                    "cargo_type": cargo_type,
                    "cost_weight": cost_weight,
                    "has_preferences": preferences is not None
                }
            )

            logger.info("━━━ [ROUTE_REC ✔] Returned %d route recommendations", len(recommendations))
            return recommendations, rec_id

        except Exception as exc:
            logger.warning("━━━ [ROUTE_REC ✘] Failed to generate recommendations: %s", exc)
            return [], 0

    def _get_user_preferences(self, user_id: int) -> Optional[UserPreference]:
        """Load user preferences from database."""
        try:
            with Session(engine) as session:
                stmt = select(UserPreference).where(UserPreference.user_id == user_id)
                return session.exec(stmt).first()
        except Exception as exc:
            logger.warning("━━━ [ROUTE_REC] Failed to load preferences: %s", exc)
            return None

    def _log_recommendation(
        self,
        user_id: int,
        conversation_id: Optional[str],
        recommendations: list[RouteRecommendation],
        context: dict
    ) -> int:
        """Log recommendation to database and return recommendation_id."""
        try:
            with Session(engine) as session:
                rec_result = RecommendationResult(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    recommendation_type=RecommendationType.route.value,
                    model_version="preference_heuristic_v1",
                    algorithm_used="user_preference_based",
                    recommended_items=json.dumps([
                        {
                            "route_id": r.route_id,
                            "carrier": r.carrier,
                            "cost_usd": r.total_cost_usd,
                            "transit_days": r.transit_days,
                            "score": r.score
                        }
                        for r in recommendations
                    ]),
                    context_json=json.dumps(context)
                )
                session.add(rec_result)
                session.commit()
                session.refresh(rec_result)
                logger.info("━━━ [ROUTE_REC] Logged recommendation_id=%d", rec_result.id)
                return rec_result.id
        except Exception as exc:
            logger.warning("━━━ [ROUTE_REC] Failed to log recommendation: %s", exc)
            return 0
