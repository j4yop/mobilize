"""Fama–MacBeth (1976) cross-sectional pricing test for the ESG factor.

Question: is the sovereign ESG score PRICED — i.e., do higher-ESG countries
earn systematically different returns, period by period?

Procedure (monthly, the classic setup):
1. Each month m: cross-sectional regression
       r_i,m = a_m + g_m * score_i + e_i,m
   (score uses the annual panel score observable BEFORE month m starts —
   no look-ahead: month of year t uses the year-(t-1) score).
2. The time series {g_m} is the priced ESG factor. Test
       mean(g) = 0  via Newey–West-corrected t-stat.

Interpretation: mean(g) < 0 means high-ESG countries earn LOWER returns
(i.e., ESG behaves like a "quality" premium investors pay for) —
consistent with our backtest's carry mechanism.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

NW_LAGS_FRAC = 0.1  # Newey-West lag length = ~10% of the sample (common rule of thumb)


def score_asof(
    panel: pd.DataFrame,
    iso3: str,
    period_year: int,
    period_month: int,
    score_col: str = "score_equal",
) -> float | None:
    """Score observable before the period starts.

    For months Jan-Sep of year t: latest score is year t-1 (published with
    a lag). For Oct-Dec: also year t-1 (annual data, conservative).
    """
    hist = panel[(panel["iso3"] == iso3) & (panel["year"] <= period_year - 1)]
    if hist.empty:
        return None
    hist = hist.dropna(subset=[score_col])
    if hist.empty:
        return None
    row = hist.sort_values("year").iloc[-1]
    return float(row[score_col])


def monthly_fama_macbeth(
    returns: pd.DataFrame,
    panel: pd.DataFrame,
    score_col: str = "score_equal",
) -> dict:
    """Run Fama–MacBeth with the ESG score as the single priced factor.

    returns: month x iso3 monthly return frame.
    Returns dict with gamma series, NW t-stat, mean, p-value (two-sided,
    normal approx), n_months, avg cross-section size.
    """
    gammas: list[float] = []
    months_used: list[pd.Period] = []
    n_cross: list[int] = []
    for month in returns.index:
        yr = month.year
        r = returns.loc[month].dropna()
        if len(r) < 8:  # need a meaningful cross-section
            continue
        scores = {}
        for iso3 in r.index:
            s = score_asof(panel, iso3, yr, month.month, score_col=score_col)
            if s is not None:
                scores[iso3] = s
        common = [i for i in r.index if i in scores]
        if len(common) < 8:
            continue
        x = np.array([scores[i] / 100.0 for i in common])
        y = r.loc[common].to_numpy(dtype=float)
        # OLS: y = a + g*x
        X = np.column_stack([np.ones(len(x)), x])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        gammas.append(float(beta[1]))
        months_used.append(month)
        n_cross.append(len(common))

    g = np.asarray(gammas, dtype=float)
    n = len(g)
    if n < 12:
        return {"n_months": n, "gamma_mean": np.nan, "t_nw": np.nan, "p": np.nan}

    # Newey–West standard error of the mean
    lags = max(1, int(n * NW_LAGS_FRAC))
    g_c = g - g.mean()
    lr_var = float((g_c**2).mean()) / n  # base variance of mean
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1)
        cov = float((g_c[:-L] * g_c[L:]).mean())
        lr_var += 2 * w * cov / n
    se = float(np.sqrt(max(lr_var, 1e-18)))
    t = float(g.mean() / se)
    # two-sided normal p-value
    from math import erfc

    p = float(erfc(abs(t) / np.sqrt(2)))

    return {
        "n_months": n,
        "gamma_mean": float(g.mean()),
        "gamma_se": se,
        "t_nw": t,
        "p": p,
        "avg_cross_section": float(np.mean(n_cross)),
        "gamma_series": pd.Series(g, index=pd.PeriodIndex(months_used), name="gamma"),
    }
