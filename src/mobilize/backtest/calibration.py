"""Calibrate the sovereign spread model on OBSERVED yields.

Design decision (honesty constraint):
An unconstrained OLS fit of sovereign spreads on macro fundamentals using
DM-only data produces wrong-signed coefficients (e.g. debt negative) —
DM spreads are driven by policy rates and safe-haven flows (Japan: 250%
debt, near-zero yield), not credit fundamentals. We therefore:

1. Fit an UNCONSTRAINED OLS and report it as a diagnostic (R^2 etc.).
2. Fit a SIGN-CONSTRAINED least squares (debt >= 0, reserves <= 0,
   inflation >= 0, gov <= 0) which is the model used for EM synthesis.
   The constraint encodes credit-pricing priors; it is disclosed, not
   hidden. Coefficient magnitudes still come from the data.
3. Report both fits' R^2 so the reader sees the DM-fit weakness.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear

FEATURES = ["debt", "reserves", "inflation_excess", "gov_norm"]
TARGET = "spread"

# Credit-pricing sign priors (upper bounds for constrained fit)
SIGN_BOUNDS = {
    "debt": (0.0, np.inf),
    "reserves": (-np.inf, 0.0),
    "inflation_excess": (0.0, np.inf),
    "gov_norm": (-np.inf, 0.0),
}


def build_features(
    panel: pd.DataFrame,
    iso3: str,
    year: int,
    us_yield: float,
    country_yield: float | None,
    nearest_backfill: dict | None = None,
) -> dict | None:
    """Feature vector for one country-year (or None if data is missing).

    Debt/GDP is highly persistent but gappy across publication regimes;
    when the target year is missing we backfill from the NEAREST available
    year for that country (prepared by prepare_backfill). Governance and
    other features come from the panel as-is.
    """
    try:
        row = panel.set_index(["iso3", "year"]).loc[(iso3, year)]
    except KeyError:
        return None
    debt = row.get("GC.DOD.TOTL.GD.ZS")
    res = row.get("FI.RES.TOTL.CD")
    gdp = row.get("NY.GDP.MKTP.CD")
    infl = row.get("FP.CPI.TOTL.ZG")
    gov = row.get("pillar_G")

    # debt backfill: use nearest available year's value (within +-4 years)
    if (debt is None or pd.isna(debt)) and nearest_backfill is not None:
        debt = nearest_backfill.get((iso3, year))

    debt = float(debt) if debt is not None and pd.notna(debt) else None
    infl = float(infl) if infl is not None and pd.notna(infl) else None
    gov = float(gov) if gov is not None and pd.notna(gov) else None
    res_gdp = None
    if res is not None and gdp is not None and pd.notna(res) and pd.notna(gdp) and float(gdp) > 0:
        res_gdp = float(res) / float(gdp) * 100.0

    if debt is None or gov is None:
        return None
    return {
        "iso3": iso3,
        "year": year,
        "debt": debt / 100.0,
        "reserves": (res_gdp / 100.0) if res_gdp is not None else np.nan,
        "inflation_excess": (max(infl - 3.0, 0.0) if infl is not None else np.nan) / 10.0,
        "gov_norm": gov / 100.0,
        "us_yield": us_yield,
        "spread": (country_yield - us_yield) if country_yield is not None else np.nan,
    }


def prepare_backfill(
    panel: pd.DataFrame,
    indicator: str = "GC.DOD.TOTL.GD.ZS",
    max_gap_years: int = 4,
) -> dict[tuple[str, int], float]:
    """Nearest-year backfill map for a gappy indicator.

    For each (iso3, year) missing the indicator, find the nearest year
    (within max_gap_years) that has a value, per country.
    """
    sub = panel[["iso3", "year", indicator]].copy()
    out: dict[tuple[str, int], float] = {}
    for iso3, g in sub.groupby("iso3"):
        obs = g.dropna(subset=[indicator]).set_index("year")[indicator]
        if obs.empty:
            continue
        years_present = obs.index.to_numpy()
        for yr in g["year"].to_numpy():
            if (iso3, yr) not in set(zip(g["iso3"], g["year"], strict=False)):
                continue
            key = (iso3, int(yr))
            if obs.get(yr) is not None and pd.notna(obs.get(yr)):
                continue
            nearest = years_present[np.argmin(np.abs(years_present - yr))]
            if abs(nearest - yr) <= max_gap_years:
                out[key] = float(obs.loc[nearest])
    return out


def fit_ols(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """OLS with intercept via normal equations (tiny problem)."""
    A = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    return beta


def predict(beta: np.ndarray, X: np.ndarray) -> np.ndarray:
    A = np.column_stack([np.ones(len(X)), X])
    return A @ beta


def calibrate(
    calibration_rows: list[dict],
    ridge_lambda: float = 1e-4,
) -> dict:
    """Fit spread models on observed (country, year) feature rows.

    Returns a dict with:
      beta            - SIGN-CONSTRAINED coefficients (used for EM synthesis)
      beta_unconstr   - plain OLS (diagnostic)
      r2 / r2_unconstr - both fits' R^2
      n, medians, coef_names
    """
    df = pd.DataFrame(calibration_rows).dropna(subset=[TARGET])
    medians = df[FEATURES].median()
    Xdf = df[FEATURES].fillna(medians)
    X = Xdf.to_numpy(dtype=float)
    y = df[TARGET].to_numpy(dtype=float)
    A = np.column_stack([np.ones(len(X)), X])

    # --- unconstrained OLS (diagnostic) ---
    beta_u, *_ = np.linalg.lstsq(A, y, rcond=None)
    r2_u = _r2(y, A @ beta_u)

    # --- sign-constrained LS (production) ---
    lb = np.array([-np.inf] + [SIGN_BOUNDS[f][0] for f in FEATURES])
    ub = np.array([np.inf] + [SIGN_BOUNDS[f][1] for f in FEATURES])
    ATA = A.T @ A + ridge_lambda * np.eye(A.shape[1])
    res = lsq_linear(ATA, A.T @ y, bounds=(lb, ub))
    beta_c = res.x
    r2_c = _r2(y, A @ beta_c)

    return {
        "beta": beta_c,
        "beta_unconstr": beta_u,
        "r2": r2_c,
        "r2_unconstr": r2_u,
        "n": len(df),
        "medians": medians.to_dict(),
        "coef_names": ["intercept"] + FEATURES,
    }


def _r2(y: np.ndarray, y_hat: np.ndarray) -> float:
    ss_res = float(((y - y_hat) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return 1 - ss_res / ss_tot if ss_tot > 0 else np.nan


def expanding_window_cv(
    calibration_rows: list[dict],
    min_train_years: int = 4,
) -> float:
    """Expanding-window CV RMSE: fit through year t, predict year t+1."""
    df = pd.DataFrame(calibration_rows).dropna(subset=[TARGET])
    medians = df[FEATURES].median()
    years = sorted(df["year"].unique())
    sq_errs: list[float] = []
    for i in range(min_train_years, len(years)):
        train_years = years[:i]
        test_year = years[i]
        train = df[df["year"].isin(train_years)]
        test = df[df["year"] == test_year].dropna(subset=[TARGET])
        if len(train) < 10 or len(test) == 0:
            continue
        Xtr = train[FEATURES].fillna(medians).to_numpy(dtype=float)
        ytr = train[TARGET].to_numpy(dtype=float)
        beta = fit_ols(Xtr, ytr)
        Xte = test[FEATURES].fillna(medians).to_numpy(dtype=float)
        yte = test[TARGET].to_numpy(dtype=float)
        resid = predict(beta, Xte) - yte
        sq_errs.extend((resid**2).tolist())
    return float(np.sqrt(np.mean(sq_errs))) if sq_errs else np.nan


def synthetic_yield(
    model: dict,
    features: dict,
    us_yield: float,
    spread_bounds: tuple[float, float] = (0.0075, 0.08),
) -> float:
    """Predict one country-year yield from the fitted spread model."""
    x = []
    for f in FEATURES:
        v = features.get(f)
        if v is None or (isinstance(v, float) and np.isnan(v)):
            v = model["medians"][f]
        x.append(float(v))
    spread = float(predict(model["beta"], np.array([x]))[0])
    spread = float(np.clip(spread, *spread_bounds))
    return max(us_yield + spread, 0.02)
