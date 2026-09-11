"""Tests for monthly engine and Fama-MacBeth."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mobilize.backtest.fama_macbeth import monthly_fama_macbeth
from mobilize.backtest.monthly import (
    annualize_return,
    annualize_vol,
    map_annual_weights_to_months,
    monthly_metrics,
    monthly_returns_from_yields,
    portfolio_monthly_returns,
)


def _months(n: int = 24) -> pd.PeriodIndex:
    return pd.period_range("2018-01", periods=n, freq="M")


def test_monthly_return_formula():
    # flat yield at 6% annual -> monthly carry = 6%/12 = 0.5%, no capital gain
    idx = _months(3)
    y = pd.DataFrame({"A": [0.06, 0.06, 0.06]}, index=idx)
    r = monthly_returns_from_yields(y)
    assert r["A"].iloc[0] == pytest.approx(0.06 / 12)

    # yield falls 1% in one month: carry 0.5% + full-duration gain 8%
    y2 = pd.DataFrame({"A": [0.06, 0.05, 0.05]}, index=idx)
    r2 = monthly_returns_from_yields(y2)
    assert r2["A"].iloc[0] == pytest.approx(0.06 / 12 + 8.0 * 0.01)


def test_annualize_return_and_vol():
    rng = np.random.default_rng(0)
    r = pd.Series(rng.normal(0.005, 0.02, 60))
    ar = annualize_return(r)
    av = annualize_vol(r)
    assert -1 < ar < 0.5
    assert av == pytest.approx(r.std(ddof=1) * np.sqrt(12), rel=1e-9)
    # constant 1% monthly compounds to (1.01^12 - 1) annual
    r_c = pd.Series([0.01] * 12)
    assert annualize_return(r_c) == pytest.approx(1.01**12 - 1)


def test_map_annual_weights_to_months():
    wdf = pd.DataFrame(
        [
            {"portfolio": "p", "hold_year": 2018, "iso3": "A", "weight": 0.5},
            {"portfolio": "p", "hold_year": 2018, "iso3": "B", "weight": 0.5},
        ]
    )
    months = pd.period_range("2018-01", "2018-12", freq="M")
    out = map_annual_weights_to_months(wdf, months)
    assert len(out) == 24
    jan = out[out["month"] == months[0]]
    assert jan["weight"].sum() == pytest.approx(1.0)


def test_portfolio_monthly_returns_weighting():
    months = _months(2)
    rets = pd.DataFrame(
        {"A": {months[0]: 0.01, months[1]: 0.02}, "B": {months[0]: 0.0, months[1]: 0.0}}
    )
    wm = pd.DataFrame(
        [
            {"portfolio": "p", "month": months[0], "iso3": "A", "weight": 0.5},
            {"portfolio": "p", "month": months[0], "iso3": "B", "weight": 0.5},
            {"portfolio": "p", "month": months[1], "iso3": "A", "weight": 0.5},
            {"portfolio": "p", "month": months[1], "iso3": "B", "weight": 0.5},
        ]
    )
    out = portfolio_monthly_returns(rets, wm)
    assert out.loc[months[0], "p"] == pytest.approx(0.005)
    assert out.loc[months[1], "p"] == pytest.approx(0.01)


def test_monthly_metrics_shape():
    months = _months(36)
    rng = np.random.default_rng(1)
    df = pd.DataFrame(
        {
            "benchmark": rng.normal(0.004, 0.02, 36),
            "esg_tilted": rng.normal(0.003, 0.015, 36),
        },
        index=months,
    )
    t = monthly_metrics(df, benchmark_col="benchmark")
    assert {"ann_return", "ann_vol", "sharpe", "max_drawdown"} <= set(t.columns)
    assert t.loc["esg_tilted", "ann_vol"] < t.loc["benchmark", "ann_vol"]


# ---------------- Fama-MacBeth ----------------

def _fm_panel() -> pd.DataFrame:
    rows = []
    # scores: A=90, B=50, C=10 across years 2017-2020 (stable)
    for yr in (2017, 2018):
        for iso3, s in [("A", 90.0), ("B", 50.0), ("C", 10.0)] + [
            (f"D{i}", 30.0 + 10 * i) for i in range(5)
        ]:
            rows.append({"iso3": iso3, "year": yr, "score_equal": s})
    return pd.DataFrame(rows)


def test_fama_macbeth_detects_priced_factor():
    months = pd.period_range("2018-01", "2019-12", freq="M")
    rng = np.random.default_rng(2)
    base = {"A": 0.002, "B": 0.004, "C": 0.006}
    data = {}
    for iso3 in ["A", "B", "C"]:
        data[iso3] = [base[iso3] + rng.normal(0, 0.001) for _ in months]
    for i in range(5):
        data[f"D{i}"] = [0.004 + rng.normal(0, 0.001) for _ in months]
    rets = pd.DataFrame(data, index=months)
    panel = _fm_panel()
    fm = monthly_fama_macbeth(rets, panel)
    # high score (A=90) earns LOW return -> negative gamma
    assert fm["gamma_mean"] < 0
    assert fm["n_months"] >= 12


def test_fama_macbeth_null_when_unpriced():
    months = pd.period_range("2018-01", "2019-12", freq="M")
    rng = np.random.default_rng(3)
    rets = pd.DataFrame(
        {iso3: rng.normal(0.003, 0.001, len(months)) for iso3 in ["A", "B", "C"]}
        | {f"D{i}": rng.normal(0.003, 0.001, len(months)) for i in range(5)},
        index=months,
    )
    panel = _fm_panel()
    fm = monthly_fama_macbeth(rets, panel)
    # scores explain nothing -> |t| should be smallish, p large
    assert fm["p"] > 0.05 or abs(fm["t_nw"]) < 2
