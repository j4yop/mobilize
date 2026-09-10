"""Cleaning and missing-data protocol for the sovereign ESG panel.

Protocol (applied per indicator, per year):
1. Interpolate short gaps (<= GAP_LIMIT years) within each country series.
2. Drop country-indicator series with coverage < MIN_COVERAGE of the window.
3. Winsorize indicator distributions at [1%, 99%] per year (cross-section).
4. Report a coverage matrix so limitations are transparent.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

GAP_LIMIT = 2
MIN_COVERAGE = 0.80
WINSOR_PCT = (0.01, 0.99)


def interpolate_short_gaps(
    df: pd.DataFrame,
    value_cols: list[str],
    id_cols: list[str] | None = None,
    gap_limit: int = GAP_LIMIT,
) -> pd.DataFrame:
    """Interpolate gaps of <= gap_limit years within each country's series.

    Uses forward interpolation with a fill limit: a run of NaNs longer than
    gap_limit is only partially filled (first `gap_limit` values), so long
    gaps are never fully bridged.
    """
    id_cols = id_cols or ["iso3"]
    out = df.sort_values(id_cols + ["year"]).copy()
    for col in value_cols:
        out[col] = (
            out.groupby(id_cols, group_keys=False)[col]
            .apply(lambda s: s.interpolate(limit=gap_limit, limit_direction="forward"))
        )
    return out


def coverage_matrix(df: pd.DataFrame, value_cols: list[str]) -> pd.DataFrame:
    """Fraction of non-null observations per indicator per country."""
    return df.groupby("iso3")[value_cols].apply(lambda g: g.notna().mean())


def drop_low_coverage(
    df: pd.DataFrame,
    value_cols: list[str],
    min_coverage: float = MIN_COVERAGE,
) -> pd.DataFrame:
    """Set to NaN any country-indicator series below the coverage threshold."""
    cov = coverage_matrix(df, value_cols)
    bad = cov < min_coverage
    out = df.set_index("iso3").copy()
    for col in value_cols:
        bad_countries = bad.index[bad[col]]
        if len(bad_countries):
            out.loc[out.index.isin(bad_countries), col] = np.nan
    return out.reset_index()


def winsorize_cross_section(
    df: pd.DataFrame,
    value_cols: list[str],
    pct: tuple[float, float] = WINSOR_PCT,
) -> pd.DataFrame:
    """Winsorize each indicator's cross-section per year at given percentiles."""
    out = df.copy()
    for col in value_cols:
        out[col] = out.groupby("year")[col].transform(
            lambda s: s.clip(*s.quantile(list(pct))) if s.notna().any() else s
        )
    return out
