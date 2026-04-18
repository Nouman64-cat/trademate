"""
services/route_engine.py — Trade Route Evaluation Engine

Evaluates all viable Pakistan → USA shipping routes for a given cargo request.

Algorithm:
  1. Load static route graph (data/pk_usa_routes.json)
  2. Filter routes compatible with cargo_type and destination_city
  3. Calculate full cost breakdown and transit time for each route
  4. Normalize cost and time across all routes → [0, 1]
  5. Compute weighted score: α × cost_norm + (1 - α) × time_norm
  6. Sort by score, tag cheapest / fastest / balanced
  7. Return ranked RouteResult list
"""

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from schemas.routes import (
    CostBreakdown,
    RouteAlert,
    RouteEvaluationRequest,
    RouteEvaluationResponse,
    RouteResult,
    TransitBreakdown,
)
from services import freightos_client
from services.freightos_client import FreightosUnavailable

logger = logging.getLogger(__name__)

# ── Load static data ───────────────────────────────────────────────────────────

_DATA_PATH = Path(__file__).parent.parent / "data" / "pk_usa_routes.json"

with open(_DATA_PATH, encoding="utf-8") as _f:
    _DATA = json.load(_f)

_ROUTES            = _DATA["routes"]
_INLAND_ORIGINS    = _DATA["inland_origins"]
_DESTINATION_CHARGES = _DATA["destination_charges"]
_HS_DUTY_RATES     = _DATA["hs_duty_rates"]
_FIXED             = _DATA["fixed_charges"]

# ── Destination → region mapping (for route filtering) ────────────────────────

_DEST_REGION: dict[str, str] = {
    d: info["region"] for d, info in _DESTINATION_CHARGES.items()
}


# ── Duty rate lookup ───────────────────────────────────────────────────────────

def _get_duty_rate(hs_code: str | None) -> float:
    """Return import duty rate (0–1) for a given HS code chapter."""
    if not hs_code:
        return _HS_DUTY_RATES["default"]
    chapter = hs_code.strip().lstrip("0")[:2].zfill(2)
    return _HS_DUTY_RATES.get(chapter, _HS_DUTY_RATES["default"])


# ── Chargeable weight for air (IATA volumetric formula) ───────────────────────

def _chargeable_weight_kg(
    actual_kg: float,
    length_cm: float | None,
    width_cm: float | None,
    height_cm: float | None,
) -> float:
    """Return the greater of actual weight and IATA volumetric weight."""
    if length_cm and width_cm and height_cm:
        volumetric = (length_cm * width_cm * height_cm) / 6000
        return max(actual_kg, volumetric)
    return actual_kg


# ── Route filter ───────────────────────────────────────────────────────────────

def _route_is_applicable(route: dict, cargo_type: str, dest_region: str) -> bool:
    """Return True if this route can carry the cargo_type to the destination region."""
    mode = route["mode"]

    # Air routes only accept AIR cargo
    if mode == "AIR" and cargo_type != "AIR":
        return False
    # Sea/multimodal routes don't accept AIR cargo type
    if mode == "SEA" and cargo_type == "AIR":
        return False

    # LCL must have LCL_CBM rates defined
    if cargo_type == "LCL" and "LCL_CBM" not in route["freight_rates"]:
        return False
    if cargo_type == "AIR" and "AIR_KG" not in route["freight_rates"]:
        return False

    # Destination region filter
    route_region = route["destination_region"]
    if route_region == "BOTH":
        return True
    if dest_region == "USWC" and route_region != "USWC":
        return False
    if dest_region == "USEC" and route_region == "USWC":
        return False
    # USMW (Chicago) accepts USWC ports with inland rail — allow USWC routes
    if dest_region == "USMW":
        return True

    return True


# ── Cost calculator ────────────────────────────────────────────────────────────

