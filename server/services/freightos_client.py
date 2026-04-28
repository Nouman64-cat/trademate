"""
services/freightos_client.py — Freightos Shipping Calculator Client

Fetches live ocean/air freight rate estimates from the Freightos public API.
Falls back gracefully: callers catch FreightosUnavailable and use static rates.

API: GET https://ship.freightos.com/api/shippingCalculator
Auth: ?key=API_KEY  (query param)
Docs: https://ship.freightos.com/api/shippingCalculator
"""

import json
import logging
import os
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────

_API_KEY    = os.environ.get("FREIGHTOS_API_KEY", "")
_API_SECRET = os.environ.get("FREIGHTOS_API_SECRET", "")  # reserved for future use

_BASE_URL   = "https://ship.freightos.com/api/shippingCalculator"
_TIMEOUT_S  = 10

# ── UNLOCODE mappings ──────────────────────────────────────────────────────────
# Each map serves both directions: when an entry's *string form* appears as
# either an origin or a destination in a route definition, _resolve_ports will
# look it up. PK_TO_US uses Pakistan as origin / USA as destination; US_TO_PK
# uses USA as origin / Pakistan as destination. Same UNLOCODE table either way.

_PK_PORT_UNLOCODE: dict[str, str] = {
    # Sea
    "Karachi (PKKHI)":   "PKKHI",
    "Karachi":           "PKKHI",
    "PKKHI":             "PKKHI",
    "PKKHIA":            "PKKHI",   # alias used in pk_usa_routes.json
    "Port Qasim":        "PKBQM",
    "Port Qasim (PKBQM)":"PKBQM",
    "PKBQM":             "PKBQM",
    # Air gateways (Freightos uses the city UNLOCODE for air too)
    "Karachi Intl (KHI)": "PKKHI",
    "KHI":               "PKKHI",
    "Lahore (LHE)":      "PKLHE",
    "LHE":               "PKLHE",
    "Islamabad (ISB)":   "PKISB",
    "ISB":               "PKISB",
    "Sialkot (SKT)":     "PKSKT",
    "SKT":               "PKSKT",
}

_US_PORT_UNLOCODE: dict[str, str] = {
    # Sea
    "Los Angeles (USLAX)": "USLAX",
    "USLAX":               "USLAX",
    "Long Beach (USLGB)":  "USLGB",
    "USLGB":               "USLGB",
    "New York (USNYC)":    "USNYC",
    "USNYC":               "USNYC",
    "USNYK":               "USNYC",   # alias
    "Savannah (USSAV)":    "USSAV",
    "USSAV":               "USSAV",
    "Baltimore (USBAL)":   "USBAL",
    "USBAL":               "USBAL",
    "Miami (USMIA)":       "USMIA",
    "USMIA":               "USMIA",
    "Seattle (USSEA)":     "USSEA",
    "USSEA":               "USSEA",
    "Houston (USHOU)":     "USHOU",
    "USHOU":               "USHOU",
    # Air gateways
    "JFK":     "USNYC",
    "New York JFK (JFK)": "USNYC",
    "ORD":     "USCHI",
    "Chicago O'Hare (ORD)": "USCHI",
    "USCHI":   "USCHI",
    "LAX":     "USLAX",   # LAX airport in LA
    "Los Angeles (LAX)":   "USLAX",
    "MIA":     "USMIA",
    "Miami (MIA)":         "USMIA",
    "ATL":     "USATL",
    "Atlanta (ATL)":       "USATL",
    "DFW":     "USDFW",
    "IAH":     "USHOU",   # IAH airport ≈ Houston for cargo lookup
    "SEA":     "USSEA",
}

# Direction-keyed lookup: which side of the lane is origin and which is destination?
# When a code is missing on the expected side, _resolve_ports raises
# FreightosUnavailable — the engine then falls back to static rates.

_ORIGIN_SEA_UNLOCODE: dict[str, str] = {**_PK_PORT_UNLOCODE, **_US_PORT_UNLOCODE}
_DEST_SEA_UNLOCODE:   dict[str, str] = {**_PK_PORT_UNLOCODE, **_US_PORT_UNLOCODE}
_ORIGIN_AIR_UNLOCODE: dict[str, str] = {**_PK_PORT_UNLOCODE, **_US_PORT_UNLOCODE}
_DEST_AIR_UNLOCODE:   dict[str, str] = {**_PK_PORT_UNLOCODE, **_US_PORT_UNLOCODE}

