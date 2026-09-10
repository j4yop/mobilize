"""Run the M2 backtest: weights -> proxy returns -> metrics -> significance.

Requires data/processed/esg_panel.parquet (from `make data`).
Writes data/processed/backtest_results.parquet and prints a summary.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from mobilize.backtest.metrics import (  # noqa: E402
    cagr,
    max_drawdown,
    summary_table,
)
from mobilize.backtest.returns import (  # noqa: E402
    FRED_DM_SERIES,
    annual_returns_from_yields,
    portfolio_annual_returns,
    synthetic_em_yield,
)
from mobilize.backtest.significance import compare_portfolios  # noqa: E402
from mobilize.data.fred import fetch_series  # noqa: E402
from mobilize.data.indicators import END_YEAR, FRED_CURVE_SERIES, PANEL_START_YEAR  # noqa: E402
from mobilize.portfolio.construction import (  # noqa: E402
    BENCHMARK,
    composition_summary,
    weight_panel,
)

DATA_DIR = REPO_ROOT / "data"
PANEL_PATH = DATA_DIR / "processed" / "esg_panel.parquet"
OUT_PATH = DATA_DIR / "processed" / "backtest_results.parquet"


def _year_end_yield(df: pd.DataFrame) -> pd.Series:
    """Last available observation per calendar year (year-end yield level)."""
    df = df.dropna(subset=["value"]).sort_values("date")
    return df.groupby("year")["value"].last() / 100.0


def build_yield_matrix(panel: pd.DataFrame) -> pd.DataFrame:
    """Year x iso3 yield matrix (decimals) mixing observed & synthetic yields.

    Convention: YEAR-END yield levels (last observation of each December),
    so annual returns = carry from year-end (t-1) minus duration times the
    year-end (t-1) -> year-end (t) change. This captures full-year yield
    moves (e.g. 2013 taper tantrum) that annual means would dampen.
    """
    years = list(range(PANEL_START_YEAR - 1, END_YEAR + 1))  # need t-1 for first return
    us5y = fetch_series(FRED_CURVE_SERIES["5Y"])
    us5y["year"] = us5y["date"].dt.year
    us_yearly = _year_end_yield(us5y)

    # DM yields from FRED long-term series (year-end observation)
    dm_yield: dict[str, pd.Series] = {}
    for iso3, series_id in FRED_DM_SERIES.items():
        if iso3 == "USA":
            continue
        try:
            df = fetch_series(series_id)
            df["year"] = df["date"].dt.year
            dm_yield[iso3] = _year_end_yield(df)
        except Exception:  # noqa: BLE001
            continue

    # Macro panel for synthetic EM yields
    macro = panel.set_index(["iso3", "year"])

    def _reserves_gdp(iso3: str, year: int) -> float | None:
        try:
            res = macro.loc[(iso3, year), "FI.RES.TOTL.CD"]
            gdp = macro.loc[(iso3, year), "NY.GDP.MKTP.CD"]
            return float(res / gdp * 100) if gdp else None
        except Exception:  # noqa: BLE001
            return None

    def _gov(iso3: str, year: int) -> float | None:
        try:
            g = macro.loc[(iso3, year), "pillar_G"]
            return None if pd.isna(g) else float(g)
        except Exception:  # noqa: BLE001
            return None

    rows = {}
    for iso3 in panel["iso3"].unique():
        series = {}
        for year in years:
            if iso3 == "USA":
                series[year] = float(us_yearly.get(year, np.nan))
            elif iso3 in dm_yield:
                series[year] = float(dm_yield[iso3].get(year, np.nan))
                if not np.isfinite(series[year]):
                    series[year] = float(us_yearly.get(year, np.nan) + 0.01)
            else:
                # EM synthetic
                try:
                    debt = macro.loc[(iso3, year), "GC.DOD.TOTL.GD.ZS"]
                    infl = macro.loc[(iso3, year), "FP.CPI.TOTL.ZG"]
                except KeyError:
                    debt, infl = None, None
                debt = float(debt) if pd.notna(debt) else None
                infl = float(infl) if pd.notna(infl) else None
                series[year] = synthetic_em_yield(
                    float(us_yearly.get(year, 0.04)),
                    debt,
                    _reserves_gdp(iso3, year),
                    infl,
                    _gov(iso3, year),
                )
        rows[iso3] = series

    ym = pd.DataFrame(rows)
    ym.index.name = "year"
    return ym.reset_index()


def main() -> None:
    panel = pd.read_parquet(PANEL_PATH)
    print(f"Loaded panel: {len(panel)} rows, years "
          f"{panel['year'].min()}-{panel['year'].max()}")

    print("[1/4] Building yield matrix (FRED observed + EM synthetic) ...")
    yields = build_yield_matrix(panel)
    print(f"      {yields.shape[1]-1} countries, {yields['year'].min()}-{yields['year'].max()}")

    print("[2/4] Portfolio weights per year (no look-ahead) ...")
    wdf = weight_panel(panel)
    comp = composition_summary(wdf)
    print(comp.groupby("portfolio")[["n_holdings", "effective_n", "max_weight"]].mean().to_string())

    print("[3/4] Annual returns + metrics ...")
    rets_wide = annual_returns_from_yields(yields)
    port = portfolio_annual_returns(rets_wide, wdf)
    metrics = summary_table(port, benchmark_col=BENCHMARK)
    print("\n=== Portfolio metrics (2013-2023, annual) ===")
    print((metrics * 1).to_string(float_format=lambda x: f"{x: .4f}"))

    print("\n=== Bootstrap comparison vs benchmark ===")
    comp_stats = compare_portfolios(port, benchmark_col=BENCHMARK)
    print(comp_stats.to_string(float_format=lambda x: f"{x: .4f}"))

    print("\n[4/4] Saving results ...")
    port.to_parquet(OUT_PATH)
    print(f"      portfolio returns -> {OUT_PATH}")

    bench_growth = (1 + port[BENCHMARK]).cumprod()
    print("\nBenchmark growth of $1 (2013-2023):", f"{bench_growth.iloc[-1]:.3f}")
    for col in [c for c in port.columns if c != BENCHMARK]:
        g = (1 + port[col]).cumprod().iloc[-1]
        dd = max_drawdown(port[col])
        print(f"{col}: growth ${g:.3f}, maxDD {dd:.2%}, CAGR {cagr(port[col]):.2%}")


if __name__ == "__main__":
    main()