def _calculate_cost(
    route: dict,
    req: RouteEvaluationRequest,
    inland: dict,
    dest: dict,
    duty_rate: float,
    chargeable_kg: float,
) -> CostBreakdown:
    ct = req.cargo_type
    rates = route["freight_rates"]

    # 1. Inland haulage
    if req.cargo_type == "AIR":
        inland_cost = inland["to_air_port_cost_usd"]
    else:
        inland_cost = inland["to_sea_port_cost_usd"]

    # 2. Origin THC (sea only)
    origin_thc = route["origin_thc_usd"] if ct != "AIR" else 0

    # 3. Ocean / air freight
    if ct == "FCL_20":
        fr = rates["FCL_20"]
        freight_min, freight_max = fr["min"], fr["max"]
    elif ct == "FCL_40":
        fr = rates["FCL_40"]
        freight_min, freight_max = fr["min"], fr["max"]
    elif ct == "FCL_40HC":
        fr = rates["FCL_40HC"]
        freight_min, freight_max = fr["min"], fr["max"]
    elif ct == "LCL":
        cbm = req.cargo_volume_cbm or 1.0
        fr = rates["LCL_CBM"]
        freight_min = fr["min"] * cbm
        freight_max = fr["max"] * cbm
    else:  # AIR
        fr = rates["AIR_KG"]
        freight_min = fr["min"] * chargeable_kg
        freight_max = fr["max"] * chargeable_kg

    # 4. Transshipment THC (sea only, per hub)
    n_hubs = len([h for h in route["hubs"] if "Canal" not in h])  # canals don't charge THC
    trans_thc = route["transshipment_thc_usd"] * n_hubs if ct != "AIR" else 0

    # 5. Fixed charges (ISF, B/L, seal, ISPS, docs)
    fixed = (
        _FIXED["isf_filing_usd"]
        + _FIXED["bl_fee_usd"]
        + _FIXED["seal_fee_usd"]
        + _FIXED["isps_surcharge_usd"]
        + _FIXED["documentation_usd"]
    ) if ct != "AIR" else _FIXED["documentation_usd"]

    # 6. Destination charges
    dest_thc    = dest["thc_usd"] if ct != "AIR" else 0
    broker      = dest["customs_broker_usd"]
    drayage     = dest["drayage_usd"]

    # 7. Government fees (on cargo value)
    hmf = round(req.cargo_value_usd * _FIXED["hmf_rate"], 2)
    mpf_raw = req.cargo_value_usd * _FIXED["mpf_rate"]
    mpf = round(max(_FIXED["mpf_min_usd"], min(_FIXED["mpf_max_usd"], mpf_raw)), 2)

    # 8. Import duty
    import_duty = round(req.cargo_value_usd * duty_rate, 2)

    # ── Totals ──
    fixed_sum = origin_thc + trans_thc + fixed + dest_thc + broker + drayage + hmf + mpf + import_duty + inland_cost
    total_min = round(freight_min + fixed_sum, 2)
    total_max = round(freight_max + fixed_sum, 2)

    return CostBreakdown(
        inland_haulage=inland_cost,
        origin_thc=origin_thc,
        ocean_air_freight_min=round(freight_min, 2),
        ocean_air_freight_max=round(freight_max, 2),
        transshipment_thc=trans_thc,
        fixed_charges=fixed,
        destination_thc=dest_thc,
        customs_broker=broker,
        drayage=drayage,
        hmf=hmf,
        mpf=mpf,
        import_duty=import_duty,
        total_min=total_min,
        total_max=total_max,
    )


# ── Transit calculator ─────────────────────────────────────────────────────────

def _calculate_transit(
    route: dict,
    inland: dict,
    cargo_type: str,
) -> TransitBreakdown:
    if cargo_type == "AIR":
        inland_days = inland["to_air_port_days"]
    else:
        inland_days = inland["to_sea_port_days"]

    sea_min = route["transit_days"]["min"]
    sea_max = route["transit_days"]["max"]

    # Port processing: ~1 day for air, 2 days for sea
    port_processing = 1 if cargo_type == "AIR" else 2

    # US customs clearance
    customs_days = 1 if cargo_type == "AIR" else 2

    total_min = round(inland_days + sea_min + port_processing + customs_days, 1)
    total_max = round(inland_days + sea_max + port_processing + customs_days + 1, 1)

    return TransitBreakdown(
        inland_days=inland_days,
        sea_air_days_min=sea_min,
        sea_air_days_max=sea_max,
        port_processing=port_processing,
        customs_days=customs_days,
        total_min=total_min,
        total_max=total_max,
    )


# ── Freightos concurrent / deduplicated pre-fetch ─────────────────────────────

def _rate_cache_key(route: dict, req: RouteEvaluationRequest, chargeable_kg: float) -> tuple:
    """Build a hashable key so identical port-pair queries share one API call."""
    weight = chargeable_kg or req.cargo_weight_kg or 15000
    return (route["origin_port"], tuple(route["destination_ports"]), req.cargo_type, weight)


