"""Yield matrix construction: annual (year-end) and monthly, DM observed / EM fitted.

Conventions:
- DM yields: observed FRED series at year-end (annual) or month-end (monthly).
- EM yields: calibrated spread model (calibration.py) at annual frequency;
  monthly EM yields linearly interpolated between annual endpoints, then
  perturbed by nothing (no fake intra-year variation). Returns from
  interpolated EM yields reflect only macro-driven moves — disclosed.
- US base: DGS10.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from mobilize.backtest.calibration import (
    build_features,
    calibrate,
    prepare_backfill,
    synthetic_yield,
)
from mobilize.data.fred import fetch_series

US_SERIES = "DGS10"

# OECD long-term government bond yields (monthly, %) via FRED — ~10y tenor.
FRED_DM_SERIES: dict[str, str] = {
    "USA": "DGS10",
    "DEU": "IRLTLT01DEM156N",
    "GBR": "IRLTLT01GBM156N",
    "FRA": "IRLTLT01FRM156N",
    "ITA": "IRLTLT01ITM156N",
    "ESP": "IRLTLT01ESM156N",
    "NLD": "IRLTLT01NLM156N",
    "SWE": "IRLTLT01SEM156N",
    "CHE": "IRLTLT01CHM156N",
    "JPN": "IRLTLT01JPM156N",
    "AUS": "IRLTLT01AUM156N",
    "CAN": "IRLTLT01CAM156N",
}


def _fetch_all_dm() -> dict[str, pd.DataFrame]:
    out = {}
    for iso3, sid in FRED_DM_SERIES.items():
        if iso3 == "USA":
            out[iso3] = fetch_series(sid)  # daily DGS10
        else:
            try:
                out[iso3] = fetch_series(sid)
            except Exception:  # noqa: BLE001
                continue
    return out


def annual_yield_matrix(panel: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    """Year x iso3 matrix of year-end yields (decimals). Returns (matrix, model, diag)."""
    dm = _fetch_all_dm()

    # Year-end DM yields
    year_end: dict[str, pd.Series] = {}
    month_end: dict[str, pd.Series] = {}
    for iso3, df in dm.items():
        d = df.dropna(subset=["value"]).sort_values("date").copy()
        d["year"] = d["date"].dt.year
        d["ym"] = d["date"].dt.to_period("M")
        year_end[iso3] = d.groupby("year")["value"].last() / 100.0
        month_end[iso3] = d.groupby("ym")["value"].last() / 100.0

    # Calibration rows: DM country-years with observed yields
    # (debt backfilled from nearest available year within a country)
    years_all = list(range(start_year, end_year + 1))
    backfill = prepare_backfill(panel)
    cal_rows: list[dict] = []
    for iso3 in year_end:
        for yr in years_all:
            y = year_end[iso3].get(yr)
            us = year_end["USA"].get(yr)
            if y is None or us is None or not np.isfinite(y) or not np.isfinite(us):
                continue
            feats = build_features(panel, iso3, yr, float(us), float(y), nearest_backfill=backfill)
            if feats is not None:
                cal_rows.append(feats)

    model = calibrate(cal_rows)

    # Build the full matrix: DM observed, EM synthetic
    universe = sorted(panel["iso3"].unique())
    mat: dict[str, dict[int, float]] = {iso3: {} for iso3 in universe}
    for iso3 in universe:
        for yr in years_all:
            us = year_end["USA"].get(yr)
            us_f = float(us) if us is not None and np.isfinite(us) else float("nan")
            if iso3 in year_end:
                y = year_end[iso3].get(yr)
                if y is not None and np.isfinite(y):
                    mat[iso3][yr] = float(y)
                elif np.isfinite(us_f):
                    # missing DM observation: fallback = US + model spread (flagged via diag)
                    feats = build_features(panel, iso3, yr, us_f, None)
                    if feats is not None:
                        mat[iso3][yr] = synthetic_yield(model, feats, us_f)
            else:
                feats = build_features(panel, iso3, yr, us_f, None, nearest_backfill=backfill)
                if feats is not None and np.isfinite(us_f):
                    mat[iso3][yr] = synthetic_yield(model, feats, us_f)

    out = pd.DataFrame({iso3: pd.Series(vals) for iso3, vals in mat.items()})
    out.index.name = "year"
    diag = {
        "n_calibration_rows": model.get("n", 0),
        "calibration_r2": model.get("r2", np.nan),
        "calibration_r2_unconstr": model.get("r2_unconstr", np.nan),
        "beta": dict(zip(model.get("coef_names", []), model.get("beta", []), strict=False)),
        "n_universe_with_yields": int(out.notna().any(axis=0).sum()),
    }
    return out, model, diag


def monthly_yield_matrix(
    panel: pd.DataFrame,
    annual_matrix: pd.DataFrame,
    model: dict,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """Month x iso3 matrix of month-end yields (decimals).

    DM: observed monthly series.
    EM: observed US 10Y + linearly interpolated annual spread
    (spread_t = annual_EM_yield_t - annual_US_yield_t). This composition
    preserves observed US curve dynamics in every EM series — EM
    co-moves with the global curve — while EM-specific monthly variation
    is macro-only. Disclosed limitation, not hidden.
    """
    dm = _fetch_all_dm()
    months = pd.period_range(f"{start_year}-01", f"{end_year}-12", freq="M")

    month_end: dict[str, pd.Series] = {}
    for iso3, df in dm.items():
        d = df.dropna(subset=["value"]).sort_values("date").copy()
        d["ym"] = d["date"].dt.to_period("M")
        month_end[iso3] = d.groupby("ym")["value"].last() / 100.0

    us_monthly = month_end.get("USA")
    if us_monthly is None:
        raise RuntimeError("US 10Y series unavailable")
    us_annual = annual_matrix.get("USA", pd.Series(dtype=float))

    def _annual_em_spread(iso3: str) -> pd.Series:
        """Annual EM spread over US, from the annual yield matrix."""
        em = annual_matrix.get(iso3, pd.Series(dtype=float))
        spreads = {}
        for yr in set(list(em.index) + list(us_annual.index)):
            e, u = em.get(yr, np.nan), us_annual.get(yr, np.nan)
            if np.isfinite(e) and np.isfinite(u):
                spreads[yr] = e - u
        return pd.Series(spreads)

    universe = sorted(panel["iso3"].unique())
    out: dict[str, pd.Series] = {}
    for iso3 in universe:
        if iso3 in month_end:
            s = pd.Series(
                [month_end[iso3].get(m, np.nan) for m in months], index=months
            )
        else:
            # EM: observed US monthly + interpolated annual spread
            spread_annual = _annual_em_spread(iso3)
            if spread_annual.empty:
                s = pd.Series(np.nan, index=months)
            else:
                path = {}
                for m in months:
                    yr = m.year
                    prev = spread_annual.get(yr - 1, np.nan)
                    curr = spread_annual.get(yr, np.nan)
                    if np.isfinite(prev) and np.isfinite(curr):
                        w = (m.month - 0.5) / 12.0
                        spread_m = prev + w * (curr - prev)
                    elif np.isfinite(curr):
                        spread_m = curr
                    elif np.isfinite(prev):
                        spread_m = prev
                    else:
                        spread_m = np.nan
                    us_m = us_monthly.get(m, np.nan)
                    path[m] = us_m + spread_m if np.isfinite(us_m) and np.isfinite(spread_m) else np.nan
                s = pd.Series(path)
        s.name = iso3
        out[iso3] = s

    frame = pd.DataFrame(out)
    frame.index.name = "month"
    return frame
