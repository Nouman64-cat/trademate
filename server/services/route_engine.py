"""
services/route_engine.py — Trade Route Evaluation Engine

Evaluates all viable shipping routes for a given cargo request.
Currently supports PK_TO_US (Pakistan → USA) direction.
Data source: data/pk_usa_routes.json

Algorithm (per request):
  1. Pick the route graph for req.direction
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
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from schemas.routes import (
    CostBreakdown,
    RouteAlert,
    RouteDirection,
    RouteEvaluationRequest,
    RouteEvaluationResponse,
    RouteResult,
    TransitBreakdown,
)
from services import freightos_client
from services.freightos_client import FreightosUnavailable

logger = logging.getLogger(__name__)

# ── Direction-specific route graph ─────────────────────────────────────────────
#
# Each direction loads its own data file with its own routes, inland origins,
# destination charges, duty rates, and per-shipment fixed fees. The cost
# calculator pulls everything it needs from the active RouteGraph so the
# calculation logic itself stays direction-agnostic.

_DATA_DIR = Path(__file__).parent.parent / "data"

_PK_TO_US_PATH = _DATA_DIR / "pk_usa_routes.json"
_US_TO_PK_PATH = _DATA_DIR / "us_pk_routes.json"


@dataclass(frozen=True)
class _RouteGraph:
    direction: RouteDirection
    routes: list
    inland_origins: dict
    destination_charges: dict
    hs_duty_rates: dict
    fixed: dict
    # Air-gateway mapping for inland origin cities → (port_code, gateway_city)
    air_gateway_by_origin: dict[str, tuple[str, str]]
    # City names that may appear verbatim in static route names — used for
    # localising the displayed route name when the user picks a non-default city.
    origin_city_names_in_route_names: list[str]
    destination_city_names_in_route_names: list[str]


def _load_graph(path: Path,
                direction: RouteDirection,
                air_gateway_by_origin: dict[str, tuple[str, str]],
                origin_cities_in_names: list[str],
                destination_cities_in_names: list[str]) -> Optional[_RouteGraph]:
    """Load a direction's route graph from disk.

    Returns None (and logs a warning) if the data file is missing or malformed,
    so a single missing JSON cannot prevent the server from starting. The
    affected direction will be reported as unsupported at request time, while
    other directions continue to serve traffic normally.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        logger.warning(
            "[ROUTE] %s graph file not found at %s — direction will be disabled. "
            "Live Freightos rates require route topology (ports, hubs, charges) "
            "that the API does not provide; restore the JSON to re-enable.",
            direction, path,
        )
        return None
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning(
            "[ROUTE] Failed to load %s graph from %s: %s — direction disabled.",
            direction, path, exc,
        )
        return None
    return _RouteGraph(
        direction=direction,
        routes=data["routes"],
        inland_origins=data["inland_origins"],
        destination_charges=data["destination_charges"],
        hs_duty_rates=data["hs_duty_rates"],
        fixed=data["fixed_charges"],
        air_gateway_by_origin=air_gateway_by_origin,
        origin_city_names_in_route_names=origin_cities_in_names,
        destination_city_names_in_route_names=destination_cities_in_names,
    )


# Pakistan air-gateway mapping — for PK_TO_US: where the user's PK origin city
# trucks to. Reused by US_TO_PK as the destination-side mapping.
_PK_AIR_GATEWAY: dict[str, tuple[str, str]] = {
    "Karachi":    ("KHI", "Karachi"),
    "Lahore":     ("LHE", "Lahore"),
    "Faisalabad": ("LHE", "Lahore"),     # FSL has no wide-body intl cargo; trucks to LHE
    "Sialkot":    ("SKT", "Sialkot"),
    "Islamabad":  ("ISB", "Islamabad"),
    "Peshawar":   ("ISB", "Islamabad"),  # PEW intl cargo is limited; trucks to ISB
    "Multan":     ("LHE", "Lahore"),
}