def _fetch_rate(route: dict, req: RouteEvaluationRequest, chargeable_kg: float):
    """Thread-pool worker: returns (route_id, FreightosRate|None, exception|None)."""
    try:
        rate = freightos_client.get_rate(
            origin_port=route["origin_port"],
            dest_port=route["destination_ports"],
            cargo_type=req.cargo_type,
            cargo_volume_cbm=req.cargo_volume_cbm,
            cargo_weight_kg=req.cargo_weight_kg,
            chargeable_kg=chargeable_kg if req.cargo_type == "AIR" else None,
        )
        return route["id"], rate, None
    except FreightosUnavailable as exc:
        return route["id"], None, exc


def _prefetch_live_rates(
    applicable_routes: list,
    req: RouteEvaluationRequest,
    chargeable_kg: float,
) -> dict:
    """
    Fetch live Freightos rates for all applicable routes concurrently.
    Routes that share the same (origin_port, dest_ports, cargo_type, weight)
    are deduplicated — one HTTP call serves all of them.

    Returns a dict mapping route_id → FreightosRate (absent if unavailable).
    """
    # Group routes by cache key; only the first representative makes the call
    key_to_route_ids: dict[tuple, list[str]] = {}
    key_to_repr: dict[tuple, dict] = {}
    for route in applicable_routes:
        key = _rate_cache_key(route, req, chargeable_kg)
        key_to_route_ids.setdefault(key, []).append(route["id"])
        key_to_repr.setdefault(key, route)

    unique_keys = list(key_to_repr.keys())
    logger.info("[ROUTE] %d applicable routes → %d unique Freightos queries (concurrent)",
                len(applicable_routes), len(unique_keys))

    live_rates: dict[str, "freightos_client.FreightosRate"] = {}

    with ThreadPoolExecutor(max_workers=len(unique_keys)) as pool:
        future_to_key = {
            pool.submit(_fetch_rate, key_to_repr[k], req, chargeable_kg): k
            for k in unique_keys
        }
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            route_id, rate, exc = future.result()
            if rate is not None:
                for rid in key_to_route_ids[key]:
                    live_rates[rid] = rate
                logger.info("[ROUTE] Live rate (%s): $%.0f–$%.0f  (shared by %s)",
                            route_id, rate.min_usd, rate.max_usd,
                            key_to_route_ids[key])
            else:
                logger.warning("[ROUTE] Freightos unavailable (%s): %s", route_id, exc)

    return live_rates


# ── Main evaluation function ───────────────────────────────────────────────────

