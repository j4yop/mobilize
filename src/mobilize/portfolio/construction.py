"""Portfolio construction: benchmark, ESG-tilted, and negative-screened.

No-look-ahead discipline
------------------------
At each annual rebalance for holding year `t`, ONLY information observable
at the end of year `t-1` is used:
- ESG composite scores from December of `t-1` (panel year `t-1`)
- GDP weights from year `t-1`

The weights are then held constant through year `t` (annual rebalancing).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from mobilize.data.indicators import END_YEAR, EXCLUDED_BOTTOM_PCT, START_YEAR, TILT_POWER

BENCHMARK = "benchmark"
TILTED = "esg_tilted"
SCREENED = "esg_screened"


def _latest_scores(panel: pd.DataFrame, as_of_year: int, score_col: str = "score_equal") -> pd.Series:
    """Most recent non-null score per country as of end of `as_of_year`."""
    if panel.empty or score_col not in panel.columns or "year" not in panel.columns:
        return pd.Series(dtype=float)
    hist = panel[panel["year"] <= as_of_year].dropna(subset=[score_col])
    if hist.empty:
        return pd.Series(dtype=float)
    # take the latest year available per country
    idx = hist.groupby("iso3")["year"].idxmax()
    return hist.loc[idx].set_index("iso3")[score_col]


def _gdp_weights(panel: pd.DataFrame, as_of_year: int) -> pd.Series:
    """GDP weights (latest observable GDP per country as of `as_of_year`)."""
    if panel.empty or "NY.GDP.MKTP.CD" not in panel.columns or "year" not in panel.columns:
        return pd.Series(dtype=float)
    hist = panel[panel["year"] <= as_of_year].dropna(subset=["NY.GDP.MKTP.CD"])
    if hist.empty:
        return pd.Series(dtype=float)
    idx = hist.groupby("iso3")["year"].idxmax()
    gdp = hist.loc[idx].set_index("iso3")["NY.GDP.MKTP.CD"]
    return gdp / gdp.sum()


def weights_for_year(
    panel: pd.DataFrame,
    hold_year: int,
    score_col: str = "score_equal",
) -> dict[str, pd.Series]:
    """Build the three portfolios' weights for holding year `hold_year`.

    Returns {portfolio_name: weights Series indexed by iso3}:
      - benchmark:   GDP-weighted, full universe
      - esg_tilted:  GDP-weighted base, re-weighted by (score/100)^TILT_POWER
      - esg_screened: GDP-weighted, bottom EXCLUDED_BOTTOM_PCT scores dropped
    """
    as_of = hold_year - 1
    base = _gdp_weights(panel, as_of)
    scores = _latest_scores(panel, as_of, score_col)
    if base.empty or scores.empty:
        return {}

    common = base.index.intersection(scores.index)
    base = base.loc[common]
    scores = scores.loc[common]

    out: dict[str, pd.Series] = {}

    # Benchmark: full universe, GDP weights
    out[BENCHMARK] = base / base.sum()

    # Tilted: multiply GDP weight by normalized score factor
    factor = (scores / 100.0) ** TILT_POWER
    tilted = base * factor
    out[TILTED] = tilted / tilted.sum()

    # Screened: drop bottom quintile by score, re-normalize GDP weights
    cutoff = scores.quantile(EXCLUDED_BOTTOM_PCT)
    keep = scores[scores > cutoff].index
    screened = base.loc[base.index.intersection(keep)]
    out[SCREENED] = screened / screened.sum()

    return {k: v for k, v in out.items() if len(v) > 0}


def weight_panel(
    panel: pd.DataFrame,
    score_col: str = "score_equal",
    start_year: int = START_YEAR,
    end_year: int = END_YEAR,
) -> pd.DataFrame:
    """Weight matrix: rows (portfolio, hold_year), columns iso3, values weight."""
    records = []
    for hold_year in range(start_year, end_year + 1):
        w = weights_for_year(panel, hold_year, score_col)
        for name, series in w.items():
            for iso3, weight in series.items():
                records.append(
                    {"portfolio": name, "hold_year": hold_year, "iso3": iso3, "weight": weight}
                )
    return pd.DataFrame.from_records(records)


def composition_summary(weight_df: pd.DataFrame) -> pd.DataFrame:
    """Per-year holding counts and effective N (1/HHI) per portfolio."""
    rows = []
    for (name, year), g in weight_df.groupby(["portfolio", "hold_year"]):
        w = g.set_index("iso3")["weight"]
        hhi = (w**2).sum()
        rows.append(
            {
                "portfolio": name,
                "hold_year": year,
                "n_holdings": len(w),
                "effective_n": 1.0 / hhi if hhi > 0 else np.nan,
                "max_weight": w.max(),
            }
        )
    return pd.DataFrame(rows)
