"""Risk & performance metrics for annual return series.

All metrics computed on annual (yearly) returns — a small-sample
environment — so we report both point estimates and bootstrap-based
uncertainty (see significance.py).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from mobilize.data.indicators import RF_ANNUAL

TRADING_DAYS = 252  # reported for reference; metrics are annual-frequency


def cagr(returns: pd.Series) -> float:
    """Compound annual growth rate from annual decimal returns."""
    r = returns.dropna().to_numpy()
    if len(r) == 0:
        return np.nan
    growth = float(np.prod(1 + r))
    if growth <= 0:
        return -1.0
    n = len(r)
    return growth ** (1 / n) - 1


def vol(returns: pd.Series) -> float:
    """Annualized volatility = std of annual returns."""
    r = returns.dropna()
    return float(r.std(ddof=1)) if len(r) >= 2 else np.nan


def sharpe(returns: pd.Series, rf: float = RF_ANNUAL) -> float:
    """Annual Sharpe ratio."""
    r = returns.dropna()
    if len(r) < 2 or r.std(ddof=1) == 0:
        return np.nan
    return float((r.mean() - rf) / r.std(ddof=1))


def sortino(returns: pd.Series, rf: float = RF_ANNUAL) -> float:
    """Annual Sortino ratio (downside deviation vs MAR = rf)."""
    r = returns.dropna()
    downside = r[r < rf]
    if len(downside) < 1:
        return np.inf if r.mean() > rf else np.nan
    dd = float(np.sqrt(((downside - rf) ** 2).mean()))
    if dd == 0:
        return np.nan
    return float((r.mean() - rf) / dd)


def drawdown_series(returns: pd.Series) -> pd.Series:
    """Drawdown (as negative fraction) at each point of the cumulative index."""
    growth = (1 + returns.fillna(0)).cumprod()
    peak = growth.cummax()
    dd = growth / peak - 1
    return dd


def max_drawdown(returns: pd.Series) -> float:
    """Maximum drawdown (most negative value, returned as a negative number)."""
    dd = drawdown_series(returns)
    return float(dd.min()) if len(dd) else np.nan


def drawdown_duration(returns: pd.Series) -> int:
    """Longest underwater period, in years (peak-to-recovery)."""
    dd = drawdown_series(returns)
    underwater = dd < -1e-12
    longest = 0
    run = 0
    for flag in underwater:
        run = run + 1 if flag else 0
        longest = max(longest, run)
    return int(longest)


def var_historical(returns: pd.Series, alpha: float = 0.05) -> float:
    """Historical VaR: the alpha-quantile of the return distribution."""
    r = returns.dropna()
    if len(r) < 3:
        return np.nan
    return float(np.quantile(r, alpha))


def cvar_historical(returns: pd.Series, alpha: float = 0.05) -> float:
    """Historical CVaR (expected shortfall): mean of returns below VaR."""
    r = returns.dropna()
    if len(r) < 3:
        return np.nan
    v = np.quantile(r, alpha)
    tail = r[r <= v]
    if len(tail) == 0:
        return float(v)
    return float(tail.mean())


def downside_capture(strat: pd.Series, bench: pd.Series) -> float:
    """Downside capture: sum of strategy vs benchmark returns in bench-down years."""
    df = pd.concat([strat.rename("s"), bench.rename("b")], axis=1).dropna()
    down = df[df["b"] < 0]
    if len(down) == 0 or down["b"].sum() == 0:
        return np.nan
    return float(down["s"].sum() / down["b"].sum())


def summary_table(returns: pd.DataFrame, benchmark_col: str | None = None) -> pd.DataFrame:
    """Full metrics table for a (year x portfolio) return frame."""
    rows = []
    bench = returns[benchmark_col] if benchmark_col in returns.columns else None
    for col in returns.columns:
        r = returns[col]
        row = {
            "portfolio": col,
            "CAGR": cagr(r),
            "vol": vol(r),
            "sharpe": sharpe(r),
            "sortino": sortino(r),
            "max_drawdown": max_drawdown(r),
            "dd_years": drawdown_duration(r),
            "VaR95": var_historical(r),
            "CVaR95": cvar_historical(r),
        }
        if bench is not None and col != benchmark_col:
            row["downside_capture"] = downside_capture(r, bench)
        rows.append(row)
    return pd.DataFrame(rows).set_index("portfolio")
