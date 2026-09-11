"""Annual bond-return proxy engine.

Real sovereign bond prices are paywalled; we proxy annual local-currency
bond returns from observable year-end yield data — the standard
"duration-times-change-in-yield" approximation plus carry:

    r_t ≈ y_{t-1} - D * (y_t - y_{t-1})

where y is the country's year-end yield and D = PROXY_DURATION (~10Y
portfolio duration). Yield matrix construction (observed DM + calibrated
EM) lives in yields.py; monthly-frequency lives in monthly.py.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from mobilize.data.indicators import PROXY_DURATION


def duration_proxy_return(start_yield: float, end_yield: float, duration: float = PROXY_DURATION) -> float:
    """One-period total return proxy: carry minus duration-weighted yield change."""
    return start_yield - duration * (end_yield - start_yield)


def annual_returns_from_yields(yields: pd.DataFrame) -> pd.DataFrame:
    """Yearly proxy returns per country from a (year x iso3) yield matrix.

    yields: index year, columns iso3, values decimals. First row has no
    return (no prior year) and is dropped.
    """
    y_all = yields.to_numpy(dtype=float)
    years = yields.index.to_numpy()
    rets = np.full((len(years) - 1, y_all.shape[1]), np.nan)
    for j in range(y_all.shape[1]):
        col = y_all[:, j]
        for i in range(1, len(col)):
            if np.isfinite(col[i]) and np.isfinite(col[i - 1]):
                rets[i - 1, j] = duration_proxy_return(col[i - 1], col[i])
    out = pd.DataFrame(rets, index=years[1:], columns=yields.columns)
    out.index.name = "year"
    return out


def portfolio_annual_returns(
    returns_wide: pd.DataFrame,
    weight_df: pd.DataFrame,
) -> pd.DataFrame:
    """Weighted portfolio returns per (portfolio, hold_year).

    returns_wide: index year, columns iso3 (decimal returns).
    weight_df: rows (portfolio, hold_year, iso3, weight).
    """
    records = []
    for (name, year), g in weight_df.groupby(["portfolio", "hold_year"]):
        w = g.set_index("iso3")["weight"]
        if year not in returns_wide.index:
            continue
        year_rets = returns_wide.loc[year]
        common = w.index.intersection(year_rets.dropna().index)
        if len(common) == 0:
            continue
        w_common = w.loc[common] / w.loc[common].sum()  # renormalize over priced countries
        r = float((w_common * year_rets.loc[common]).sum())
        records.append({"portfolio": name, "year": year, "return": r})
    out = pd.DataFrame.from_records(records)
    return out.pivot_table(index="year", columns="portfolio", values="return")


def cumulative_growth(returns: pd.Series) -> pd.Series:
    """Cumulative growth index from a Series of decimal annual returns."""
    return (1 + returns.fillna(0)).cumprod()
