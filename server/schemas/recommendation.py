from typing import Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from models.recommendation import RecommendationType

# ── Generic Schemas ───────────────────────────────────────────────────────────

class RecommendedItem(BaseModel):
    id: str
    name: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)
    reason: Optional[str] = None

class RecommendationResponse(BaseModel):
    recommendation_id: int
    recommendation_type: RecommendationType
    items: list[RecommendedItem]
    model_version: str
    explanation: Optional[str] = None

class RecommendationFeedback(BaseModel):
    selected_item_id: str
    selection_rank: Optional[int] = None
    was_helpful: Optional[bool] = None
    feedback_text: Optional[str] = None


# ── Document Recommendations ──────────────────────────────────────────────────

class DocumentRecommendation(BaseModel):
    document_id: str = Field(description="Unique identifier for the document chunk")
    source: str = Field(description="Source filename (e.g., 'SRO_1234_2023.pdf')")
    snippet: str = Field(description="Relevant excerpt from the document (max 200 chars)")
    relevance_score: float = Field(description="Similarity score (0-1)", ge=0, le=1)
    reason: str = Field(description="Explanation of why this document is recommended")


class DocumentRecommendationResponse(BaseModel):
    recommendations: list[DocumentRecommendation]
    recommendation_id: int = Field(description="ID for tracking user feedback")


# ── HS Code Recommendations ───────────────────────────────────────────────────

class HSCodeRecommendation(BaseModel):
    hs_code: str = Field(description="HS code (12-digit for PK, variable for US)")
    description: str = Field(description="Product description")
    source: str = Field(description="'PK' or 'US'")
    score: float = Field(description="Recommendation score (0-1)", ge=0, le=1)
    reason: str = Field(description="Why this code is recommended")


class HSCodeRecommendationResponse(BaseModel):
    recommendations: list[HSCodeRecommendation]
    recommendation_id: int = Field(description="ID for tracking user feedback")


# ── Tariff Optimization ───────────────────────────────────────────────────────

class TariffAlternative(BaseModel):
    hs_code: str = Field(description="Alternative HS code")
    description: str = Field(description="Product description")
    current_tariff_rate: float = Field(description="Original tariff rate (e.g., 0.18 for 18%)")
    alternative_tariff_rate: float = Field(description="Lower tariff rate (e.g., 0.12 for 12%)")
    estimated_savings_usd: float = Field(description="Estimated duty savings in USD")
    similarity_score: float = Field(description="Semantic similarity to original code (0-1)", ge=0, le=1)
    reason: str = Field(description="Why this alternative is viable")
    disclaimer: str = Field(
        description="Legal disclaimer about classification verification",
        default="⚠️ Classification alternatives are suggestions only. You must verify with customs authorities that the alternative classification is legally valid and compliant for your specific product. Incorrect classification can result in penalties."
    )


class TariffOptimizationResponse(BaseModel):
    alternatives: list[TariffAlternative]
    recommendation_id: int = Field(description="ID for tracking user feedback")


# ── Route Recommendations ─────────────────────────────────────────────────────

class RouteRecommendation(BaseModel):
    route_id: str = Field(description="Unique route identifier")
    origin: str = Field(description="Origin city")
    destination: str = Field(description="Destination city")
    mode: str = Field(description="Transport mode (Sea, Air, Land)")
    carrier: str = Field(description="Carrier/shipping line")
    total_cost_usd: float = Field(description="Total estimated cost in USD")
    transit_days: int = Field(description="Estimated transit time in days")
    score: float = Field(description="Recommendation score (0-1)", ge=0, le=1)
    reason: str = Field(description="Why this route is recommended")
    badge: Optional[str] = Field(default=None, description="Badge label (e.g., 'Recommended for you', 'Best value')")


class RouteRecommendationResponse(BaseModel):
    routes: list[RouteRecommendation]
    recommendation_id: int = Field(description="ID for tracking user feedback")


# ── Feedback ──────────────────────────────────────────────────────────────────

class RecommendationFeedbackRequest(BaseModel):
    selected_item_id: Optional[str] = Field(default=None, description="ID of selected item (if clicked)")
    selection_rank: Optional[int] = Field(default=None, description="Position in list (1-indexed)")
    was_helpful: bool = Field(description="Whether the recommendation was helpful")
    feedback_text: Optional[str] = Field(default=None, max_length=500, description="Optional feedback text")


class FeedbackResponse(BaseModel):
    message: str = Field(default="Feedback recorded successfully")