_US_CITY_NAMES = [
    "New York", "Los Angeles", "Long Beach", "Chicago",
    "Miami", "Savannah", "Seattle", "Baltimore",
    "Houston", "Dallas", "Atlanta",
    "US Both Coasts",
]
_PK_CITY_NAMES = [
    "Karachi", "Lahore", "Sialkot", "Islamabad",
    "Faisalabad", "Multan", "Peshawar",
]

# US air-gateway mapping — for US_TO_PK: where the US origin city ships air cargo from.
_US_AIR_GATEWAY: dict[str, tuple[str, str]] = {
    "Los Angeles":  ("USLAX", "Los Angeles"),
    "Long Beach":   ("USLAX", "Los Angeles"),   # LGB cargo routes through LAX
    "New York":     ("USJFK", "New York"),
    "Chicago":      ("USORD", "Chicago"),
    "Miami":        ("USMIA", "Miami"),
    "Savannah":     ("USATL", "Atlanta"),        # SAV air cargo trucks to ATL
    "Seattle":      ("USSEA", "Seattle"),
    "Houston":      ("USIAH", "Houston"),
    "Dallas":       ("USDFW", "Dallas"),
    "Atlanta":      ("USATL", "Atlanta"),
    "Baltimore":    ("USBWI", "Baltimore"),
}


_GRAPHS: dict[RouteDirection, _RouteGraph] = {}
for _direction, _path, _gateway, _origin_names, _dest_names in (
    ("PK_TO_US", _PK_TO_US_PATH, _PK_AIR_GATEWAY, _PK_CITY_NAMES, _US_CITY_NAMES),
    ("US_TO_PK", _US_TO_PK_PATH, _US_AIR_GATEWAY, _US_CITY_NAMES, _PK_CITY_NAMES),
):
    _g = _load_graph(_path, _direction, _gateway, _origin_names, _dest_names)
    if _g is not None:
        _GRAPHS[_direction] = _g

if not _GRAPHS:
    logger.warning(
        "[ROUTE] No route graphs loaded. /v1/routes/* endpoints will return 400 "
        "until at least one direction's JSON is provided in server/data/."
    )


# ── Backward-compat module-level aliases ──────────────────────────────────────
# The existing `/v1/routes/options` endpoint and a few other call sites read
# these directly. They reflect the PK_TO_US graph when available; otherwise
# they remain empty so the server still imports cleanly.

_PK_TO_US_GRAPH = _GRAPHS.get("PK_TO_US")
_ROUTES              = _PK_TO_US_GRAPH.routes              if _PK_TO_US_GRAPH else []
_INLAND_ORIGINS      = _PK_TO_US_GRAPH.inland_origins      if _PK_TO_US_GRAPH else {}
_DESTINATION_CHARGES = _PK_TO_US_GRAPH.destination_charges if _PK_TO_US_GRAPH else {}
_HS_DUTY_RATES       = _PK_TO_US_GRAPH.hs_duty_rates       if _PK_TO_US_GRAPH else {"default": 0.0}
_FIXED               = _PK_TO_US_GRAPH.fixed              if _PK_TO_US_GRAPH else {}


def get_options(direction: RouteDirection = "PK_TO_US") -> dict:
    """Return the available origin/destination cities for a given direction.

    Used by /v1/routes/options to populate the route-evaluation form.
    """
    g = _GRAPHS.get(direction)
    if g is None:
        raise ValueError(f"Direction '{direction}' is not supported. Supported: {list(_GRAPHS.keys())}")
    return {
        "direction": direction,
        "origin_cities": sorted(g.inland_origins.keys()),
        "destination_cities": sorted(g.destination_charges.keys()),
    }


def _localize_route_name(name: str, replacement_city: str, source_cities: list[str]) -> str:
    """Replace a hardcoded city name in a route name with the user's actual choice.

    `source_cities` is the list of city names that may appear in the static
    route-name templates (US cities for PK_TO_US, PK cities for US_TO_PK).
    """
    target = replacement_city.title()
    for city in source_cities:
        if city in name and city.lower() != target.lower():
            return name.replace(city, target, 1)
    return name


