from typing import Literal, Optional
from pydantic import BaseModel, Field


# ── Request ────────────────────────────────────────────────────────────────────

# Trade direction. The two route graphs (server/data/pk_usa_routes.json and
# server/data/us_pk_routes.json) are mirrors of each other with country-
# specific origin/destination fees, customs duty tables, and government levies.
RouteDirection = Literal["PK_TO_US", "US_TO_PK"]


class RouteEvaluationRequest(BaseModel):
    direction: RouteDirection = Field(
        default="PK_TO_US",
        description=(
            "Trade direction. PK_TO_US = exporting from Pakistan to the USA "
            "(default; uses US import duties + HMF/MPF). US_TO_PK = exporting "
            "from the USA to Pakistan (uses Pakistani import duties + "
            "withholding tax + Pakistani port fees)."
        ),
    )
    origin_city: str = Field(
        ...,
        description=(
            "City of origin. Must be in Pakistan when direction=PK_TO_US, "
            "or in the USA when direction=US_TO_PK."
        ),
        examples=["Karachi", "Lahore", "Los Angeles", "New York"],
    )
    destination_city: str = Field(
        ...,
        description=(
            "Destination city. Must be in the USA when direction=PK_TO_US, "
            "or in Pakistan when direction=US_TO_PK."
        ),
        examples=["Los Angeles", "New York", "Karachi", "Lahore"],
    )
    cargo_type: str = Field(
        ...,
        description="FCL_20 | FCL_40 | FCL_40HC | LCL | AIR",
        examples=["FCL_40HC"]
    )
    cargo_value_usd: float = Field(
        ...,
        gt=0,
        description="Total declared cargo value in USD"
    )
    hs_code: Optional[str] = Field(
        None,
        description="HS code (first 2–6 digits) for duty calculation",
        examples=["6109", "6204"]
    )
    # Required for LCL
    cargo_volume_cbm: Optional[float] = Field(
        None,
        gt=0,
        description="Cargo volume in CBM (required for LCL)"
    )
    # Required for AIR
    cargo_weight_kg: Optional[float] = Field(
        None,
        gt=0,
        description="Cargo weight in kg (required for AIR)"
    )
    # Cargo dimensions for air volumetric weight (optional)
    cargo_length_cm: Optional[float] = Field(None, gt=0)
    cargo_width_cm: Optional[float] = Field(None, gt=0)
    cargo_height_cm: Optional[float] = Field(None, gt=0)
    # Number of containers (FCL only — multiplies per-container costs)
    container_count: int = Field(
        default=1,
        ge=1,
        description="Number of FCL containers. Freight, THC, and drayage are multiplied by this value."
    )
    # Optimization preference: 0 = minimize time, 1 = minimize cost
    cost_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="0 = prioritize speed, 1 = prioritize cost"
    )


# ── Response ───────────────────────────────────────────────────────────────────

class CostBreakdown(BaseModel):
    inland_haulage:        float
    origin_thc:            float
    ocean_air_freight_min: float
    ocean_air_freight_max: float
    transshipment_thc:     float
    fixed_charges:         float
    destination_thc:       float
    customs_broker:        float
    drayage:               float
    hmf:                   float
    mpf:                   float
    import_duty:           float
    total_min:             float
    total_max:             float


class TransitBreakdown(BaseModel):
    inland_days:       float
    sea_air_days_min:  int
    sea_air_days_max:  int
    port_processing:   int
    customs_days:      int
    total_min:         float
    total_max:         float


class RouteAlert(BaseModel):
    level:   str   # "info" | "warning" | "critical"
    message: str


class RouteResult(BaseModel):
    id:                str
    name:              str
    mode:              str
    origin_port:       str
    hubs:              list[str]
    destination_ports: list[str]
    carriers:          list[str]
    frequency_per_week: int
    reliability_score: float
    cost:              CostBreakdown
    transit:           TransitBreakdown
    score:             float          # normalized weighted score (lower = better)
    tag:               Optional[str]  # "cheapest" | "fastest" | "balanced" | None
    alerts:            list[RouteAlert]
    rate_source:       str = "static" # "live" | "static"


class RouteEvaluationResponse(BaseModel):
    direction:        RouteDirection = "PK_TO_US"
    origin_city:      str
    destination_city: str
    cargo_type:       str
    cargo_value_usd:  float
    hs_code:          Optional[str]
    duty_rate_pct:    float
    cost_weight:      float
    routes:           list[RouteResult]
    recommended:      dict[str, str]   # {cheapest, fastest, balanced} → route id
    disclaimer:       str
