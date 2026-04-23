# TradeMate ML-Based Recommendation System
## Comprehensive Implementation Plan & Documentation

**Version:** 1.0
**Last Updated:** 2026-04-22
**Status:** Approved - Ready for Implementation

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Database Schema](#database-schema)
4. [Recommendation Systems](#recommendation-systems)
5. [API Endpoints](#api-endpoints)
6. [Infrastructure Setup](#infrastructure-setup)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Success Metrics](#success-metrics)
9. [Risk Management](#risk-management)

---

## Overview

### Executive Summary

This document outlines the comprehensive plan to implement **4 ML-based recommendation systems** for TradeMate:

1. **Smart Document Recommendations** - Context-aware trade document suggestions
2. **Product/HS Code Recommendations** - Collaborative filtering for related products
3. **Tariff Optimization Recommendations** - Alternative HS classifications with lower duties
4. **Optimal Route Recommendations** - Personalized shipping route suggestions

### Key Features

- ✅ **Immediate Launch** with content-based recommendations (no ML training required initially)
- ✅ **Automatic ML Transition** when sufficient data collected (500+ interactions)
- ✅ **Full Infrastructure** including Redis, Celery, AWS S3 for model storage
- ✅ **A/B Testing Framework** for continuous optimization
- ✅ **Comprehensive Monitoring** with Prometheus + Grafana

### Strategic Approach

**Phase 1 (Week 1):** Launch all 4 systems with content-based/rule-based algorithms
- Provides immediate value to users
- Starts collecting interaction data
- No ML model training required

**Phase 2 (Week 3-4):** Add collaborative filtering ML models
- Train on collected user interaction data
- Hybrid approach (blend ML + content-based)
- A/B test ML vs baseline

**Phase 3 (Ongoing):** Continuous improvement
- Weekly model retraining
- Performance monitoring
- Feature enhancements based on user feedback

---

## System Architecture

### Technology Stack

#### Core Infrastructure
- **FastAPI** - Existing web framework
- **PostgreSQL** - Relational data (interactions, preferences, model metadata)
- **Redis 7.x** - Message broker, cache, result backend
- **Celery + Beat** - Background jobs, scheduled tasks
- **Flower** - Celery task monitoring UI

#### Machine Learning
- **OpenAI Embeddings** (`text-embedding-3-small`) - Semantic similarity
- **Memgraph/Memgraph** - Graph database with vector index (existing)
- **Pinecone** - Vector database for documents (existing)
- **implicit** - Collaborative filtering (ALS)
- **LightGBM** - Gradient boosting (route preferences)
- **scikit-learn** - Feature engineering, evaluation

#### Model Storage
- **AWS S3** - Model artifact storage with versioning
- **Local Cache** - `/tmp/model_cache/` for fast loading

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (React)                     │
└────────────────┬────────────────────────────────────────┘
                 │ HTTP/SSE
                 ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Routes (recommendations.py)         │
│  /v1/recommendations/documents                          │
│  /v1/recommendations/hs-codes                           │
│  /v1/recommendations/tariff-optimization                │
│  /v1/recommendations/routes                             │
└────────────────┬────────────────────────────────────────┘
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
┌─────────────────┐   ┌──────────────────────┐
│  Recommender    │   │  User Interaction    │
│  Services       │   │  Tracking            │
│  - Document     │   │  (bot.py, chat.py)   │
│  - HS Code      │   └──────────┬───────────┘
│  - Tariff       │              │
│  - Route        │              ▼
└────────┬────────┘   ┌──────────────────────┐
         │            │   PostgreSQL         │
         │            │   - user_interactions│
         │            │   - recommendations  │
         │            │   - user_preferences │
         │            └──────────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌─────────────┐
│ Memgraph  │ │  Pinecone   │
│ Vector │ │  Vector DB  │
│ Search │ │  (Docs)     │
└────────┘ └─────────────┘

         Background Processing
         ═════════════════════
┌─────────────────────────────────────────────┐
│         Celery Workers + Beat                │
│  - Model Training (weekly)                   │
│  - Preference Updates (daily)                │
│  - Similarity Computation (weekly)           │
└────────────┬────────────────────────────────┘
             │
             ▼
     ┌───────────────┐
     │   AWS S3      │
     │   Model       │
     │   Storage     │
     └───────────────┘
```

---

## Database Schema

### New Models (6 Tables)

#### 1. UserInteraction
**Purpose:** Track all user interactions with HS codes, routes, documents

```python
class InteractionType(str, Enum):
    search_hs_code = "search_hs_code"
    view_hs_code = "view_hs_code"
    route_evaluation = "route_evaluation"
    document_retrieval = "document_retrieval"
    recommendation_click = "recommendation_click"

class UserInteraction(SQLModel, table=True):
    __tablename__ = "user_interactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id", ondelete="CASCADE")))
    conversation_id: Optional[str] = Field(sa_column=Column(Text, ForeignKey("conversations.id", ondelete="SET NULL")))
    message_id: Optional[int] = Field(sa_column=Column(Integer, ForeignKey("messages.id", ondelete="SET NULL")))

    interaction_type: str = Field(sa_column=Column(SAEnum(...)))

    # Entity identifiers
    hs_code: Optional[str] = Field(default=None, max_length=12)
    route_id: Optional[str] = Field(default=None, max_length=100)
    document_id: Optional[str] = Field(default=None, max_length=255)

    # Search context
    query: Optional[str] = Field(default=None, max_length=500)
    similarity_score: Optional[float] = Field(default=None)
    rank_position: Optional[int] = Field(default=None)  # Position in search results

    # Flexible metadata
    metadata: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON

    created_at: datetime = Field(default_factory=datetime.utcnow, ...)

    __table_args__ = (
        Index("ix_interactions_user_type_created", "user_id", "interaction_type", "created_at"),
        Index("ix_interactions_conversation", "conversation_id", "created_at"),
        Index("ix_interactions_hs_code", "hs_code", "created_at"),
    )
```

**Use Cases:**
- ML training data for collaborative filtering
- User behavior analysis
- Popularity-based recommendations

#### 2. RecommendationResult
**Purpose:** Track recommendations shown to users and their responses

```python
class RecommendationType(str, Enum):
    route = "route"
    hs_code = "hs_code"
    document = "document"
    tariff_optimization = "tariff_optimization"

class RecommendationResult(SQLModel, table=True):
    __tablename__ = "recommendation_results"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(...)
    conversation_id: Optional[str] = Field(...)
    message_id: Optional[int] = Field(...)

    # Recommendation metadata
    recommendation_type: str = Field(sa_column=Column(SAEnum(...)))
    model_version: str = Field(max_length=50)  # "content_based_v1", "collaborative_v2", etc.
    algorithm_used: str = Field(max_length=100)  # "memgraph_vector", "als", "hybrid"

    # What was recommended
    recommended_items: str = Field(sa_column=Column(Text))  # JSON array
    context: Optional[str] = Field(sa_column=Column(Text))  # JSON (trigger context)

    # User feedback (explicit)
    selected_item_id: Optional[str] = Field(default=None, max_length=100)
    selection_rank: Optional[int] = Field(default=None)  # Which position they selected
    time_to_selection_seconds: Optional[float] = Field(default=None)
    was_helpful: Optional[bool] = Field(default=None)

    # User feedback (implicit)
    implicit_feedback_score: Optional[float] = Field(default=None)  # Dwell time, etc.

    created_at: datetime = Field(...)
    updated_at: Optional[datetime] = Field(sa_column=Column(DateTime, onupdate=datetime.utcnow))

    __table_args__ = (
        Index("ix_recommendations_user_type", "user_id", "recommendation_type", "created_at"),
        Index("ix_recommendations_model", "model_version", "created_at"),
    )
```

**Use Cases:**
- A/B testing evaluation
- Model performance monitoring (CTR, conversion rate)
- User satisfaction tracking

#### 3. UserPreference
**Purpose:** Store learned user preferences (aggregated from interactions)

```python
class UserPreference(SQLModel, table=True):
    __tablename__ = "user_preferences"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(..., unique=True)  # One record per user

    # Route preferences (learned from route evaluations)
    preferred_cargo_types: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON
    typical_cost_weight: Optional[float] = Field(default=None)  # 0 = fastest, 1 = cheapest
    preferred_carriers: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON
    common_routes: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON

    # Trade preferences (learned from HS code searches)
    frequent_hs_chapters: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON
    common_origin_cities: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON
    common_dest_cities: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON
    typical_cargo_value_range: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON {"min": 1000, "max": 50000}

    # Behavioral patterns
    prefers_detailed_responses: Optional[bool] = Field(default=None)
    typical_session_duration_minutes: Optional[float] = Field(default=None)
    response_quality_preference: Optional[float] = Field(default=None)  # Average rating given

    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow, ...)
    confidence_score: Optional[float] = Field(default=None)  # 0-1, based on data quantity

    __table_args__ = (
        Index("ix_user_preferences_user", "user_id"),
    )
```

**Use Cases:**
- Personalized route recommendations
- Cold-start user recommendations
- User segmentation

#### 4. RouteEvaluationHistory
**Purpose:** Persist route evaluation requests (currently ephemeral)

```python
class RouteEvaluationHistory(SQLModel, table=True):
    __tablename__ = "route_evaluation_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(...)
    conversation_id: Optional[str] = Field(...)
    message_id: Optional[int] = Field(...)

    # Request parameters
    origin_city: str = Field(max_length=100)
    destination_city: str = Field(max_length=100)
    cargo_type: str = Field(max_length=20)  # FCL20, FCL40, LCL, AIR
    cargo_value_usd: float
    hs_code: Optional[str] = Field(default=None, max_length=10)
    cargo_volume_cbm: Optional[float] = Field(default=None)
    cargo_weight_kg: Optional[float] = Field(default=None)
    container_count: int = Field(default=1)
    cost_weight: float = Field(default=0.5)  # User's cost vs speed preference

    # Response summary
    routes_count: int
    cheapest_route_id: str = Field(max_length=100)
    fastest_route_id: str = Field(max_length=100)
    balanced_route_id: str = Field(max_length=100)
    selected_route_id: Optional[str] = Field(default=None, max_length=100)  # If user clicked

    # Full response for replay/analysis
    full_response: str = Field(sa_column=Column(Text))  # JSON

    created_at: datetime = Field(...)

    __table_args__ = (
        Index("ix_route_eval_user_created", "user_id", "created_at"),
        Index("ix_route_eval_cities", "origin_city", "destination_city"),
        Index("ix_route_eval_cargo", "cargo_type", "hs_code"),
    )
```

**Use Cases:**
- Train route preference ML model
- Understand user routing patterns
- Personalized route recommendations

#### 5. ModelMetadata
**Purpose:** Track ML model versions, metrics, deployment status

```python
class ModelMetadata(SQLModel, table=True):
    __tablename__ = "model_metadata"

    id: Optional[int] = Field(default=None, primary_key=True)
    model_name: str = Field(max_length=100, unique=True)  # "hs_code_collaborative_v2"
    model_version: str = Field(max_length=50)  # "v2"
    model_type: str = Field(max_length=50)  # "collaborative_filtering", "content_based", "hybrid"

    # Training metadata
    trained_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    training_data_start: Optional[datetime] = Field(...)  # Data range used
    training_data_end: Optional[datetime] = Field(...)
    training_samples_count: Optional[int] = Field(default=None)
    hyperparameters: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON

    # Evaluation metrics
    metrics: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON
    # Example: {"precision@5": 0.32, "recall@10": 0.45, "ndcg@10": 0.41, "coverage": 0.85}

    # Deployment status
    is_active: bool = Field(default=False)  # Only one active per model_type
    deployment_date: Optional[datetime] = Field(...)
    model_artifact_uri: Optional[str] = Field(default=None, max_length=500)  # S3 path

    # Documentation
    description: Optional[str] = Field(default=None, max_length=500)
    created_by: Optional[str] = Field(default=None, max_length=100)

    created_at: datetime = Field(...)

    __table_args__ = (
        Index("ix_model_metadata_active", "is_active", "deployment_date"),
        Index("ix_model_metadata_type", "model_type", "is_active"),
    )
```

**Use Cases:**
- Model versioning and rollback
- A/B testing (select model by version)
- Performance tracking over time

#### 6. ABTestVariant (A/B Testing)
**Purpose:** Assign users to A/B test variants deterministically

```python
class ABTestVariant(SQLModel, table=True):
    __tablename__ = "ab_test_variants"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(...)
    test_name: str = Field(max_length=100)  # "route_rec_v1_vs_v2"
    variant: str = Field(max_length=20)  # "control" or "treatment"
    assigned_at: datetime = Field(...)

    __table_args__ = (
        Index("ix_ab_test_user", "user_id", "test_name", unique=True),
    )

class ABTestConfig(SQLModel, table=True):
    __tablename__ = "ab_test_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    test_name: str = Field(max_length=100, unique=True)
    is_active: bool = Field(default=False)
    traffic_split: float = Field(default=0.5)  # 0.5 = 50/50 split
    control_model_version: str = Field(max_length=50)
    treatment_model_version: str = Field(max_length=50)
    start_date: datetime = Field(...)
    end_date: Optional[datetime] = Field(default=None)

    __table_args__ = (
        Index("ix_ab_test_active", "is_active", "test_name"),
    )
```

---

## Recommendation Systems

### 1. Smart Document Recommendations

#### Algorithm
**Content-Based Filtering** using existing Pinecone vector embeddings

#### How It Works
1. Aggregate recent user messages in conversation (last 5 messages)
2. Embed combined query using OpenAI `text-embedding-3-small`
3. Query Pinecone for semantically similar documents
4. Filter out documents already shown (`sources_hit` in Message table)
5. Return top 3 with explanations

#### Implementation File
`server/services/document_recommender.py`

```python
class DocumentRecommender:
    def recommend(
        self,
        user_id: int,
        conversation_context: list[Message],
        top_k: int = 3
    ) -> list[DocumentRecommendation]:
        # Combine recent user messages
        user_messages = [msg.content for msg in conversation_context if msg.role == "user"]
        combined_query = "\n".join(user_messages[-3:])

        # Embed query
        query_vector = self.embeddings.embed_query(combined_query)

        # Query Pinecone
        results = self.pinecone_index.query(
            vector=query_vector,
            top_k=top_k + 10,
            include_metadata=True
        )

        # Filter already-shown documents
        # Format and return
```

#### Trigger Conditions
- Conversation mentions keywords: "import", "export", "compliance", "regulation", "tariff"
- User asks about procedures, documentation, or policies

#### API Endpoint
`GET /v1/recommendations/documents?conversation_id={id}&top_k=3`

#### Success Metrics
- CTR > 5%
- Time-to-click < 30 seconds
- "Was helpful" feedback > 70%

---

### 2. Product/HS Code Recommendations

#### Phase 1: Content-Based (Launch Immediately)
**Algorithm:** Memgraph vector similarity using existing embeddings

```python
class HSCodeRecommender:
    def _recommend_content_based(
        self,
        context_codes: list[str],  # Recently searched
        top_k: int = 10
    ) -> list[HSCodeRecommendation]:
        # Use most recent code as seed
        seed_code = context_codes[-1]

        # Get embedding from Memgraph
        # Query vector index for similar codes
        # Return top K (excluding seed)
```

**Fallback (Cold Start):** Return popular codes for user's trade_role

#### Phase 2: Collaborative Filtering (After 500+ interactions)
**Algorithm:** Alternating Least Squares (ALS) from `implicit` library

```python
class HSCodeCollaborativeFilter:
    def train(self, interactions: list[UserInteraction]):
        # Build user-item matrix (users × HS codes)
        # Values: interaction count weighted by recency
        # Train ALS model (100-200 dimensions)
        # Save to S3
```

#### Phase 3: Hybrid (Blend Both)
**Algorithm:** Weighted combination (60% collaborative, 40% content-based)

```python
def recommend(self, user_id, context_codes, top_k=10):
    collab_recs = self.collaborative.recommend(user_id, top_k=20)
    content_recs = self.content_based.recommend_similar(context_codes[-1], top_k=20)

    # Blend scores
    blended = self._blend(collab_recs, content_recs, weight=0.6)

    # Re-rank by user preferences (trade_role, target_region)
    return blended[:top_k]
```

#### API Endpoint
`GET /v1/recommendations/hs-codes?context_codes=0101.21,0102.31&top_k=10`

#### Success Metrics
- Precision@5 > 0.3
- Recall@10 > 0.5
- NDCG@10 > 0.4
- Coverage > 80%

---

### 3. Tariff Optimization Recommendations

#### Algorithm
**Graph-Based Similarity + Duty Comparison** (Rule-Based, No ML Training)

#### How It Works
1. Query Memgraph for given HS code with tariff data
2. Get embedding for the HS code
3. Vector search for semantically similar codes
4. **Filter:** Only codes with LOWER tariff/duty rates
5. **Rank:** By `similarity_score × duty_savings`
6. Return top 5 with savings estimates

#### Memgraph Cypher Query
```cypher
MATCH (original:HSCode:PK {code: $hs_code})
OPTIONAL MATCH (original)-[:HAS_TARIFF]->(t_original:Tariff)

CALL vector_search.search('HSCode_embedding', 50, $query_vector)
YIELD node AS candidate, similarity
WHERE 'PK' IN labels(candidate)
  AND candidate.code <> $hs_code

OPTIONAL MATCH (candidate)-[:HAS_TARIFF]->(t_candidate:Tariff)
WHERE t_candidate.rate < t_original.rate

WITH candidate, similarity,
     (t_original.rate - t_candidate.rate) AS savings_percent
RETURN candidate.code, candidate.description,
       t_candidate.rate, savings_percent, similarity
ORDER BY similarity * savings_percent DESC
LIMIT $max_alternatives
```

#### Savings Calculation
```python
def estimate_savings(
    original_code: str,
    alternative_code: str,
    cargo_value_usd: float
) -> float:
    original_tariff = get_tariff_rate(original_code)  # e.g., 0.18 (18%)
    alternative_tariff = get_tariff_rate(alternative_code)  # e.g., 0.12 (12%)

    savings_usd = (original_tariff - alternative_tariff) * cargo_value_usd
    return savings_usd
```

#### API Endpoint
`GET /v1/recommendations/tariff-optimization?hs_code=6203.42&cargo_value_usd=50000`

Response:
```json
{
  "alternatives": [
    {
      "hs_code": "6203.49",
      "description": "Men's trousers, of other textile materials",
      "current_tariff_rate": 0.18,
      "alternative_tariff_rate": 0.12,
      "estimated_savings_usd": 3000.00,
      "similarity_score": 0.92,
      "reason": "Similar product category with lower duty rate",
      "disclaimer": "⚠️ Please verify with customs authorities that this classification is legally valid for your product."
    }
  ]
}
```

#### Legal Compliance
**IMPORTANT:** Always include disclaimer:
> "⚠️ Classification alternatives are suggestions only. You must verify with customs authorities that the alternative classification is legally valid and compliant for your specific product. Incorrect classification can result in penalties."

#### Success Metrics
- Acceptance rate > 20%
- Average savings per accepted recommendation > $500
- False positive rate < 10% (invalid classifications)

---

### 4. Optimal Route Recommendations

#### Phase 1: Preference Heuristics (Launch Immediately)
**Algorithm:** Use `UserPreference` table + simple rules

```python
class RouteRecommender:
    def recommend_routes(
        self,
        user_id: int,
        origin_city: str,
        destination_city: str,
        cargo_type: str
    ) -> list[RouteRecommendation]:
        # Load user preferences
        prefs = self._get_user_preferences(user_id)

        # Default cost_weight if no history
        cost_weight = prefs.typical_cost_weight if prefs else 0.5

        # Call existing route_engine
        routes = route_engine.evaluate(origin_city, destination_city, cargo_type, cost_weight)

        # Boost preferred carriers
        routes = self._boost_preferred_carriers(routes, prefs.preferred_carriers)

        # Add explanations
        for route in routes[:3]:
            route.reason = f"Based on your preference for {'cost' if cost_weight > 0.6 else 'speed'}"

        return routes[:3]
```

#### Phase 2: ML Preference Learning (After 500+ route evaluations)
**Algorithm:** LightGBM Gradient Boosting

```python
class RoutePreferenceModel:
    def train(self, route_history: list[RouteEvaluationHistory]):
        # Extract features
        # User features: trade_role, target_region, company_type
        # Route features: mode, cost, transit_time, carrier
        # Interaction: cost_weight, selected_route

        # Train LightGBM classifier: Will user select this route?
        # Train LightGBM regressor: User's cost_weight preference

        # Save to S3
```

#### API Endpoint
`GET /v1/recommendations/routes?origin=Karachi&destination=New York&cargo_type=FCL20`

Response:
```json
{
  "routes": [
    {
      "route_id": "KHI-NYC-SEA-001",
      "origin": "Karachi",
      "destination": "New York",
      "mode": "Sea",
      "carrier": "Maersk",
      "total_cost_usd": 2450.00,
      "transit_days": 35,
      "score": 0.92,
      "reason": "Based on your preference for cost-effective routes",
      "badge": "Recommended for you"
    }
  ]
}
```

#### Success Metrics
- Top-3 accuracy > 70% (user selects one of top 3 routes)
- Cost_weight prediction MAE < 0.15
- User satisfaction > 4.0/5.0

---

## API Endpoints

### Complete Endpoint Specification

#### 1. GET /v1/recommendations/documents
**Purpose:** Get recommended trade documents based on conversation context

**Parameters:**
- `conversation_id` (required): UUID of conversation
- `top_k` (optional, default=3): Number of recommendations

**Authentication:** JWT Bearer token

**Response:**
```json
{
  "recommendations": [
    {
      "document_id": "sha256_hash",
      "source": "SRO_1234_2023.pdf",
      "snippet": "Import procedures for textile products require...",
      "relevance_score": 0.89,
      "reason": "Related to your question about import regulations"
    }
  ],
  "recommendation_id": 12345
}
```

#### 2. GET /v1/recommendations/hs-codes
**Purpose:** Get recommended HS codes based on user's search history

**Parameters:**
- `context_codes` (optional): List of recently searched codes
- `top_k` (optional, default=10): Number of recommendations

**Authentication:** JWT Bearer token

**Response:**
```json
{
  "recommendations": [
    {
      "hs_code": "5208.32",
      "description": "Woven fabrics of cotton, dyed, weighing > 200 g/m²",
      "source": "PK",
      "score": 0.87,
      "reason": "Semantically similar to your recent search"
    }
  ],
  "recommendation_id": 12346
}
```

#### 3. GET /v1/recommendations/tariff-optimization
**Purpose:** Find alternative HS code classifications with lower tariffs

**Parameters:**
- `hs_code` (required): Current HS code
- `cargo_value_usd` (required): Cargo value for savings calculation
- `source` (optional, default="PK"): "PK" or "US"

**Authentication:** JWT Bearer token

**Response:** See Tariff Optimization section above

#### 4. GET /v1/recommendations/routes
**Purpose:** Get personalized route recommendations

**Parameters:**
- `origin_city` (required)
- `destination_city` (required)
- `cargo_type` (required): FCL20, FCL40, LCL, or AIR
- `top_k` (optional, default=3)

**Authentication:** JWT Bearer token

**Response:** See Route Recommendations section above

#### 5. POST /v1/recommendations/{rec_id}/feedback
**Purpose:** Submit user feedback on a recommendation

**Parameters:**
- `rec_id` (path): ID of recommendation result

**Request Body:**
```json
{
  "selected_item_id": "5208.32",
  "selection_rank": 2,
  "was_helpful": true,
  "feedback_text": "Very useful suggestion!"
}
```

**Authentication:** JWT Bearer token

**Response:**
```json
{
  "message": "Feedback recorded successfully"
}
```

---

## Infrastructure Setup

### Prerequisites
- Docker & Docker Compose
- AWS Account (for S3)
- PostgreSQL database (existing)
- Memgraph/Memgraph (existing)
- Pinecone account (existing)

### Step 1: Redis + Celery Setup

#### Create `docker-compose.recommendation.yml`:
```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: trademate-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: trademate-celery-worker
    command: celery -A server.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - S3_MODEL_BUCKET=trademate-ml-models
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    volumes:
      - ./server:/app/server
      - /tmp/model_cache:/tmp/model_cache

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: trademate-celery-beat
    command: celery -A server.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./server:/app/server

  flower:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: trademate-flower
    command: celery -A server.celery_app flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - redis
    volumes:
      - ./server:/app/server

volumes:
  redis-data:
  celery-beat-data:
```

#### Start Services:
```bash
# Start all services
docker-compose -f docker-compose.yml -f docker-compose.recommendation.yml up -d

# View Celery monitoring dashboard
open http://localhost:5555

# Scale workers for high load
docker-compose -f docker-compose.recommendation.yml up -d --scale celery-worker=8
```

### Step 2: AWS S3 Setup

#### Create S3 Bucket:
```bash
aws s3 mb s3://trademate-ml-models --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket trademate-ml-models \
  --versioning-configuration Status=Enabled
```

#### IAM Policy (Minimal Permissions):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::trademate-ml-models",
        "arn:aws:s3:::trademate-ml-models/*"
      ]
    }
  ]
}
```

#### Environment Variables (`.env`):
```bash
# AWS S3
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AWS_REGION=us-east-1
S3_MODEL_BUCKET=trademate-ml-models

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Model cache
MODEL_CACHE_DIR=/tmp/model_cache
```

### Step 3: Database Migrations

```bash
# Run migrations to create new tables
python -m server.database.migrations

# Verify tables created
psql $DATABASE_URL -c "\dt user_interactions"
psql $DATABASE_URL -c "\dt recommendation_results"
psql $DATABASE_URL -c "\dt user_preferences"
psql $DATABASE_URL -c "\dt route_evaluation_history"
psql $DATABASE_URL -c "\dt model_metadata"
psql $DATABASE_URL -c "\dt ab_test_variants"
```

### Step 4: Install Dependencies

Update `requirements.txt`:
```
# Existing dependencies...

# Background Jobs
celery==5.4.0
redis==5.2.1
flower==2.0.1

# ML Libraries
implicit==0.7.2
lightgbm==4.5.0
scikit-learn==1.6.1

# AWS Integration
boto3==1.36.0

# Monitoring
prometheus-client==0.21.0
```

Install:
```bash
pip install -r requirements.txt
```

---

## Implementation Roadmap

### Week 1: Foundation & Infrastructure
**Goal:** Set up all infrastructure and data collection

**Tasks:**
- [ ] Create 6 new database models
- [ ] Run database migrations
- [ ] Set up Redis + Celery (Docker Compose)
- [ ] Set up AWS S3 bucket and IAM policies
- [ ] Implement interaction tracking in `agent/bot.py`
- [ ] Implement route evaluation history in `routes/routes.py`
- [ ] Create `server/celery_app.py` with Beat schedule
- [ ] Test data collection (verify records in DB)

**Deliverables:**
- All tables created and indexed
- Redis + Celery operational
- S3 bucket ready
- User interactions being logged

### Week 1-2: Content-Based Recommendations (All 4 Systems)
**Goal:** Launch all 4 recommendation systems using content-based approaches

**System 1: Documents**
- [ ] Create `server/services/document_recommender.py`
- [ ] Create `server/schemas/recommendation.py`
- [ ] Create `server/routes/recommendations.py`
- [ ] Add SSE event to `routes/chat.py`
- [ ] Test with sample conversations

**System 2: HS Codes**
- [ ] Create `server/services/hs_code_recommender.py`
- [ ] Implement content-based recommendations (Memgraph vector search)
- [ ] Add API endpoint
- [ ] Add SSE event to chat
- [ ] Test with sample HS code searches

**System 3: Tariff Optimization**
- [ ] Create `server/services/tariff_optimizer.py`
- [ ] Implement Memgraph query with duty comparison
- [ ] Add savings calculation
- [ ] Add legal disclaimer
- [ ] Add API endpoint
- [ ] Test with sample HS codes

**System 4: Routes**
- [ ] Create `server/services/route_recommender.py`
- [ ] Implement preference heuristics
- [ ] Integrate with existing route_engine
- [ ] Add API endpoint
- [ ] Test with sample route queries

**Deliverables:**
- All 4 recommendation systems live
- API endpoints functional
- SSE events streaming recommendations
- Content-based algorithms providing value

### Week 2-3: ML Training Pipeline
**Goal:** Build infrastructure for training and deploying ML models

**Tasks:**
- [ ] Create `server/ml/collaborative_filter.py`
- [ ] Create `server/ml/route_preference_model.py`
- [ ] Create `server/services/s3_model_store.py`
- [ ] Create `server/tasks/training_tasks.py`
- [ ] Create `server/scripts/train_initial_models.py`
- [ ] Implement model versioning logic
- [ ] Test model training locally (with sample data)
- [ ] Test S3 upload/download

**Deliverables:**
- ML training scripts functional
- S3 model storage working
- Celery tasks scheduled
- Ready to train when data available

### Week 3-4: ML Model Integration
**Goal:** Add collaborative filtering to HS Code and Route recommendations

**Tasks:**
- [ ] Train initial collaborative filtering model (requires 500+ interactions)
- [ ] Train initial route preference model (requires 200+ evaluations)
- [ ] Update `hs_code_recommender` to use hybrid approach
- [ ] Update `route_recommender` to use ML predictions
- [ ] Implement automatic fallback logic
- [ ] Create A/B testing framework
- [ ] Deploy ML models to 10% of users
- [ ] Monitor performance metrics

**Deliverables:**
- ML models trained and deployed
- A/B test running (10% ML vs 90% baseline)
- Performance dashboard showing metrics

### Week 4-5: Optimization & Monitoring
**Goal:** Optimize performance and set up comprehensive monitoring

**Tasks:**
- [ ] Add Redis caching for hot recommendations
- [ ] Optimize database queries (add covering indexes)
- [ ] Create Prometheus metrics
- [ ] Set up Grafana dashboards
- [ ] Create offline evaluation scripts
- [ ] Document runbooks for model retraining
- [ ] Create alerting for model performance degradation
- [ ] Performance testing (latency, throughput)

**Deliverables:**
- P95 latency < 200ms
- Monitoring dashboards operational
- Alerting configured
- Documentation complete

---

## Success Metrics

### Business Metrics (Primary)
| Metric | Target | Measurement |
|--------|--------|-------------|
| Recommendation CTR | > 5% | `clicks / impressions` |
| User Engagement Increase | +20% | Session duration, queries per session |
| Conversion Rate | +15% | Users finding relevant HS codes/routes faster |
| User Satisfaction | > 4.0/5.0 | Star ratings on recommendations |

### Technical Metrics (Performance)
| Metric | Target | Measurement |
|--------|--------|-------------|
| P50 Latency | < 100ms | Time to generate recommendations |
| P95 Latency | < 200ms | 95th percentile response time |
| P99 Latency | < 500ms | 99th percentile response time |
| Model Training Time | < 30 minutes | Weekly retraining job duration |
| Availability | > 99.5% | Uptime excluding maintenance |

### Quality Metrics (ML Model)
| Metric | Target | Measurement |
|--------|--------|-------------|
| Precision@5 | > 0.3 | % of top-5 recommendations clicked |
| Recall@10 | > 0.5 | % of relevant items in top-10 |
| NDCG@10 | > 0.4 | Normalized Discounted Cumulative Gain |
| Coverage | > 80% | % of items recommended at least once |
| Diversity | > 0.6 | Average pairwise dissimilarity |

### Data Quality Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Daily Active Users with Interactions | > 70% | % of DAU with >= 1 interaction |
| Interaction Data Completeness | > 95% | % of sessions with logged interactions |
| Feedback Rate | > 10% | % of recommendations with feedback |

---

## Risk Management

### Risk 1: Insufficient Data (Cold Start Problem)
**Impact:** High
**Probability:** High (new system)

**Mitigation Strategy:**
- ✅ Launch with content-based recommendations (no training data needed)
- ✅ Popularity-based fallback for new users
- ✅ Leverage existing semantic embeddings (Memgraph, Pinecone)
- ✅ Gradually transition to ML when data available (500+ interactions)

**Success Criteria:**
- All users receive recommendations from day 1
- Quality improves over time as data accumulates

### Risk 2: Model Performance Below Baseline
**Impact:** Medium
**Probability:** Medium

**Mitigation Strategy:**
- ✅ A/B test ML models vs content-based baseline
- ✅ Monitor CTR, user satisfaction, conversion rate
- ✅ Automatic rollback if ML underperforms
- ✅ Keep content-based as permanent fallback

**Success Criteria:**
- ML model CTR >= content-based CTR
- User satisfaction maintained or improved

### Risk 3: Performance Degradation (Latency)
**Impact:** High
**Probability:** Low

**Mitigation Strategy:**
- ✅ Redis caching for hot data
- ✅ Async recommendation generation (don't block chat)
- ✅ Pre-compute similarities weekly
- ✅ Database query optimization (indexes, covering indexes)
- ✅ Load testing before production deployment

**Success Criteria:**
- P95 latency < 200ms
- No increase in chat response time

### Risk 4: Model Staleness / Drift
**Impact:** Medium
**Probability:** Medium (over time)

**Mitigation Strategy:**
- ✅ Scheduled weekly retraining (Celery Beat)
- ✅ Monitor online metrics daily
- ✅ Alerting on performance degradation (> 20% CTR drop)
- ✅ Data drift detection (feature distribution shifts)

**Success Criteria:**
- Model performance stable over time
- Alerts triggered within 24 hours of degradation

### Risk 5: AWS S3 Cost Overruns
**Impact:** Low
**Probability:** Low

**Mitigation Strategy:**
- ✅ Small model sizes (<100MB per model)
- ✅ Lifecycle policies (delete old versions after 90 days)
- ✅ Local cache to minimize S3 requests
- ✅ Budget alerts on AWS account

**Estimated Cost:**
- Storage: ~$1/month (5 models × 50MB × $0.023/GB)
- Requests: ~$0.50/month (100 downloads/day)
- **Total: <$2/month**

---

## Next Steps

### Immediate Actions (This Week)
1. **Review & Approve** this document with stakeholders
2. **Set up development environment**:
   - Install Redis locally or via Docker
   - Configure AWS account and S3 bucket
   - Update `.env` with new variables
3. **Create database models** (6 new tables)
4. **Run migrations** and verify tables created

### Week 1 Priorities
1. Implement interaction tracking in `agent/bot.py`
2. Set up Celery + Redis infrastructure
3. Create `server/services/document_recommender.py` (simplest system)
4. Launch document recommendations to internal testing

### Success Checkpoints
- **Day 7:** All infrastructure operational, data being collected
- **Day 14:** All 4 content-based systems live, monitoring in place
- **Day 21:** First ML models trained (if data available)
- **Day 30:** A/B test results reviewed, full rollout decision

---

## Appendix

### Useful Commands

```bash
# Start all services
docker-compose -f docker-compose.yml -f docker-compose.recommendation.yml up -d

# View Celery task monitoring
open http://localhost:5555

# Check interaction data
psql $DATABASE_URL -c "SELECT interaction_type, COUNT(*) FROM user_interactions GROUP BY interaction_type"

# Check recommendation performance
psql $DATABASE_URL -c "SELECT recommendation_type, model_version, COUNT(*) as impressions, SUM(CASE WHEN selected_item_id IS NOT NULL THEN 1 ELSE 0 END) as clicks FROM recommendation_results WHERE created_at > NOW() - INTERVAL '7 days' GROUP BY recommendation_type, model_version"

# Train models manually
python -m server.scripts.train_initial_models

# View Celery logs
docker logs trademate-celery-worker -f
```

### File Structure

```
server/
├── models/
│   ├── interaction.py              # NEW
│   ├── recommendation.py           # NEW
│   ├── user_preference.py          # NEW
│   ├── route_evaluation_history.py # NEW
│   ├── model_metadata.py           # NEW
│   └── ab_test.py                  # NEW
├── services/
│   ├── document_recommender.py     # NEW
│   ├── hs_code_recommender.py      # NEW
│   ├── tariff_optimizer.py         # NEW
│   ├── route_recommender.py        # NEW
│   ├── s3_model_store.py           # NEW
│   └── ab_testing.py               # NEW
├── routes/
│   └── recommendations.py          # NEW
├── schemas/
│   └── recommendation.py           # NEW
├── ml/
│   ├── collaborative_filter.py     # NEW
│   ├── content_based_filter.py     # NEW
│   └── route_preference_model.py   # NEW
├── tasks/
│   ├── __init__.py                 # NEW
│   ├── training_tasks.py           # NEW
│   └── preference_tasks.py         # NEW
├── scripts/
│   ├── train_initial_models.py     # NEW
│   └── evaluate_recommendations.py # NEW
├── monitoring/
│   └── recommendation_metrics.py   # NEW
├── tests/
│   ├── test_recommendations.py     # NEW
│   └── test_recommendation_endpoints.py # NEW
└── celery_app.py                   # NEW
```

---

**Document Version:** 1.0
**Last Updated:** 2026-04-22
**Status:** ✅ Approved - Ready for Implementation
**Next Review:** After Week 2 (Post-Launch)
