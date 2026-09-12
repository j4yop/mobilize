"""Run the full analysis: calibration -> annual + monthly backtests + Fama-MacBeth.

Requires data/processed/esg_panel.parquet (from `make data`).
Writes data/processed/backtest_results.parquet (annual),
        data/processed/backtest_monthly.parquet (monthly),
        data/processed/fama_macbeth.parquet (gamma series).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from mobilize.backtest.fama_macbeth import monthly_fama_macbeth  # noqa: E402
from mobilize.backtest.metrics import max_drawdown, summary_table  # noqa: E402
from mobilize.backtest.monthly import (  # noqa: E402
    map_annual_weights_to_months,
    monthly_metrics,
    monthly_returns_from_yields,
    portfolio_monthly_returns,
)
from mobilize.backtest.returns import (  # noqa: E402
    annual_returns_from_yields,
    portfolio_annual_returns,
)
from mobilize.backtest.significance import compare_portfolios  # noqa: E402
from mobilize.backtest.yields import annual_yield_matrix, monthly_yield_matrix  # noqa: E402
from mobilize.data.indicators import END_YEAR, PANEL_START_YEAR, START_YEAR  # noqa: E402
from mobilize.portfolio.construction import (  # noqa: E402
    BENCHMARK,
    composition_summary,
    weight_panel,
)

DATA_DIR = REPO_ROOT / "data"
PANEL_PATH = DATA_DIR / "processed" / "esg_panel.parquet"
OUT_ANNUAL = DATA_DIR / "processed" / "backtest_results.parquet"
OUT_MONTHLY = DATA_DIR / "processed" / "backtest_monthly.parquet"
OUT_FM = DATA_DIR / "processed" / "fama_macbeth.parquet"


def main() -> None:
    panel = pd.read_parquet(PANEL_PATH)
    print(f"Loaded panel: {len(panel)} rows, years "
          f"{panel['year'].min()}-{panel['year'].max()}")

    # ---------- Yields + calibration ----------
    print("[1/6] Building annual yield matrix (DM observed, EM calibrated) ...")
    ym, model, diag = annual_yield_matrix(panel, PANEL_START_YEAR - 1, END_YEAR)
    print(f"      calibration n={diag['n_calibration_rows']}, "
          f"R2(constrained)={diag['calibration_r2']:.3f}, "
          f"R2(unconstrained)={diag['calibration_r2_unconstr']:.3f}")
    print("      beta (constrained):", {k: f"{v:.4f}" for k, v in diag["beta"].items()})
    print(f"      universe with yields: {diag['n_universe_with_yields']}/{panel['iso3'].nunique()}")

    from mobilize.backtest.calibration import expanding_window_cv, prepare_backfill

    cal_rows = []
    from mobilize.backtest.calibration import build_features
    from mobilize.backtest.yields import _fetch_all_dm

    dm = _fetch_all_dm()
    year_end = {}
    for iso3, df in dm.items():
        d = df.dropna(subset=["value"]).sort_values("date").copy()
        d["year"] = d["date"].dt.year
        year_end[iso3] = d.groupby("year")["value"].last() / 100.0
    backfill = prepare_backfill(panel)
    for iso3 in year_end:
        for yr in range(PANEL_START_YEAR - 1, END_YEAR + 1):
            y = year_end[iso3].get(yr)
            us = year_end["USA"].get(yr)
            if y is None or us is None:
                continue
            f = build_features(panel, iso3, yr, float(us), float(y), nearest_backfill=backfill)
            if f is not None:
                cal_rows.append(f)
    cv_rmse = expanding_window_cv(cal_rows)
    print(f"      expanding-window CV RMSE: {cv_rmse:.4f} ({cv_rmse*10000:.0f}bp)")

    # ---------- Annual backtest ----------
    print("[2/6] Annual backtest (year-end yields) ...")
    wdf = weight_panel(panel)
    comp = composition_summary(wdf)
    print(comp.groupby("portfolio")[["n_holdings", "effective_n", "max_weight"]].mean().to_string())

    rets_wide = annual_returns_from_yields(ym)
    port = portfolio_annual_returns(rets_wide, wdf)
    metrics = summary_table(port, benchmark_col=BENCHMARK)
    print("\n=== Annual portfolio metrics (2013-2023) ===")
    print(metrics.to_string(float_format=lambda x: f"{x: .4f}"))

    print("\n=== Annual significance vs benchmark ===")
    comp_stats = compare_portfolios(port, benchmark_col=BENCHMARK)
    print(comp_stats.to_string(float_format=lambda x: f"{x: .4f}"))

    # ---------- Monthly backtest ----------
    print("\n[3/6] Monthly backtest (month-end yields, annual weights) ...")
    ym_month = monthly_yield_matrix(panel, ym, model, START_YEAR, END_YEAR)
    rets_m = monthly_returns_from_yields(ym_month)
    wdf_m = map_annual_weights_to_months(wdf, rets_m.index)
    port_m = portfolio_monthly_returns(rets_m, wdf_m)
    mm = monthly_metrics(port_m, benchmark_col=BENCHMARK)
    print("\n=== Monthly portfolio metrics (annualized) ===")
    print(mm.to_string(float_format=lambda x: f"{x: .4f}"))

    print("\n=== Monthly significance vs benchmark ===")
    stats_m = compare_portfolios(port_m, benchmark_col=BENCHMARK)
    print(stats_m.to_string(float_format=lambda x: f"{x: .4f}"))
    print("      (mean_ret_diff is per-month; multiply by 12 for annualized)")

    # ---------- Fama-MacBeth ----------
    print("\n[4/6] Fama-MacBeth: is the ESG score priced? ...")
    fm = monthly_fama_macbeth(rets_m, panel)
    if np.isfinite(fm.get("t_nw", np.nan)):
        print(f"      months={fm['n_months']}, avg cross-section={fm['avg_cross_section']:.0f}")
        print(f"      gamma(mean)={fm['gamma_mean']*10000:.2f}bp per unit ESG(0-100) per month")
        print(f"      Newey-West t={fm['t_nw']:.3f}, two-sided p={fm['p']:.4f}")
    else:
        print(f"      insufficient months: {fm.get('n_months')}")

    # Pillar-level Fama-MacBeth (does the composite null hide pillar effects?)
    fm_pillars = {}
    for pillar_col, label in (("pillar_E", "E"), ("pillar_S", "S"), ("pillar_G", "G")):
        fm_p = monthly_fama_macbeth(rets_m, panel, score_col=pillar_col)
        if np.isfinite(fm_p.get("t_nw", np.nan)):
            fm_pillars[label] = fm_p
            print(f"      pillar {label}: gamma={fm_p['gamma_mean']*10000:6.2f}bp, "
                  f"NW t={fm_p['t_nw']:5.2f}, p={fm_p['p']:.3f}")
        else:
            print(f"      pillar {label}: insufficient months ({fm_p.get('n_months')})")

    # ---------- Save ----------
    print("\n[5/6] Saving outputs ...")
    port.to_parquet(OUT_ANNUAL)
    port_m.to_parquet(OUT_MONTHLY)
    rets_m.to_parquet(DATA_DIR / "processed" / "country_returns_monthly.parquet")
    if "gamma_series" in fm:
        fm["gamma_series"].to_frame("gamma").to_parquet(OUT_FM)
    pillar_rows = []
    for label, fm_p in fm_pillars.items():
        pillar_rows.append(
            {
                "pillar": label,
                "n_months": fm_p["n_months"],
                "gamma_mean": fm_p["gamma_mean"],
                "gamma_se": fm_p["gamma_se"],
                "t_nw": fm_p["t_nw"],
                "p": fm_p["p"],
                "avg_cross_section": fm_p["avg_cross_section"],
            }
        )
    if pillar_rows:
        pd.DataFrame(pillar_rows).to_parquet(OUT_FM.with_name("fama_macbeth_pillars.parquet"))

    # ---------- Headlines ----------
    print("\n[6/6] Headlines")
    bench_growth = (1 + port[BENCHMARK]).cumprod()
    print(f"Annual  | benchmark growth ${bench_growth.iloc[-1]:.3f}, maxDD {max_drawdown(port[BENCHMARK]):.2%}")
    for col in [c for c in port.columns if c != BENCHMARK]:
        g = (1 + port[col]).cumprod().iloc[-1]
        print(f"Annual  | {col}: growth ${g:.3f}, maxDD {max_drawdown(port[col]):.2%}")
    bm = port_m[BENCHMARK]
    print(f"Monthly | benchmark: ann ret {(np.prod(1+bm.dropna())**(12/len(bm.dropna()))-1):.2%}, "
          f"ann vol {bm.std(ddof=1)*np.sqrt(12):.2%}, maxDD {max_drawdown(bm):.2%}")


if __name__ == "__main__":
    main()