def _localize_air_route(route: dict, origin_city: str, graph: _RouteGraph) -> dict:
    """Return a shallow copy of an AIR route with origin_port and displayed
    origin city rewritten to the user's nearest air gateway for the active
    direction."""
    default_pair = next(iter(graph.air_gateway_by_origin.values()), ("", ""))
    port_code, city_name = graph.air_gateway_by_origin.get(origin_city, default_pair)
    if not port_code:
        return route
    localized = dict(route)
    localized["origin_port"] = port_code
    name = route.get("name", "")
    for existing in graph.origin_city_names_in_route_names:
        if name.startswith(f"{existing} →") and existing != city_name:
            localized["name"] = name.replace(existing, city_name, 1)
            break
    return localized


# ── Duty rate lookup ───────────────────────────────────────────────────────────

def _get_duty_rate(hs_code: str | None, graph: _RouteGraph) -> float:
    """Return import duty rate (0–1) for a given HS code chapter on the
    destination side of the active direction."""
    if not hs_code:
        return graph.hs_duty_rates["default"]
    chapter = hs_code.strip().lstrip("0")[:2].zfill(2)
    return graph.hs_duty_rates.get(chapter, graph.hs_duty_rates["default"])


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

# Region-pair compatibility table for sea/multimodal routes per direction.
# Maps (direction, dest_region) → set of route_region values that can serve it.
# AIR routes are filtered separately: they require an exact region match.
_SEA_REGION_COMPATIBILITY: dict[tuple[RouteDirection, str], set[str]] = {
    # Pakistan → USA: West-coast destinations only get USWC sea service;
    # East-coast destinations don't get USWC; Midwest accepts everything via rail.
    ("PK_TO_US", "USWC"): {"USWC", "BOTH"},
    ("PK_TO_US", "USEC"): {"USEC", "BOTH"},
    ("PK_TO_US", "USMW"): {"USWC", "USEC", "BOTH"},  # rail to Chicago either coast
    # USA → Pakistan: every PK destination is reachable from any incoming
    # sea hub — the country is small enough that inland drayage covers it.
    ("US_TO_PK", "PKSOUTH"):   {"PKSOUTH", "BOTH"},
    ("US_TO_PK", "PKCENTRAL"): {"PKSOUTH", "PKCENTRAL", "BOTH"},
    ("US_TO_PK", "PKNORTH"):   {"PKSOUTH", "PKCENTRAL", "PKNORTH", "BOTH"},
}


def _route_is_applicable(
    route: dict,
    cargo_type: str,
    dest_region: str,
    direction: RouteDirection,
) -> bool:
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

    route_region = route["destination_region"]
    if route_region == "BOTH":
        return True

    # AIR routes fly into a specific airport — exact region match only.
    if cargo_type == "AIR":
        return route_region == dest_region

    # SEA/LCL: consult the per-direction compatibility table.
    allowed = _SEA_REGION_COMPATIBILITY.get((direction, dest_region))
    if allowed is None:
        # Unknown destination region — fall back to permissive matching so a
        # mis-tagged data file doesn't lose all routes silently.
        return True
    return route_region in allowed


# ── Cost calculator ────────────────────────────────────────────────────────────

