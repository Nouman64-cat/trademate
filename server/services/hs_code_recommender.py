"""
HS Code Recommender Service
───────────────────────────────

Phase 1: Content-based filtering using Memgraph vector similarity
Phase 2: Add collaborative filtering (when sufficient data available)

Algorithm (Phase 1):
1. Use most recent searched HS code as seed
2. Query Memgraph vector index for semantically similar codes
3. Return top K excluding the seed
4. Fallback: Return popular codes for user's trade_role if no context
"""

import json
import logging
from typing import Optional
from sqlmodel import Session
from database.database import engine
from models.recommendation import RecommendationResult, RecommendationType
from schemas.recommendation import HSCodeRecommendation
from agent.bot import _get_driver

logger = logging.getLogger(__name__)

# Cypher query for finding related HS codes (text-based fallback)
# TODO: Use vector similarity once memgraph-mage is installed
_SIMILARITY_QUERY_FALLBACK = """
// Get seed code and its heading/subheading
MATCH (hd:Heading)-[:HAS_SUBHEADING]->(sh:SubHeading)-[:HAS_HSCODE]->(seed:HSCode)
WHERE seed.code STARTS WITH $seed_code
  AND ('PK' IN labels(seed) OR 'US' IN labels(seed))

// Find related codes in the same heading
MATCH (hd)-[:HAS_SUBHEADING]->(related_sh:SubHeading)-[:HAS_HSCODE]->(candidate:HSCode)
WHERE candidate.code <> $seed_code
  AND (
    ('PK' IN labels(seed) AND 'PK' IN labels(candidate)) OR
    ('US' IN labels(seed) AND 'US' IN labels(candidate))
  )

WITH candidate, sh, related_sh,
     CASE
       WHEN related_sh.code = sh.code THEN 0.9  // Same subheading
       ELSE 0.7  // Same heading
     END AS similarity

WITH candidate, similarity
ORDER BY similarity DESC, candidate.code
LIMIT $top_k

// Fetch final display details
OPTIONAL MATCH (result_sh:SubHeading)-[:HAS_HSCODE]->(candidate)
OPTIONAL MATCH (result_hd:Heading)-[:HAS_SUBHEADING]->(result_sh)

RETURN
    candidate.code AS code,
    COALESCE(candidate.hts_code, candidate.code) AS display_code,
    COALESCE(candidate.description, result_hd.description, 'No description') AS description,
    similarity,
    CASE WHEN 'PK' IN labels(candidate) THEN 'PK' ELSE 'US' END AS source
ORDER BY similarity DESC
"""


