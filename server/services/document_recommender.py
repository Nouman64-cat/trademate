"""
Document Recommender Service
────────────────────────────

Content-based filtering using Pinecone embeddings (NO ML TRAINING)

Algorithm:
1. Aggregate recent messages into single query
2. Embed the aggregated query
3. Query Pinecone (similar to existing search_trade_documents tool)
4. Filter out already-retrieved documents
5. Return top K with explanations
"""

import json
import logging
from typing import Optional
from sqlmodel import Session, select
from database.database import engine
from models.recommendation import RecommendationResult, RecommendationType
from models.conversation import Message
from schemas.recommendation import DocumentRecommendation
from agent.bot import _get_embeddings, _get_pinecone_index

logger = logging.getLogger(__name__)


class DocumentRecommender:
    """Recommends relevant trade documents based on conversation context."""

    def __init__(self):
        self.embeddings = None  # Lazy-loaded
        self.pinecone_index = None  # Lazy-loaded

    def recommend(
        self,
        user_id: int,
        conversation_id: str,
        conversation_context: list[dict],  # [{"role": "user", "content": "..."}, ...]
        top_k: int = 3
    ) -> tuple[list[DocumentRecommendation], int]:
        """
        Generate document recommendations based on conversation context.

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            conversation_context: List of recent messages (role + content)
            top_k: Number of recommendations

        Returns:
            Tuple of (recommendations, recommendation_id)
        """
        try:
            # 1. Aggregate recent user messages into single query
            user_messages = [
                msg["content"] for msg in conversation_context
                if msg.get("role") == "user"
            ]

            if not user_messages:
                logger.info("━━━ [DOC_REC] No user messages to base recommendations on")
                return [], 0

            combined_query = "\n".join(user_messages[-3:])  # Last 3 user messages

            # 2. Check if query is relevant for document recommendations
            if not self._should_recommend_documents(combined_query):
                logger.info("━━━ [DOC_REC] Query not relevant for document recommendations")
                return [], 0

            # 3. Lazy-load embeddings and Pinecone
            if self.embeddings is None:
                self.embeddings = _get_embeddings()
            if self.pinecone_index is None:
                self.pinecone_index = _get_pinecone_index()

            # 4. Embed the aggregated query
            query_vector = self.embeddings.embed_query(combined_query)

            # 5. Query Pinecone (fetch more for filtering)
            results = self.pinecone_index.query(
                vector=query_vector,
                top_k=top_k + 10,  # Fetch extra for filtering
                include_metadata=True
            )

            matches = results.get("matches", [])
            if not matches:
                logger.info("━━━ [DOC_REC] No matching documents found")
                return [], 0

            # 6. Filter out already-shown documents
            already_shown = self._get_shown_documents(conversation_id)
            filtered_matches = [
                m for m in matches
                if m.get("metadata", {}).get("source") not in already_shown
            ][:top_k]

            if not filtered_matches:
                logger.info("━━━ [DOC_REC] All matches already shown in conversation")
                return [], 0

            # 7. Format recommendations with explanations
            recommendations = []
            for match in filtered_matches:
                metadata = match.get("metadata", {})
                recommendations.append(DocumentRecommendation(
                    document_id=match.get("id", ""),
                    source=metadata.get("source", "Unknown Document"),
                    snippet=metadata.get("text", "")[:200],
                    relevance_score=match.get("score", 0.0),
                    reason=self._generate_reason(combined_query)
                ))

            # 8. Log recommendation to database
            rec_id = self._log_recommendation(
                user_id=user_id,
                conversation_id=conversation_id,
                recommendations=recommendations,
                context={"query": combined_query[:200]}
            )

            logger.info("━━━ [DOC_REC ✔] Returned %d document recommendations", len(recommendations))
            return recommendations, rec_id

        except Exception as exc:
            logger.warning("━━━ [DOC_REC ✘] Failed to generate recommendations: %s", exc)
            return [], 0

    def _should_recommend_documents(self, query: str) -> bool:
        """Check if query is relevant for document recommendations."""
        # Keywords that indicate regulatory/compliance questions
        keywords = [
            "regulation", "compliance", "policy", "law", "requirement",
            "duty", "tariff", "restriction", "permit", "license",
            "sro", "notification", "rule", "amendment", "import", "export"
        ]

        query_lower = query.lower()
        return any(keyword in query_lower for keyword in keywords)

    def _get_shown_documents(self, conversation_id: str) -> set[str]:
        """Get set of document sources already shown in this conversation."""
        try:
            with Session(engine) as session:
                # Query messages in this conversation that have sources_hit
                messages = session.exec(
                    select(Message)
                    .where(
                        Message.conversation_id == conversation_id,
                        Message.sources_hit.is_not(None)
                    )
                ).all()

                shown = set()
                for msg in messages:
                    if msg.sources_hit:
                        try:
                            sources = json.loads(msg.sources_hit)
                            if isinstance(sources, list):
                                shown.update(sources)
                        except json.JSONDecodeError:
                            pass

                return shown
        except Exception as exc:
            logger.warning("━━━ [DOC_REC] Failed to get shown documents: %s", exc)
            return set()

    def _generate_reason(self, query: str) -> str:
        """Generate human-readable reason for recommendation."""
        # Simple keyword extraction
        keywords = {
            "import": "import regulations",
            "export": "export regulations",
            "tariff": "tariff information",
            "duty": "duty requirements",
            "compliance": "compliance requirements",
            "sro": "SRO notifications",
            "restriction": "trade restrictions"
        }

        query_lower = query.lower()
        for keyword, topic in keywords.items():
            if keyword in query_lower:
                return f"Related to your question about {topic}"

        return "Related to your query about trade regulations"

    def _log_recommendation(
        self,
        user_id: int,
        conversation_id: str,
        recommendations: list[DocumentRecommendation],
        context: dict
    ) -> int:
        """Log recommendation to database and return recommendation_id."""
        try:
            with Session(engine) as session:
                rec_result = RecommendationResult(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    recommendation_type=RecommendationType.document.value,
                    model_version="content_based_v1",
                    algorithm_used="pinecone_vector_similarity",
                    recommended_items=json.dumps([
                        {
                            "document_id": r.document_id,
                            "source": r.source,
                            "snippet": r.snippet[:100],
                            "relevance_score": r.relevance_score
                        }
                        for r in recommendations
                    ]),
                    context_json=json.dumps(context)
                )
                session.add(rec_result)
                session.commit()
                session.refresh(rec_result)
                logger.info("━━━ [DOC_REC] Logged recommendation_id=%d", rec_result.id)
                return rec_result.id
        except Exception as exc:
            logger.warning("━━━ [DOC_REC] Failed to log recommendation: %s", exc)
            return 0