def _calculate_cost(
    route: dict,
    req: RouteEvaluationRequest,
    inland: dict,
    dest: dict,
    duty_rate: float,
    chargeable_kg: float,
    graph: _RouteGraph,
) -> CostBreakdown:
    ct = req.cargo_type
    rates = route["freight_rates"]
    fixed_cfg = graph.fixed
    # FCL: costs that scale per container; AIR/LCL: always 1 unit
    n_units = req.container_count if ct.startswith("FCL") else 1

    # 1. Inland haulage (per container)
    if req.cargo_type == "AIR":
        inland_cost = inland["to_air_port_cost_usd"]
    else:
        inland_cost = inland["to_sea_port_cost_usd"] * n_units

    # 2. Origin THC (sea only, per container)
    origin_thc = route["origin_thc_usd"] * n_units if ct != "AIR" else 0

    # 3. Ocean / air freight
    if ct == "FCL_20":
        fr = rates["FCL_20"]
        freight_min, freight_max = fr["min"] * n_units, fr["max"] * n_units
    elif ct == "FCL_40":
        fr = rates["FCL_40"]
        freight_min, freight_max = fr["min"] * n_units, fr["max"] * n_units
    elif ct == "FCL_40HC":
        fr = rates["FCL_40HC"]
        freight_min, freight_max = fr["min"] * n_units, fr["max"] * n_units
    elif ct == "LCL":
        cbm = req.cargo_volume_cbm or 1.0
        fr = rates["LCL_CBM"]
        freight_min = fr["min"] * cbm
        freight_max = fr["max"] * cbm
    else:  # AIR
        fr = rates["AIR_KG"]
        freight_min = fr["min"] * chargeable_kg
        freight_max = fr["max"] * chargeable_kg

    # 4. Transshipment THC (sea only, per hub per container)
    n_hubs = len([h for h in route["hubs"] if "Canal" not in h])  # canals don't charge THC
    trans_thc = route["transshipment_thc_usd"] * n_hubs * n_units if ct != "AIR" else 0

    # 5. Fixed charges — per B/L (once per shipment, not per container).
    # Each direction declares its own per-shipment levies in fixed_charges:
    #   PK_TO_US: ISF, B/L, seal, ISPS, documentation (US export-side)
    #   US_TO_PK: B/L, seal, ISPS, documentation, PK wharfage + handling
    if ct == "AIR":
        fixed = fixed_cfg.get("documentation_usd", 0)
    else:
        fixed = (
            fixed_cfg.get("isf_filing_usd", 0)
            + fixed_cfg.get("bl_fee_usd", 0)
            + fixed_cfg.get("seal_fee_usd", 0)
            + fixed_cfg.get("isps_surcharge_usd", 0)
            + fixed_cfg.get("documentation_usd", 0)
            + fixed_cfg.get("pk_wharfage_usd", 0)
            + fixed_cfg.get("pk_port_handling_usd", 0)
        )

    # 6. Destination charges (THC per container, broker/drayage per container)
    dest_thc    = dest["thc_usd"] * n_units if ct != "AIR" else 0
    broker      = dest["customs_broker_usd"]
    drayage     = dest["drayage_usd"] * n_units

    # 7. Government levies on cargo value. Stored in the same CostBreakdown
    # fields (hmf/mpf) regardless of direction so the response schema and the
    # frontend widget stay unchanged.
    #   PK_TO_US: hmf = US Harbor Maintenance Fee, mpf = US Merchandise Processing Fee
    #   US_TO_PK: hmf = PK Wharfage levy proxy (set to 0 here — already in `fixed`),
    #             mpf = PK Withholding Tax (income-tax withholding on commercial imports)
    if graph.direction == "PK_TO_US":
        hmf = round(req.cargo_value_usd * fixed_cfg.get("hmf_rate", 0), 2)
        mpf_raw = req.cargo_value_usd * fixed_cfg.get("mpf_rate", 0)
        mpf_min = fixed_cfg.get("mpf_min_usd", 0)
        mpf_max = fixed_cfg.get("mpf_max_usd", 0)
        if mpf_max > 0:
            mpf = round(max(mpf_min, min(mpf_max, mpf_raw)), 2)
        else:
            mpf = round(mpf_raw, 2)
    else:  # US_TO_PK
        hmf = 0.0
        wht_rate = fixed_cfg.get("pk_withholding_tax_rate", 0)
        mpf = round(req.cargo_value_usd * wht_rate, 2)

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

