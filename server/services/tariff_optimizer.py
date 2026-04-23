"""
Tariff Optimizer Service
────────────────────────

Graph-based similarity + duty comparison (Rule-Based, No ML Training Required)

Algorithm:
1. Query Memgraph for given HS code with tariff data
2. Get embedding for the HS code
3. Vector search for semantically similar codes
4. FILTER: Only codes with LOWER tariff/duty rates
5. RANK: By (similarity_score × duty_savings)
6. Return top K with savings estimates and legal disclaimers
"""

import json
import logging
from typing import Optional
from sqlmodel import Session
from database.database import engine
from models.recommendation import RecommendationResult, RecommendationType
from schemas.recommendation import TariffAlternative
from agent.bot import _get_driver

logger = logging.getLogger(__name__)

# Cypher query to find lower-tariff alternatives (text-based fallback)
# TODO: Use vector similarity once memgraph-mage is installed
_TARIFF_OPTIMIZATION_QUERY_FALLBACK = """
// Get original code with tariff and hierarchy
MATCH (hd_orig:Heading:PK)-[:HAS_SUBHEADING]->(sh_orig:SubHeading:PK)-[:HAS_HSCODE]->(original:HSCode:PK {code: $hs_code})
MATCH (original)-[:HAS_TARIFF]->(t_original:Tariff)

// Find codes in same heading or nearby headings with lower tariffs
MATCH (hd_candidate:Heading:PK)-[:HAS_SUBHEADING]->(sh_candidate:SubHeading:PK)-[:HAS_HSCODE]->(candidate:HSCode:PK)
MATCH (candidate)-[:HAS_TARIFF]->(t_candidate:Tariff)

WHERE candidate.code <> $hs_code
  AND t_candidate.rate < t_original.rate
  AND (
    // Same heading (more similar)
    hd_candidate.code = hd_orig.code OR
    // Same chapter (less similar)
    substring(hd_candidate.code, 0, 2) = substring(hd_orig.code, 0, 2)
  )

WITH
    candidate,
    t_candidate,
    t_original,
    hd_orig,
    hd_candidate,
    sh_orig,
    sh_candidate,
    // Calculate similarity based on hierarchy proximity
    CASE
      WHEN sh_candidate.code = sh_orig.code THEN 0.95  // Same subheading (rare but possible)
      WHEN hd_candidate.code = hd_orig.code THEN 0.85  // Same heading
      ELSE 0.70  // Same chapter
    END AS similarity,
    (t_original.rate - t_candidate.rate) AS savings_percent,
    (t_original.rate - t_candidate.rate) * $cargo_value_usd AS savings_usd

WITH
    candidate,
    t_candidate.rate AS alt_rate,
    t_original.rate AS orig_rate,
    similarity,
    savings_percent,
    savings_usd,
    similarity * savings_percent AS combined_score

ORDER BY combined_score DESC
LIMIT $max_alternatives

// Get description
OPTIONAL MATCH (sh_final:SubHeading:PK)-[:HAS_HSCODE]->(candidate)
OPTIONAL MATCH (hd_final:Heading:PK)-[:HAS_SUBHEADING]->(sh_final)

RETURN
    candidate.code AS code,
    COALESCE(candidate.description, hd_final.description, 'No description') AS description,
    orig_rate,
    alt_rate,
    savings_percent,
    savings_usd,
    similarity
ORDER BY combined_score DESC
"""