def evaluate_routes(req: RouteEvaluationRequest) -> RouteEvaluationResponse:
    # Validate origin
    inland = _INLAND_ORIGINS.get(req.origin_city)
    if not inland:
        available = list(_INLAND_ORIGINS.keys())
        raise ValueError(f"Unknown origin city '{req.origin_city}'. Available: {available}")

    # Validate destination
    dest = _DESTINATION_CHARGES.get(req.destination_city)
    if not dest:
        available = list(_DESTINATION_CHARGES.keys())
        raise ValueError(f"Unknown destination city '{req.destination_city}'. Available: {available}")

    dest_region = dest["region"]
    duty_rate   = _get_duty_rate(req.hs_code)

    # Chargeable weight for air
    chargeable_kg = 0.0
    if req.cargo_type == "AIR":
        if not req.cargo_weight_kg:
            raise ValueError("cargo_weight_kg is required for AIR shipments")
        chargeable_kg = _chargeable_weight_kg(
            req.cargo_weight_kg,
            req.cargo_length_cm,
            req.cargo_width_cm,
            req.cargo_height_cm,
        )

    logger.info(
        "[ROUTE] Evaluating %s→%s  cargo=%s  value=$%.0f  hs=%s  α=%.2f",
        req.origin_city, req.destination_city, req.cargo_type,
        req.cargo_value_usd, req.hs_code or "N/A", req.cost_weight,
    )

    # ── Pre-fetch live rates concurrently (deduplicated) ──────────────────────
    applicable_routes = [r for r in _ROUTES if _route_is_applicable(r, req.cargo_type, dest_region)]
    live_rates = _prefetch_live_rates(applicable_routes, req, chargeable_kg)

    # ── Build route results ────────────────────────────────────────────────────
    results: list[RouteResult] = []

    for route in applicable_routes:
        cost    = _calculate_cost(route, req, inland, dest, duty_rate, chargeable_kg)
        transit = _calculate_transit(route, inland, req.cargo_type)
        alerts  = [RouteAlert(**a) for a in route["alerts"]]
        rate_source = "live"

        live = live_rates.get(route["id"])
        if live is not None:
            # Replace static freight with live quote (keep all other charges unchanged)
            fixed_sum = (
                cost.inland_haulage
                + cost.origin_thc
                + cost.transshipment_thc
                + cost.fixed_charges
                + cost.destination_thc
                + cost.customs_broker
                + cost.drayage
                + cost.hmf
                + cost.mpf
                + cost.import_duty
            )
            cost = CostBreakdown(
                inland_haulage=cost.inland_haulage,
                origin_thc=cost.origin_thc,
                ocean_air_freight_min=round(live.min_usd, 2),
                ocean_air_freight_max=round(live.max_usd, 2),
                transshipment_thc=cost.transshipment_thc,
                fixed_charges=cost.fixed_charges,
                destination_thc=cost.destination_thc,
                customs_broker=cost.customs_broker,
                drayage=cost.drayage,
                hmf=cost.hmf,
                mpf=cost.mpf,
                import_duty=cost.import_duty,
                total_min=round(live.min_usd + fixed_sum, 2),
                total_max=round(live.max_usd + fixed_sum, 2),
            )
            rate_source = "live"

        results.append(RouteResult(
            id=route["id"],
            name=route["name"],
            mode=route["mode"],
            origin_port=route["origin_port"],
            hubs=route["hubs"],
            destination_ports=route["destination_ports"],
            carriers=route["carriers"],
            frequency_per_week=route["frequency_per_week"],
            reliability_score=route["reliability_score"],
            cost=cost,
            transit=transit,
            score=0.0,   # filled below
            tag=None,
            alerts=alerts,
            rate_source=rate_source,
        ))

    if not results:
        raise ValueError("No viable routes found for the given parameters.")

    # ── Normalize and score ────────────────────────────────────────────────────
    costs_mid = [(r.cost.total_min + r.cost.total_max) / 2 for r in results]
    times_mid = [(r.transit.total_min + r.transit.total_max) / 2 for r in results]

    min_cost, max_cost = min(costs_mid), max(costs_mid)
    min_time, max_time = min(times_mid), max(times_mid)

    cost_range = max_cost - min_cost or 1
    time_range = max_time - min_time or 1

    alpha = req.cost_weight  # 1 = minimize cost, 0 = minimize time

    for i, r in enumerate(results):
        cost_norm = (costs_mid[i] - min_cost) / cost_range
        time_norm = (times_mid[i] - min_time) / time_range
        r.score = round(alpha * cost_norm + (1 - alpha) * time_norm, 4)

    # ── Tag cheapest / fastest / balanced ─────────────────────────────────────
    cheapest_id = results[costs_mid.index(min(costs_mid))].id
    fastest_id  = results[times_mid.index(min(times_mid))].id
    # Balanced = best score at α = 0.5
    balanced_scores = [
        0.5 * (costs_mid[i] - min_cost) / cost_range
        + 0.5 * (times_mid[i] - min_time) / time_range
        for i in range(len(results))
    ]
    balanced_id = results[balanced_scores.index(min(balanced_scores))].id

    for r in results:
        tags = []
        if r.id == cheapest_id:
            tags.append("cheapest")
        if r.id == fastest_id:
            tags.append("fastest")
        if r.id == balanced_id and r.id not in (cheapest_id, fastest_id):
            tags.append("balanced")
        r.tag = tags[0] if tags else None

    # Sort by user-weighted score ascending
    results.sort(key=lambda r: r.score)

    logger.info(
        "[ROUTE] %d routes evaluated. Cheapest=%s  Fastest=%s  Balanced=%s",
        len(results), cheapest_id, fastest_id, balanced_id,
    )

    return RouteEvaluationResponse(
        origin_city=req.origin_city,
        destination_city=req.destination_city,
        cargo_type=req.cargo_type,
        cargo_value_usd=req.cargo_value_usd,
        hs_code=req.hs_code,
        duty_rate_pct=round(duty_rate * 100, 2),
        cost_weight=req.cost_weight,
        routes=results,
        recommended={
            "cheapest": cheapest_id,
            "fastest":  fastest_id,
            "balanced": balanced_id,
        },
        disclaimer=(
            "All cost and transit time figures are indicative estimates for planning purposes only. "
            "Actual freight rates, duties, and transit times may vary. "
            "Obtain binding quotes from a licensed freight forwarder before making shipping decisions."
        ),
    )
