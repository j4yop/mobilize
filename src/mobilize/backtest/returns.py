"""Bond-return proxy engine.

Real sovereign bond prices are paywalled; we proxy annual local-currency
bond returns from observable yield data — the standard "duration-times-
change-in-yield" approximation — and add the carry (starting yield).

    r_t ≈ y_{t-1} - D * (y_t - y_{t-1})

where y is the country's observed yield level and D = PROXY_DURATION
(5y modified duration). Realized limitations of this proxy are disclosed
in the report's limitations section.

Yield inputs per country (all free):
- United States: FRED DGS5 (5y CMT)
- Other DMs: FRED series for that market where available, else regional proxy
- EMs: IMF/WB-derived synthetic yields from macro fundamentals:
      y = US_5Y + sovereign spread,
      spread = f(debt/GDP, reserves, inflation, governance score) calibrated
      to a cross-section of observed JPM EMBI-style spread levels (published
      ranges, e.g. EMBI Global ~250-600bp over the window).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from mobilize.data.indicators import PROXY_DURATION

# FRED series used directly for yield proxies.
FRED_DM_SERIES: dict[str, str] = {
    "USA": "DGS5",
    "DEU": "IRLTLT01DEM156N",  # long-term govt bond yield, monthly (OECD via FRED)
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


def duration_proxy_return(start_yield: float, end_yield: float, duration: float = PROXY_DURATION) -> float:
    """One-period total return proxy: carry minus duration-weighted yield change."""
    return start_yield - duration * (end_yield - start_yield)


def synthetic_em_yield(
    us_5y: float,
    debt_gdp: float | None,
    reserves_gdp: float | None,
    inflation: float | None,
    gov_score: float | None,
) -> float:
    """Synthetic EM yield level (annual, decimal) from macro fundamentals.

    Spread model (calibrated to public EMBI-style cross-sections, where
    spreads range ~150bp (strong IG-like EM) to ~800bp (stressed):
      spread = 4.5% + 1.2%*(debt/100) - 0.8%*(reserves/100)
               + 0.08%*max(inflation-3, 0) - 3.5%*(gov/100)
      clipped to [75bp, 800bp]; yield = max(us_5y + spread, 2% floor)
    A gov score of 100 with debt 50% moves the spread near the floor;
    a gov score near 0 with high debt hits the ceiling.
    """
    spread = 0.045
    if debt_gdp is not None and np.isfinite(debt_gdp):
        spread += 0.012 * (debt_gdp / 100.0)
    if reserves_gdp is not None and np.isfinite(reserves_gdp):
        spread -= 0.008 * (reserves_gdp / 100.0)
    if inflation is not None and np.isfinite(inflation):
        spread += 0.0008 * max(inflation - 3.0, 0.0)
    if gov_score is not None and np.isfinite(gov_score):
        spread -= 0.035 * (gov_score / 100.0)
    spread = float(np.clip(spread, 0.0075, 0.080))
    return max(us_5y + spread, 0.02)


def annual_returns_from_yields(yields: pd.DataFrame) -> pd.DataFrame:
    """Yearly proxy returns per country from a (year x iso3) yield matrix.

    Column layout: years in rows, one column per iso3, yield in decimals.
    Returns a (year x iso3) frame of annual returns in decimals.
    """
    rets = {}
    cols = [c for c in yields.columns if c != "year"]
    for col in cols:
        y = yields[col].astype(float).to_numpy()
        r = []
        for i in range(1, len(y)):
            if np.isfinite(y[i]) and np.isfinite(y[i - 1]):
                r.append(duration_proxy_return(y[i - 1], y[i]))
            else:
                r.append(np.nan)
        rets[col] = pd.Series(r, index=yields["year"].to_numpy()[1:])
    out = pd.DataFrame(rets)
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
            # should not happen with a complete panel
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