def evaluate_routes(
    req: RouteEvaluationRequest,
    user_id: Optional[int] = None,
    conversation_id: Optional[str] = None,
    message_id: Optional[int] = None,
) -> RouteEvaluationResponse:
    # Pick the active graph based on the requested direction
    graph = _GRAPHS.get(req.direction)
    if graph is None:
        supported = list(_GRAPHS.keys())
        raise ValueError(
            f"Direction '{req.direction}' is not supported. Supported: {supported}"
        )

    # Validate origin
    inland = graph.inland_origins.get(req.origin_city)
    if not inland:
        available = list(graph.inland_origins.keys())
        raise ValueError(
            f"Unknown origin city '{req.origin_city}' for direction "
            f"{req.direction}. Available: {available}"
        )

    # Validate destination
    dest = graph.destination_charges.get(req.destination_city)
    if not dest:
        available = list(graph.destination_charges.keys())
        raise ValueError(
            f"Unknown destination city '{req.destination_city}' for direction "
            f"{req.direction}. Available: {available}"
        )

    dest_region = dest["region"]
    duty_rate   = _get_duty_rate(req.hs_code, graph)

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
        "[ROUTE] Evaluating [%s] %s→%s  cargo=%s  value=$%.0f  hs=%s  α=%.2f",
        req.direction, req.origin_city, req.destination_city, req.cargo_type,
        req.cargo_value_usd, req.hs_code or "N/A", req.cost_weight,
    )

    # ── Pre-fetch live rates concurrently (deduplicated) ──────────────────────
    applicable_routes = [
        r for r in graph.routes
        if _route_is_applicable(r, req.cargo_type, dest_region, req.direction)
    ]
    if req.cargo_type == "AIR":
        applicable_routes = [_localize_air_route(r, req.origin_city, graph) for r in applicable_routes]
    live_rates = _prefetch_live_rates(applicable_routes, req, chargeable_kg)

    # ── Build route results ────────────────────────────────────────────────────
    results: list[RouteResult] = []

    for route in applicable_routes:
        cost    = _calculate_cost(route, req, inland, dest, duty_rate, chargeable_kg, graph)
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

            # Replace static sea/air leg transit with live Freightos times when available.
            # Inland days, port processing, and customs days remain from the JSON since
            # Freightos only covers the port-to-port segment.
            if live.transit_min_days is not None and live.transit_max_days is not None:
                transit = TransitBreakdown(
                    inland_days=transit.inland_days,
                    sea_air_days_min=live.transit_min_days,
                    sea_air_days_max=live.transit_max_days,
                    port_processing=transit.port_processing,
                    customs_days=transit.customs_days,
                    total_min=round(transit.inland_days + live.transit_min_days + transit.port_processing + transit.customs_days, 1),
                    total_max=round(transit.inland_days + live.transit_max_days + transit.port_processing + transit.customs_days + 1, 1),
                )
                logger.info(
                    "[ROUTE] Live transit for %s: %d–%d days (sea/air leg)",
                    route["id"], live.transit_min_days, live.transit_max_days,
                )

        # Air routes contain airport codes (JFK, ORD, LAX) — keep name as-is.
        # Sea routes use generic city names that need localising for non-default destinations.
        display_name = (
            route["name"]
            if route["mode"] == "AIR"
            else _localize_route_name(
                route["name"],
                req.destination_city,
                graph.destination_city_names_in_route_names,
            )
        )
        results.append(RouteResult(
            id=route["id"],
            name=display_name,
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

    response = RouteEvaluationResponse(
        direction=req.direction,
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

    # ── Persist to DB ──
    if user_id:
        try:
            from models.route_evaluation_history import RouteEvaluationHistory
            from database.database import engine
            from sqlmodel import Session
            
            with Session(engine) as session:
                history = RouteEvaluationHistory(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    message_id=message_id,
                    origin_city=req.origin_city,
                    destination_city=req.destination_city,
                    cargo_type=req.cargo_type,
                    cargo_value_usd=req.cargo_value_usd,
                    hs_code=req.hs_code,
                    cargo_volume_cbm=req.cargo_volume_cbm,
                    cargo_weight_kg=req.cargo_weight_kg,
                    container_count=req.container_count,
                    cost_weight=req.cost_weight,
                    routes_count=len(results),
                    cheapest_route_id=cheapest_id,
                    fastest_route_id=fastest_id,
                    balanced_route_id=balanced_id,
                    full_response_json=response.model_dump_json(),
                )
                session.add(history)
                session.commit()
                logger.info(f"━━━ [DB] Saved route evaluation history for user {user_id}")
        except Exception as exc:
            logger.warning(f"━━━ [DB] Failed to save route evaluation history: {exc}")

    return response
