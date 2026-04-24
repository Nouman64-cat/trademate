"""
UN Comtrade API Service.
Comprehensive client for the UN Comtrade Public API (v1).

Usage:
    python -m app.services.un_comtrade
"""
from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict, Optional, Literal

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import settings

logger = logging.getLogger("trademate.un_comtrade")

# API Defaults
BASE_URL = "https://comtradeapi.un.org/public/v1"

# Type Aliases for better documentation
TypeCode = Literal["C", "S"]
FreqCode = Literal["A", "M"]
ClassificationCode = Literal[
    "HS", "H6", "H5", "H4", "H3", "H2", "H1", "H0",
    "S4", "S3", "S2", "S1", "BE", "BE5", "EB", "EB10", "EB02", "EBS", "EBSDMX"
]


class ComtradeClient:
    """
    Client for the UN Comtrade Public API.
    Handles sessions, retries, and formatting for various endpoints.
    """

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        self.base_url = BASE_URL
        self.timeout = timeout
        self.api_key = api_key
        self.session = self._init_session()

    def _init_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=(429, 500, 502, 503, 504),
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        # Set API Key if provided
        if self.api_key:
            session.headers.update({"Ocp-Apim-Subscription-Key": self.api_key})

        return session

    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        kwargs.setdefault("timeout", self.timeout)

        try:
            resp = self.session.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            logger.error(f"HTTP Error for {url}: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")
            raise

    def get_releases(self) -> Dict[str, Any]:
        """Fetch all available Comtrade releases."""
        return self._request("GET", "getComtradeReleases")

    def get_preview(
        self,
        type_code: TypeCode,
        freq_code: FreqCode,
        cl_code: ClassificationCode,
        reporter_code: Optional[str] = None,
        period: Optional[str] = None,
        partner_code: Optional[str] = None,
        cmd_code: Optional[str] = None,
        flow_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Preview trade data.
        Note: Preview endpoints are limited in the number of records returned.
        """
        path = f"preview/{type_code}/{freq_code}/{cl_code}"
        params = {
            "reporterCode": reporter_code,
            "period": period,
            "partnerCode": partner_code,
            "cmdCode": cmd_code,
            "flowCode": flow_code,
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}
        return self._request("GET", path, params=params)

    def get_preview_tariffline(
        self,
        type_code: TypeCode,
        freq_code: FreqCode,
        cl_code: ClassificationCode,
        reporter_code: Optional[str] = None,
        period: Optional[str] = None,
        partner_code: Optional[str] = None,
        partner2_code: Optional[str] = None,
        cmd_code: Optional[str] = None,
        flow_code: Optional[str] = None,
        customs_code: Optional[str] = None,
        mot_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Preview detailed tariff line data."""
        path = f"previewTariffline/{type_code}/{freq_code}/{cl_code}"
        params = {
            "reporterCode": reporter_code,
            "period": period,
            "partnerCode": partner_code,
            "partner2Code": partner2_code,
            "cmdCode": cmd_code,
            "flowCode": flow_code,
            "customsCode": customs_code,
            "motCode": mot_code,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._request("GET", path, params=params)

    def get_metadata(
        self,
        type_code: TypeCode,
        freq_code: FreqCode,
        cl_code: ClassificationCode,
    ) -> Dict[str, Any]:
        """Get metadata for a specific dataset."""
        path = f"getMetadata/{type_code}/{freq_code}/{cl_code}"
        return self._request("GET", path)

    def get_data_availability(
        self,
        type_code: TypeCode,
        freq_code: FreqCode,
        cl_code: ClassificationCode,
        is_tariffline: bool = False,
    ) -> Dict[str, Any]:
        """Get data availability (DA) information."""
        endpoint = "getDATariffline" if is_tariffline else "getDA"
        path = f"{endpoint}/{type_code}/{freq_code}/{cl_code}"
        return self._request("GET", path)

    def get_world_share(
        self,
        type_code: TypeCode,
        freq_code: FreqCode,
        period: Optional[int] = None,
        reporter_code: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get world share data."""
        path = f"getWorldShare/{type_code}/{freq_code}"
        params = {"period": period, "reporterCode": reporter_code}
        params = {k: v for k, v in params.items() if v is not None}
        return self._request("GET", path, params=params)

    def get_mbs(
        self,
        series_type: Optional[str] = None,
        year: Optional[str] = None,
        country_code: Optional[str] = None,
        period: Optional[str] = None,
        period_type: Optional[str] = None,
        table_type: Optional[str] = None,
        output_format: str = "json",
    ) -> Dict[str, Any]:
        """Get Monthly Bulletin of Statistics (MBS) data."""
        params = {
            "series_type": series_type,
            "year": year,
            "country_code": country_code,
            "period": period,
            "period_type": period_type,
            "table_type": table_type,
            "format": output_format,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._request("GET", "getMBS", params=params)


def _main() -> int:
    logging.basicConfig(level=logging.INFO)
    client = ComtradeClient()

    try:
        print("\n--- Fetching Comtrade Releases ---")
        releases = client.get_releases()
        print(f"Found {releases.get('count', 0)} releases.")
        if releases.get("data"):
            print("Latest release:", json.dumps(releases["data"][0], indent=2))

        print("\n--- Previewing Pakistan (586) Annual HS data for 2023 ---")
        # 586 is Pakistan code in M49
        preview = client.get_preview(
            type_code="C", freq_code="A", cl_code="HS",
            reporter_code="586", period="2023"
        )
        print(f"Preview count: {preview.get('count', 0)}")
        if preview.get("data"):
            print("First data record:", json.dumps(preview["data"][0], indent=2))

    except Exception as exc:
        logger.error(f"Execution failed: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(_main())
