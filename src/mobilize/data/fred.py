"""FRED client for US Treasury yield-curve data.

Uses the keyless fredgraph.csv endpoint (no API key required).
Falls back gracefully when a series is discontinued (e.g., DGS20 has gaps).
"""

from __future__ import annotations

from io import StringIO

import pandas as pd
import requests

FREDGRAPH_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
TIMEOUT_S = 30.0


class FREDError(RuntimeError):
    """Raised when a FRED download cannot be turned into a usable frame."""


def fetch_series(series_id: str, session: requests.Session | None = None) -> pd.DataFrame:
    """Download one FRED series via fredgraph.csv.

    Returns DataFrame with columns: date (datetime), value (float, NaN for gaps).
    """
    sess = session or requests.Session()
    resp = sess.get(FREDGRAPH_URL, params={"id": series_id}, timeout=TIMEOUT_S)
    if resp.status_code != 200:
        raise FREDError(f"FRED returned {resp.status_code} for {series_id}")
    try:
        df = pd.read_csv(StringIO(resp.text))
    except Exception as exc:  # noqa: BLE001
        raise FREDError(f"Cannot parse FRED CSV for {series_id}: {exc}") from exc

    first_col = df.columns[0]
    df[first_col] = pd.to_datetime(df[first_col], errors="coerce")
    df = df.rename(columns={first_col: "date", series_id: "value"})
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df[["date", "value"]].dropna(subset=["date"])


def fetch_curve(series_map: dict[str, str]) -> pd.DataFrame:
    """Download multiple curve series and return a wide date-indexed frame."""
    frames = {}
    for tenor, series_id in series_map.items():
        df = fetch_series(series_id)
        s = df.set_index("date")["value"].rename(tenor)
        frames[tenor] = s
    out = pd.concat(frames.values(), axis=1)
    out.index.name = "date"
    return out.sort_index()
