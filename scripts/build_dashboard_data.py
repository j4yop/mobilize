"""Export all analysis outputs into a single static JSON bundle for the web app.

Reads:  data/processed/{esg_panel, backtest_results, backtest_monthly,
        fama_macbeth}.parquet
Writes: app/public/data/dashboard.json  (committed; app is fully static)

Run AFTER `python scripts/run_backtest.py`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from mobilize.backtest.metrics import (  # noqa: E402
    drawdown_series,
    summary_table,
)
from mobilize.backtest.monthly import monthly_metrics  # noqa: E402
from mobilize.backtest.significance import compare_portfolios  # noqa: E402
from mobilize.data.indicators import COUNTRIES  # noqa: E402
from mobilize.portfolio.construction import (  # noqa: E402
    BENCHMARK,
    composition_summary,
    weight_panel,
)

DATA_DIR = REPO_ROOT / "data" / "processed"
OUT = REPO_ROOT / "app" / "public" / "data" / "dashboard.json"

METRIC_LABELS = {
    "CAGR": "CAGR",
    "vol": "Volatility",
    "sharpe": "Sharpe",
    "sortino": "Sortino",
    "max_drawdown": "Max Drawdown",
    "dd_years": "Drawdown (yrs)",
    "VaR95": "VaR 95%",
    "CVaR95": "CVaR 95%",
    "downside_capture": "Downside Capture",
}


def _periods_to_str(idx: pd.PeriodIndex) -> list[str]:
    return [str(p) for p in idx]


def main() -> None:
    panel = pd.read_parquet(DATA_DIR / "esg_panel.parquet")
    annual = pd.read_parquet(DATA_DIR / "backtest_results.parquet")
    monthly = pd.read_parquet(DATA_DIR / "backtest_monthly.parquet")
    fm = pd.read_parquet(DATA_DIR / "fama_macbeth.parquet")

    # ---- 1. ESG panel (all years, for map + drilldown) ----
    panel_out = []
    for _, row in panel.iterrows():
        panel_out.append(
            {
                "iso3": row["iso3"],
                "country": COUNTRIES.get(row["iso3"], row["iso3"]),
                "year": int(row["year"]),
                "scoreEqual": None if pd.isna(row.get("score_equal")) else round(float(row["score_equal"]), 1),
                "scorePca": None if pd.isna(row.get("score_pca")) else round(float(row["score_pca"]), 1),
                "pillarE": None if pd.isna(row.get("pillar_E")) else round(float(row["pillar_E"]), 1),
                "pillarS": None if pd.isna(row.get("pillar_S")) else round(float(row["pillar_S"]), 1),
                "pillarG": None if pd.isna(row.get("pillar_G")) else round(float(row["pillar_G"]), 1),
            }
        )

    # ---- 2. Annual + monthly metrics ----
    annual_metrics = summary_table(annual, benchmark_col=BENCHMARK)
    monthly_m = monthly_metrics(monthly, benchmark_col=BENCHMARK)

    def metrics_to_records(df: pd.DataFrame, freq: str) -> list[dict]:
        out = []
        for portfolio, row in df.iterrows():
            rec = {"portfolio": portfolio, "frequency": freq}
            for k, v in row.items():
                label = METRIC_LABELS.get(k, k)
                rec[label] = None if pd.isna(v) else round(float(v), 4)
            out.append(rec)
        return out

    # ---- 3. Growth + drawdown series (both frequencies) ----
    def growth_dd(rets: pd.DataFrame) -> dict:
        out = {}
        for col in rets.columns:
            r = rets[col].dropna()
            growth = (1 + r).cumprod()
            dd = drawdown_series(r)
            out[col] = {
                "labels": [str(i) for i in r.index],
                "growth": [round(float(x), 4) for x in growth],
                "drawdown": [round(float(x) * 100, 2) for x in dd],  # percent
            }
        return out

    # ---- 4. Weights (latest year) per portfolio + composition ----
    wdf = weight_panel(panel)
    comp = composition_summary(wdf)
    latest_year = int(wdf["hold_year"].max())
    latest_weights = {}
    for name, g in wdf[wdf["hold_year"] == latest_year].groupby("portfolio"):
        latest_weights[name] = {
            row["iso3"]: round(float(row["weight"]), 4)
            for _, row in g.iterrows()
        }

    # ---- 5. Significance ----
    sig_annual = compare_portfolios(annual, benchmark_col=BENCHMARK)
    sig_monthly = compare_portfolios(monthly, benchmark_col=BENCHMARK)

    def sig_to_records(df: pd.DataFrame, freq: str) -> list[dict]:
        out = []
        for strat, row in df.iterrows():
            out.append(
                {
                    "strategy": strat,
                    "frequency": freq,
                    "volDiff": round(float(row["vol_diff"]), 5),
                    "volP": round(float(row["vol_p"]), 4),
                    "volCI": [round(float(row["vol_CI95"][0]), 5), round(float(row["vol_CI95"][1]), 5)],
                    "meanRetDiff": round(float(row["mean_ret_diff"]), 5),
                    "meanRetP": round(float(row["mean_ret_p"]), 4),
                    "meanRetCI": [
                        round(float(row["mean_ret_CI95"][0]), 5),
                        round(float(row["mean_ret_CI95"][1]), 5),
                    ],
                }
            )
        return out

    # ---- 6. Fama-MacBeth ----
    g = fm["gamma"].dropna()
    fm_summary = {
        "nMonths": int(len(g)),
        "gammaMean": round(float(g.mean()), 6),
        "gammaStd": round(float(g.std(ddof=1)), 6),
        "tStat": round(float(g.mean() / g.std(ddof=1)), 3),  # plain t; NW reported in report
        "series": {
            "labels": _periods_to_str(g.index),
            "gamma": [round(float(x), 6) for x in g],
            "cumGamma": [round(float(x), 6) for x in g.cumsum()],
        },
    }
    # Newey-West t (recompute for the bundle)
    from mobilize.backtest.fama_macbeth import NW_LAGS_FRAC

    n = len(g)
    lags = max(1, int(n * NW_LAGS_FRAC))
    g_c = (g - g.mean()).to_numpy()
    lr_var = float((g_c**2).mean()) / n
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1)
        lr_var += 2 * w * float((g_c[:-L] * g_c[L:]).mean()) / n
    from math import erfc

    t_nw = float(g.mean() / np.sqrt(max(lr_var, 1e-18)))
    fm_summary["tNeweyWest"] = round(t_nw, 3)
    fm_summary["pValue"] = round(float(erfc(abs(t_nw) / np.sqrt(2))), 4)

    # ---- 7. Headline findings (pre-written, displayed on landing) ----
    findings = {
        "volReduction": {
            "tilted_vs_benchmark_annualized_pp": -0.7,
            "p_value": "<0.001",
            "statement": "ESG tilting significantly reduces portfolio volatility (~0.7pp annualized).",
        },
        "returnCost": {
            "estimate_pp_per_year": -0.1,
            "p_value": "0.25-0.35",
            "statement": "The tilt's return cost is small and not statistically distinguishable from zero.",
        },
        "drawdowns": {
            "statement": "Max drawdowns are near-identical across portfolios; ESG tilting did not limit the worst loss.",
        },
        "pricing": {
            "gamma_bp_per_month": -28.2,
            "t_newey_west": -0.91,
            "p_value": 0.36,
            "statement": "The sovereign ESG score is not significantly priced in returns (Fama-MacBeth).",
        },
    }

    bundle = {
        "meta": {
            "universe": 35,
            "window": "2013-2023",
            "benchmark": BENCHMARK,
            "portfolios": sorted(annual.columns.tolist()),
            "latestWeightsYear": latest_year,
            "generated": pd.Timestamp.now().isoformat(),
        },
        "panel": panel_out,
        "metrics": metrics_to_records(annual_metrics, "annual")
        + metrics_to_records(monthly_m, "monthly"),
        "series": {"annual": growth_dd(annual), "monthly": growth_dd(monthly)},
        "weights": latest_weights,
        "composition": [
            {
                "portfolio": r["portfolio"],
                "holdYear": int(r["hold_year"]),
                "nHoldings": int(r["n_holdings"]),
                "effectiveN": round(float(r["effective_n"]), 2),
                "maxWeight": round(float(r["max_weight"]), 4),
            }
            for _, r in comp.iterrows()
        ],
        "significance": sig_to_records(sig_annual, "annual") + sig_to_records(sig_monthly, "monthly"),
        "famaMacbeth": fm_summary,
        "findings": findings,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(bundle, allow_nan=False))
    size_kb = OUT.stat().st_size / 1024
    print(f"dashboard.json written: {OUT} ({size_kb:.0f} KB)")
    print(f"  panel rows: {len(panel_out)}")
    print(f"  portfolio series: {list(annual.columns)}")
    print(f"  fama-macbeth months: {fm_summary['nMonths']}")


if __name__ == "__main__":
    main()
