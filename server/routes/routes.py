import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from schemas.routes import RouteEvaluationRequest, RouteEvaluationResponse
from security.security import decode_access_token
from services.route_engine import evaluate_routes

logger = logging.getLogger(__name__)

router  = APIRouter(prefix="/v1", tags=["routes"])
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


@router.post(
    "/routes/evaluate",
    response_model=RouteEvaluationResponse,
    summary="Evaluate all viable Pakistan → USA shipping routes",
)
def evaluate(
    body: RouteEvaluationRequest,
    user_id: int = Depends(_get_current_user_id),
):
    """
    Given origin city, destination, cargo details, and cost/time preference,
    returns all viable routes ranked by a weighted score.

    The `cost_weight` parameter (0–1) controls the optimization:
      - 0.0 → minimize transit time (fastest route wins)
      - 1.0 → minimize total cost (cheapest route wins)
      - 0.5 → balanced (default)
    """
    try:
        logger.info("[ROUTES] user_id=%d  %s→%s  %s  $%.0f",
                    user_id, body.origin_city, body.destination_city,
                    body.cargo_type, body.cargo_value_usd)
        return evaluate_routes(body, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/routes/options",
    summary="Return available origin cities, destination cities, and cargo types",
)
def get_options(_user_id: int = Depends(_get_current_user_id)):
    """Returns the valid input options for the route evaluation form."""
    from services.route_engine import (
        _DESTINATION_CHARGES,
        _INLAND_ORIGINS,
    )
    return {
        "origin_cities":      sorted(_INLAND_ORIGINS.keys()),
        "destination_cities": sorted(_DESTINATION_CHARGES.keys()),
        "cargo_types": [
            {"value": "FCL_20",  "label": "FCL 20' (Full Container)"},
            {"value": "FCL_40",  "label": "FCL 40' (Full Container)"},
            {"value": "FCL_40HC","label": "FCL 40' HC (High Cube)"},
            {"value": "LCL",     "label": "LCL (Less than Container Load)"},
            {"value": "AIR",     "label": "Air Freight"},
        ],
    }
