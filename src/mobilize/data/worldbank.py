"""World Bank Open Data API client.

Keyless REST client for api.worldbank.org with retry and page handling.
Returns tidy DataFrames: country, iso3, year, indicator code, value.
"""

from __future__ import annotations

import time
from collections.abc import Iterable

import pandas as pd
import requests

BASE_URL = "https://api.worldbank.org/v2"
FORMAT_JSON = "json"
PER_PAGE = 16000
MAX_RETRIES = 4
RETRY_BACKOFF_S = 2.0


class WorldBankAPIError(RuntimeError):
    """Raised when the World Bank API returns an unusable response."""


class WorldBankClient:
    """Thin, polite client around the World Bank indicator API."""

    def __init__(
        self,
        session: requests.Session | None = None,
        timeout_s: float = 30.0,
        sleep_s: float = 0.15,
    ) -> None:
        self.session = session or requests.Session()
        self.timeout_s = timeout_s
        self.sleep_s = sleep_s

    def _get(self, path: str, params: dict) -> dict | list:
        url = f"{BASE_URL}{path}"
        last_err: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout_s)
                if resp.status_code == 429:
                    time.sleep(RETRY_BACKOFF_S * (attempt + 1))
                    continue
                resp.raise_for_status()
                payload = resp.json()
                # The WB API returns [meta, data] for format=json.
                if isinstance(payload, list) and len(payload) == 2:
                    if payload[0].get("message"):
                        raise WorldBankAPIError(str(payload[0]["message"]))
                    return payload[1]
                return payload
            except (requests.RequestException, ValueError) as exc:
                last_err = exc
                time.sleep(RETRY_BACKOFF_S * (attempt + 1))
        raise WorldBankAPIError(f"GET {url} failed after {MAX_RETRIES} retries: {last_err}")

    def fetch_indicator(
        self,
        indicator: str,
        countries: Iterable[str],
        start_year: int,
        end_year: int,
    ) -> pd.DataFrame:
        """Fetch one indicator across countries and years, tidy format."""
        ctry = ";".join(countries)
        path = f"/country/{ctry}/indicator/{indicator}"
        params = {
            "format": FORMAT_JSON,
            "date": f"{start_year}:{end_year}",
            "per_page": PER_PAGE,
        }
        rows = self._get(path, params)
        records = []
        for row in rows:
            value = row.get("value")
            records.append(
                {
                    "iso3": row.get("countryiso3code") or "",
                    "country": row.get("country", {}).get("value", ""),
                    "year": int(row["date"]),
                    "indicator": indicator,
                    "value": value,
                }
            )
        df = pd.DataFrame.from_records(records)
        # Drop aggregates (empty iso3) and keep only requested countries
        return df[df["iso3"].isin(set(countries))].reset_index(drop=True)

    def fetch_many(
        self,
        indicators: Iterable[str],
        countries: Iterable[str],
        start_year: int,
        end_year: int,
    ) -> pd.DataFrame:
        """Fetch several indicators, concatenating tidy frames."""
        frames = []
        for ind in indicators:
            frame = self.fetch_indicator(ind, countries, start_year, end_year)
            frames.append(frame)
            time.sleep(self.sleep_s)  # be polite
        return pd.concat(frames, ignore_index=True)


def wide(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot tidy frame to wide: index (iso3, year), columns = indicators."""
    return (
        df.dropna(subset=["value"])
        .pivot_table(index=["iso3", "year"], columns="indicator", values="value")
        .reset_index()
    )