class HSCodeRecommender:
    """Recommends related HS codes based on user's search history."""

    def __init__(self):
        self.driver = None  # Lazy-loaded
        self.collaborative_model = None  # Future: load from S3 when available

    def recommend(
        self,
        user_id: int,
        context_hs_codes: list[str],  # Recently searched codes
        conversation_id: Optional[str] = None,
        top_k: int = 10
    ) -> tuple[list[HSCodeRecommendation], int]:
        """
        Generate HS code recommendations.

        Args:
            user_id: User ID
            context_hs_codes: List of recently searched HS codes
            conversation_id: Optional conversation ID
            top_k: Number of recommendations

        Returns:
            Tuple of (recommendations, recommendation_id)
        """
        try:
            # Check if collaborative model is available (Phase 2)
            if self.collaborative_model is not None:
                return self._recommend_collaborative(user_id, context_hs_codes, top_k)
            else:
                return self._recommend_content_based(user_id, context_hs_codes, conversation_id, top_k)

        except Exception as exc:
            logger.warning("━━━ [HS_REC ✘] Failed to generate recommendations: %s", exc)
            return [], 0

    def _recommend_content_based(
        self,
        user_id: int,
        context_codes: list[str],
        conversation_id: Optional[str],
        top_k: int
    ) -> tuple[list[HSCodeRecommendation], int]:
        """Content-based recommendations using Memgraph vector similarity."""

        # No context - return popular codes
        if not context_codes:
            logger.info("━━━ [HS_REC] No context codes - using popularity fallback")
            return self._get_popular_codes(user_id, conversation_id, top_k)

        # Use most recent code as seed
        seed_code = context_codes[-1]
        logger.info("━━━ [HS_REC] Vector search from seed: %s", seed_code)

        # Lazy-load Memgraph driver
        if self.driver is None:
            self.driver = _get_driver()

        # Query Memgraph for similar codes
        recommendations = []
        try:
            with self.driver.session() as session:
                result = session.run(_SIMILARITY_QUERY_FALLBACK, {
                    "seed_code": seed_code,
                    "top_k": top_k
                })

                for record in result:
                    recommendations.append(HSCodeRecommendation(
                        hs_code=record["display_code"],
                        description=record["description"],
                        source=record["source"],
                        score=record["similarity"],
                        reason="Semantically similar to your recent search"
                    ))

        except Exception as exc:
            logger.warning("━━━ [HS_REC] Memgraph query failed: %s", exc)
            return [], 0

        if not recommendations:
            logger.info("━━━ [HS_REC] No similar codes found")
            return [], 0

        # Log recommendation
        rec_id = self._log_recommendation(
            user_id=user_id,
            conversation_id=conversation_id,
            recommendations=recommendations,
            algorithm="memgraph_vector_similarity",
            context={"seed_code": seed_code}
        )

        logger.info("━━━ [HS_REC ✔] Returned %d HS code recommendations", len(recommendations))
        return recommendations, rec_id

    def _get_popular_codes(
        self,
        user_id: int,
        conversation_id: Optional[str],
        top_k: int
    ) -> tuple[list[HSCodeRecommendation], int]:
        """
        Fallback: Return popular HS codes for user's trade_role.

        Queries UserInteraction table to find most searched codes by similar users.
        """
        try:
            from models.interaction import UserInteraction, InteractionType
            from models.user import User
            from sqlmodel import select, func

            with Session(engine) as session:
                # Get user's trade_role
                user = session.exec(select(User).where(User.id == user_id)).first()
                if not user:
                    return [], 0

                # Query popular codes for this trade_role
                stmt = (
                    select(
                        UserInteraction.hs_code,
                        func.count(UserInteraction.id).label("count")
                    )
                    .join(User, User.id == UserInteraction.user_id)
                    .where(
                        UserInteraction.interaction_type == InteractionType.search_hs_code,
                        UserInteraction.hs_code.is_not(None),
                        User.trade_role == user.trade_role
                    )
                    .group_by(UserInteraction.hs_code)
                    .order_by(func.count(UserInteraction.id).desc())
                    .limit(top_k)
                )

                results = session.exec(stmt).all()

                if not results:
                    logger.info("━━━ [HS_REC] No popular codes found")
                    return [], 0

                # Format as recommendations
                recommendations = []
                for hs_code, count in results:
                    # Query Memgraph for description
                    description = self._get_code_description(hs_code)
                    recommendations.append(HSCodeRecommendation(
                        hs_code=hs_code,
                        description=description,
                        source="PK",  # Assume PK for now
                        score=min(count / 100.0, 1.0),  # Normalize count to 0-1
                        reason=f"Popular among {user.trade_role}s"
                    ))

                # Log recommendation
                rec_id = self._log_recommendation(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    recommendations=recommendations,
                    algorithm="popularity_by_trade_role",
                    context={"trade_role": user.trade_role}
                )

                logger.info("━━━ [HS_REC ✔] Returned %d popular codes", len(recommendations))
                return recommendations, rec_id

        except Exception as exc:
            logger.warning("━━━ [HS_REC] Popular codes query failed: %s", exc)
            return [], 0

    def _get_code_description(self, hs_code: str) -> str:
        """Fetch HS code description from Memgraph."""
        try:
            if self.driver is None:
                self.driver = _get_driver()

            with self.driver.session() as session:
                result = session.run(
                    "MATCH (hs:HSCode {code: $code}) RETURN hs.description AS desc",
                    {"code": hs_code}
                ).single()

                if result and result["desc"]:
                    return result["desc"]
        except Exception:
            pass
        return "HS code description"

    def _recommend_collaborative(
        self,
        user_id: int,
        context_codes: list[str],
        top_k: int
    ) -> tuple[list[HSCodeRecommendation], int]:
        """
        Phase 2: Collaborative filtering recommendations.

        TODO: Implement when ML model is trained (requires 500+ interactions).
        """
        logger.info("━━━ [HS_REC] Collaborative filtering not yet implemented")
        return [], 0

    def _log_recommendation(
        self,
        user_id: int,
        conversation_id: Optional[str],
        recommendations: list[HSCodeRecommendation],
        algorithm: str,
        context: dict
    ) -> int:
        """Log recommendation to database and return recommendation_id."""
        try:
            with Session(engine) as session:
                rec_result = RecommendationResult(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    recommendation_type=RecommendationType.hs_code.value,
                    model_version="content_based_v1",
                    algorithm_used=algorithm,
                    recommended_items=json.dumps([
                        {
                            "hs_code": r.hs_code,
                            "description": r.description[:100],
                            "source": r.source,
                            "score": r.score
                        }
                        for r in recommendations
                    ]),
                    context_json=json.dumps(context)
                )
                session.add(rec_result)
                session.commit()
                session.refresh(rec_result)
                logger.info("━━━ [HS_REC] Logged recommendation_id=%d", rec_result.id)
                return rec_result.id
        except Exception as exc:
            logger.warning("━━━ [HS_REC] Failed to log recommendation: %s", exc)
            return 0