# Cargo type → Freightos loadtype param
_LOADTYPE_MAP: dict[str, str] = {
    "FCL_20":   "container20",
    "FCL_40":   "container40",
    "FCL_40HC": "container40HC",
    "LCL":      "boxes",       # LCL billed per CBM as boxes
    "AIR":      "air",
}


# ── Data classes ───────────────────────────────────────────────────────────────

@dataclass
class FreightosRate:
    """Live freight rate returned by the API."""
    min_usd: float
    max_usd: float
    currency: str = "USD"


class FreightosUnavailable(Exception):
    """Raised when Freightos cannot return a rate (no key, API error, no quotes)."""


# ── Internal helpers ───────────────────────────────────────────────────────────

def _resolve_ports(
    origin_port: str | list,
    dest_port: str | list,
    cargo_type: str,
) -> tuple[str, str]:
    """
    Resolve port name strings to UNLOCODEs.
    Accepts either a single string or a list (picks first match).
    Raises FreightosUnavailable if no mapping exists.
    """
    origin_map = _ORIGIN_AIR_UNLOCODE if cargo_type == "AIR" else _ORIGIN_SEA_UNLOCODE
    dest_map   = _DEST_AIR_UNLOCODE   if cargo_type == "AIR" else _DEST_SEA_UNLOCODE

    origins = origin_port if isinstance(origin_port, list) else [origin_port]
    dests   = dest_port   if isinstance(dest_port,   list) else [dest_port]

    origin_code = next((origin_map[p] for p in origins if p in origin_map), None)
    dest_code   = next((dest_map[p]   for p in dests   if p in dest_map),   None)

    if not origin_code:
        raise FreightosUnavailable(f"No UNLOCODE mapping for origin port: '{origin_port}'")
    if not dest_code:
        raise FreightosUnavailable(f"No UNLOCODE mapping for destination port: '{dest_port}'")

    return origin_code, dest_code


def _parse_response(data: dict) -> FreightosRate:
    """
    Parse the Freightos JSON response into a FreightosRate.

    Expected shape:
    {
      "response": {
        "estimatedFreightRates": {
          "numQuotes": 1,
          "mode": {   // may also be a list
            "price": {
              "min": {"moneyAmount": {"amount": 1234, "currency": "USD"}},
              "max": {"moneyAmount": {"amount": 2345, "currency": "USD"}}
            }
          }
        }
      }
    }
    """
    try:
        rates_root = data["response"]["estimatedFreightRates"]
        num_quotes = int(rates_root.get("numQuotes", 0))
        if num_quotes == 0:
            raise FreightosUnavailable("Freightos returned 0 quotes for this lane")

        # "mode" can be a single dict or a list of dicts
        mode_data = rates_root.get("mode")
        if isinstance(mode_data, list):
            modes = mode_data
        else:
            modes = [mode_data]

        min_prices: list[float] = []
        max_prices: list[float] = []

        for m in modes:
            if not m:
                continue
            price = m.get("price", {})
            min_amount = price.get("min", {}).get("moneyAmount", {}).get("amount")
            max_amount = price.get("max", {}).get("moneyAmount", {}).get("amount")
            if min_amount is not None:
                min_prices.append(float(min_amount))
            if max_amount is not None:
                max_prices.append(float(max_amount))

        if not min_prices or not max_prices:
            raise FreightosUnavailable("Could not parse price from Freightos response")

        return FreightosRate(min_usd=min(min_prices), max_usd=max(max_prices))

    except FreightosUnavailable:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise FreightosUnavailable(f"Unexpected Freightos response structure: {exc}") from exc


# ── Public API ─────────────────────────────────────────────────────────────────

