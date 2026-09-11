"""Monthly-frequency returns engine and metrics.

Monthly returns from month-end yields:
    r_m ≈ y_{m-1} - D_m * (y_m - y_{m-1})
where D_m = PROXY_DURATION / 12 (annual duration spread monthly).

EM caveat: EM monthly yields are interpolated annual levels, so EM
intra-year variation is macro-only — disclosed in the report.

Portfolio rules (realistic institutional behavior):
- Weights: annual, from year-(t-1) scores/GDP (same as annual engine).
- Within the year, weights stay fixed (annual rebalancing).
- Monthly returns are weighted with those annual weights.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from mobilize.data.indicators import PROXY_DURATION, RF_ANNUAL

MONTHS_PER_YEAR = 12


def monthly_returns_from_yields(yields: pd.DataFrame) -> pd.DataFrame:
    """Month x iso3 decimal returns from a Month x iso3 yield matrix.

    Monthly return of a constant-duration portfolio:
        r_m ≈ y_{m-1}/12 - D * (y_m - y_{m-1})
    The capital-gain term uses the FULL portfolio duration D against the
    month's yield move (dy_m is a monthly move; duration is not scaled).
    Compounding these monthly returns reproduces the annual duration-
    approximation return to first order.
    """
    rets = pd.DataFrame(index=yields.index[1:], columns=yields.columns, dtype=float)
    y = yields.to_numpy(dtype=float)
    for j in range(y.shape[1]):
        col = y[:, j]
        r = np.full(y.shape[0] - 1, np.nan)
        for i in range(1, y.shape[0]):
            if np.isfinite(col[i]) and np.isfinite(col[i - 1]):
                r[i - 1] = col[i - 1] / MONTHS_PER_YEAR - PROXY_DURATION * (col[i] - col[i - 1])
        rets.iloc[:, j] = r
    return rets


def map_annual_weights_to_months(
    weight_df: pd.DataFrame,
    months: pd.PeriodIndex,
) -> pd.DataFrame:
    """Expand annual weights to each month of their holding year.

    weight_df rows: (portfolio, hold_year, iso3, weight).
    Returns rows: (portfolio, month, iso3, weight).
    """
    records = []
    for (name, year), g in weight_df.groupby(["portfolio", "hold_year"]):
        year_months = [m for m in months if m.year == year]
        if not year_months:
            continue
        for iso3, w in g.set_index("iso3")["weight"].items():
            for m in year_months:
                records.append(
                    {"portfolio": name, "month": m, "iso3": iso3, "weight": w}
                )
    return pd.DataFrame.from_records(records)


def portfolio_monthly_returns(
    returns_wide: pd.DataFrame,
    weight_month_df: pd.DataFrame,
) -> pd.DataFrame:
    """Month x portfolio weighted returns."""
    records = []
    for (name, month), g in weight_month_df.groupby(["portfolio", "month"]):
        if month not in returns_wide.index:
            continue
        w = g.set_index("iso3")["weight"]
        month_rets = returns_wide.loc[month].dropna()
        common = w.index.intersection(month_rets.index)
        if len(common) == 0:
            continue
        w_c = w.loc[common] / w.loc[common].sum()
        records.append(
            {"portfolio": name, "month": month, "return": float((w_c * month_rets.loc[common]).sum())}
        )
    out = pd.DataFrame.from_records(records)
    return out.pivot_table(index="month", columns="portfolio", values="return")


def annualize_return(monthly: pd.Series) -> float:
    """Annualized (geometric) return from monthly decimals."""
    r = monthly.dropna().to_numpy()
    if len(r) == 0:
        return np.nan
    growth = float(np.prod(1 + r))
    n_years = len(r) / MONTHS_PER_YEAR
    return growth ** (1 / n_years) - 1 if growth > 0 else -1.0


def annualize_vol(monthly: pd.Series) -> float:
    """Annualized volatility from monthly decimals."""
    r = monthly.dropna()
    if len(r) < 3:
        return np.nan
    return float(r.std(ddof=1) * np.sqrt(MONTHS_PER_YEAR))


def monthly_metrics(returns: pd.DataFrame, benchmark_col: str | None = None) -> pd.DataFrame:
    """Summary table at monthly frequency (annualized units)."""
    from mobilize.backtest.metrics import (
        cvar_historical,
        max_drawdown,
        var_historical,
    )

    rows = []
    for col in returns.columns:
        r = returns[col]
        rf_m = (1 + RF_ANNUAL) ** (1 / MONTHS_PER_YEAR) - 1
        excess = r - rf_m
        downside = excess[excess < 0]
        dd_dev = float(np.sqrt((downside**2).mean())) if len(downside) else np.nan
        rows.append(
            {
                "portfolio": col,
                "ann_return": annualize_return(r),
                "ann_vol": annualize_vol(r),
                "sharpe": (
                    float(excess.mean() / r.std(ddof=1) * np.sqrt(MONTHS_PER_YEAR))
                    if r.std(ddof=1) > 0
                    else np.nan
                ),
                "sortino": (
                    float(excess.mean() * 12 / dd_dev) if dd_dev and dd_dev > 0 else np.nan
                ),
                "max_drawdown": max_drawdown(r),
                "VaR95_m": var_historical(r),
                "CVaR95_m": cvar_historical(r),
            }
        )
    return pd.DataFrame(rows).set_index("portfolio")