class TariffOptimizer:
    """Finds alternative HS code classifications with lower duty rates."""

    def __init__(self):
        self.driver = None  # Lazy-loaded

    def find_alternatives(
        self,
        hs_code: str,
        cargo_value_usd: float,
        user_id: int,
        conversation_id: Optional[str] = None,
        source: str = "PK",
        max_alternatives: int = 5
    ) -> tuple[list[TariffAlternative], int]:
        """
        Find alternative HS codes with lower tariff rates.

        Args:
            hs_code: Current HS code
            cargo_value_usd: Cargo value for savings calculation
            user_id: User ID
            conversation_id: Optional conversation ID
            source: "PK" or "US" (currently only PK supported)
            max_alternatives: Max number of alternatives to return

        Returns:
            Tuple of (alternatives, recommendation_id)
        """
        try:
            if source != "PK":
                logger.info("━━━ [TARIFF_OPT] Only PK tariffs supported currently")
                return [], 0

            logger.info("━━━ [TARIFF_OPT] Finding alternatives for %s (value=$%.2f)", hs_code, cargo_value_usd)

            # Lazy-load Memgraph driver
            if self.driver is None:
                self.driver = _get_driver()

            # Query Memgraph for lower-tariff alternatives
            alternatives = []
            try:
                with self.driver.session() as session:
                    result = session.run(_TARIFF_OPTIMIZATION_QUERY_FALLBACK, {
                        "hs_code": hs_code,
                        "cargo_value_usd": cargo_value_usd,
                        "max_alternatives": max_alternatives
                    })

                    for record in result:
                        alternatives.append(TariffAlternative(
                            hs_code=record["code"],
                            description=record["description"],
                            current_tariff_rate=record["orig_rate"],
                            alternative_tariff_rate=record["alt_rate"],
                            estimated_savings_usd=record["savings_usd"],
                            similarity_score=record["similarity"],
                            reason=self._generate_reason(
                                record["similarity"],
                                record["savings_percent"]
                            )
                            # disclaimer is set by default in schema
                        ))

            except Exception as exc:
                logger.warning("━━━ [TARIFF_OPT] Memgraph query failed: %s", exc)
                return [], 0

            if not alternatives:
                logger.info("━━━ [TARIFF_OPT] No lower-tariff alternatives found")
                return [], 0

            # Log recommendation
            rec_id = self._log_recommendation(
                user_id=user_id,
                conversation_id=conversation_id,
                alternatives=alternatives,
                context={
                    "original_hs_code": hs_code,
                    "cargo_value_usd": cargo_value_usd,
                    "source": source
                }
            )

            logger.info("━━━ [TARIFF_OPT ✔] Returned %d tariff alternatives (potential savings: $%.2f)",
                       len(alternatives),
                       sum(a.estimated_savings_usd for a in alternatives))
            return alternatives, rec_id

        except Exception as exc:
            logger.warning("━━━ [TARIFF_OPT ✘] Failed to find alternatives: %s", exc)
            return [], 0

    def _generate_reason(self, similarity: float, savings_percent: float) -> str:
        """Generate human-readable reason for the alternative."""
        if similarity > 0.9 and savings_percent > 0.05:
            return f"Very similar product with {savings_percent*100:.1f}% lower duty rate"
        elif similarity > 0.8:
            return f"Similar product category with {savings_percent*100:.1f}% duty savings"
        else:
            return f"Related classification with potential {savings_percent*100:.1f}% savings"

    def estimate_savings(
        self,
        original_code: str,
        alternative_code: str,
        cargo_value_usd: float
    ) -> float:
        """
        Calculate duty savings between two HS codes.

        Args:
            original_code: Current HS code
            alternative_code: Alternative HS code
            cargo_value_usd: Cargo value

        Returns:
            Estimated savings in USD
        """
        try:
            if self.driver is None:
                self.driver = _get_driver()

            with self.driver.session() as session:
                result = session.run("""
                    MATCH (orig:HSCode:PK {code: $original_code})-[:HAS_TARIFF]->(t_orig:Tariff)
                    MATCH (alt:HSCode:PK {code: $alternative_code})-[:HAS_TARIFF]->(t_alt:Tariff)
                    RETURN t_orig.rate AS orig_rate, t_alt.rate AS alt_rate
                """, {
                    "original_code": original_code,
                    "alternative_code": alternative_code
                }).single()

                if result:
                    savings_percent = result["orig_rate"] - result["alt_rate"]
                    return savings_percent * cargo_value_usd
                return 0.0

        except Exception as exc:
            logger.warning("━━━ [TARIFF_OPT] Savings calculation failed: %s", exc)
            return 0.0

    def _log_recommendation(
        self,
        user_id: int,
        conversation_id: Optional[str],
        alternatives: list[TariffAlternative],
        context: dict
    ) -> int:
        """Log recommendation to database and return recommendation_id."""
        try:
            with Session(engine) as session:
                rec_result = RecommendationResult(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    recommendation_type=RecommendationType.tariff_optimization.value,
                    model_version="graph_based_v1",
                    algorithm_used="memgraph_vector_similarity_with_tariff_filter",
                    recommended_items=json.dumps([
                        {
                            "hs_code": a.hs_code,
                            "description": a.description[:100],
                            "current_rate": a.current_tariff_rate,
                            "alternative_rate": a.alternative_tariff_rate,
                            "savings_usd": a.estimated_savings_usd,
                            "similarity": a.similarity_score
                        }
                        for a in alternatives
                    ]),
                    context_json=json.dumps(context)
                )
                session.add(rec_result)
                session.commit()
                session.refresh(rec_result)
                logger.info("━━━ [TARIFF_OPT] Logged recommendation_id=%d", rec_result.id)
                return rec_result.id
        except Exception as exc:
            logger.warning("━━━ [TARIFF_OPT] Failed to log recommendation: %s", exc)
            return 0