def get_rate(
    origin_port: str | list,
    dest_port: str | list,
    cargo_type: str,
    cargo_volume_cbm: float | None = None,
    cargo_weight_kg: float | None = None,
    chargeable_kg: float | None = None,
) -> FreightosRate:
    """
    Fetch a live freight rate estimate from Freightos for the given lane.

    Parameters
    ----------
    origin_port     : Port name string or list as used in pk_usa_routes.json
    dest_port       : Destination port string or list
    cargo_type      : FCL_20 | FCL_40 | FCL_40HC | LCL | AIR
    cargo_volume_cbm: Volume in CBM (used for LCL weight proxy)
    cargo_weight_kg : Actual weight in kg
    chargeable_kg   : IATA chargeable weight for AIR

    Raises
    ------
    FreightosUnavailable
        If no API key, port not mapped, API errors, or zero quotes returned.
    """
    # ── 1. Validate ports first (always surfaced, even without credentials)\
    origin_code, dest_code = _resolve_ports(origin_port, dest_port, cargo_type)

    # ── 2. Check credentials
    if not _API_KEY:
        raise FreightosUnavailable("Freightos API credentials not configured")

    # ── 3. Build query params
    loadtype = _LOADTYPE_MAP.get(cargo_type, "container20")

    # Effective weight: chargeable_kg > cargo_weight_kg > CBM proxy > default
    if cargo_type == "AIR":
        weight = chargeable_kg or cargo_weight_kg or 100.0
    elif cargo_type == "LCL":
        # Approximate: 1 CBM ≈ 500 kg (freight industry standard)
        weight = (cargo_volume_cbm or 1.0) * 500
    else:
        weight = cargo_weight_kg or 15000  # typical FCL cargo weight

    params: dict = {
        "key":         _API_KEY,
        "origin":      origin_code,
        "destination": dest_code,
        "loadtype":    loadtype,
        "weight":      weight,
        "format":      "json",
    }

    # ── 4. Call API
    try:
        logger.info(
            "[FREIGHTOS] GET %s → %s  type=%s  weight=%.0f",
            origin_code, dest_code, loadtype, weight,
        )
        resp = requests.get(_BASE_URL, params=params, timeout=_TIMEOUT_S)
    except requests.RequestException as exc:
        raise FreightosUnavailable(f"Network error contacting Freightos: {exc}") from exc

    if resp.status_code == 401 or resp.status_code == 403:
        raise FreightosUnavailable("Freightos authentication failed (check API key)")
    if not resp.ok:
        raise FreightosUnavailable(
            f"Freightos returned HTTP {resp.status_code}: {resp.text[:200]}"
        )

    # ── 5. Parse response
    try:
        data = resp.json()
    except Exception as exc:
        raise FreightosUnavailable(f"Freightos returned non-JSON response: {exc}") from exc

    rate = _parse_response(data)

    # ── 6. Persist to DB (fire-and-forget, never blocks the caller)
    _save_to_db(
        origin_port=origin_port,
        dest_port=dest_port,
        origin_code=origin_code,
        dest_code=dest_code,
        cargo_type=cargo_type,
        loadtype=loadtype,
        weight=weight,
        http_status=resp.status_code,
        raw_body=data,
        rate=rate,
    )

    return rate


def _save_to_db(
    origin_port,
    dest_port,
    origin_code: str,
    dest_code: str,
    cargo_type: str,
    loadtype: str,
    weight: float,
    http_status: int,
    raw_body: dict,
    rate: "FreightosRate",
) -> None:
    try:
        from database.database import engine
        from models.freightos_rate import FreightosRateRecord
        from sqlmodel import Session

        origin_name = origin_port if isinstance(origin_port, str) else ", ".join(origin_port)
        dest_name   = dest_port   if isinstance(dest_port,   str) else ", ".join(dest_port)

        record = FreightosRateRecord(
            origin_name=origin_name,
            origin_code=origin_code,
            dest_name=dest_name,
            dest_code=dest_code,
            cargo_type=cargo_type,
            loadtype=loadtype,
            weight_kg=weight,
            http_status=http_status,
            num_quotes=1,
            min_usd=rate.min_usd,
            max_usd=rate.max_usd,
            currency=rate.currency,
            raw_response=json.dumps(raw_body, ensure_ascii=False),
        )
        with Session(engine) as session:
            session.add(record)
            session.commit()
    except Exception:
        # Never let DB persistence break a live user request
        logger.warning("[FREIGHTOS] Failed to persist rate to DB", exc_info=True)
