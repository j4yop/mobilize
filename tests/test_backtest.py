"""Tests for the returns proxy engine and risk metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mobilize.backtest.metrics import (
    cagr,
    cvar_historical,
    drawdown_series,
    max_drawdown,
    sharpe,
    sortino,
    summary_table,
    var_historical,
)
from mobilize.backtest.returns import (
    duration_proxy_return,
    portfolio_annual_returns,
)
from mobilize.backtest.significance import compare_portfolios

# ---------------- returns proxy ----------------

def test_duration_proxy_return_formula():
    # carry 5%, yields flat -> return = 5%
    assert duration_proxy_return(0.05, 0.05) == pytest.approx(0.05)
    # yields fall 1% with D=8 -> return = 5% + 8% = 13%
    assert duration_proxy_return(0.05, 0.04, duration=8.0) == pytest.approx(0.13)
    # yields rise 1% -> return = 5% - 8% = -3%
    assert duration_proxy_return(0.05, 0.06, duration=8.0) == pytest.approx(-0.03)


def test_portfolio_annual_returns_weighting():
    yields_rets = pd.DataFrame(
        {"C1": {2013: 0.10}, "C2": {2013: 0.00}}
    )
    yields_rets.index.name = "year"
    wdf = pd.DataFrame(
        [
            {"portfolio": "p", "hold_year": 2013, "iso3": "C1", "weight": 0.75},
            {"portfolio": "p", "hold_year": 2013, "iso3": "C2", "weight": 0.25},
        ]
    )
    out = portfolio_annual_returns(yields_rets, wdf)
    assert out.loc[2013, "p"] == pytest.approx(0.075)


# ---------------- metrics ----------------

def _rets(seq):
    return pd.Series(seq, index=range(2013, 2013 + len(seq)), dtype=float)


def test_cagr_matches_geometric_mean():
    r = _rets([0.10, 0.10, 0.10])
    assert cagr(r) == pytest.approx(0.10)
    r2 = _rets([0.20, -0.20])
    growth = 1.2 * 0.8
    assert cagr(r2) == pytest.approx(growth**0.5 - 1)


def test_max_drawdown_and_series():
    r = _rets([0.10, -0.20, 0.05, 0.30])
    dd = drawdown_series(r)
    # peak after year1 = 1.1; trough = 1.1*0.8 = 0.88 -> dd = -0.2
    assert dd.iloc[1] == pytest.approx(-0.2)
    assert max_drawdown(r) == pytest.approx(-0.2)


def test_var_cvar_historical():
    r = _rets(sorted([0.01, 0.02, 0.03, 0.04, 0.05, -0.10, -0.05, 0.06, 0.07, 0.08]))
    v = var_historical(r, alpha=0.05)
    c = cvar_historical(r, alpha=0.05)
    assert c <= v  # tail mean is at least as extreme as the quantile


def test_sharpe_and_sortino_signs():
    good = _rets([0.08, 0.09, 0.10, 0.11])
    bad = _rets([0.02, 0.05, -0.10, 0.02])
    assert sharpe(good) > sharpe(bad)
    assert sortino(good) > sortino(bad)


def test_summary_table_shape():
    df = pd.DataFrame(
        {
            "benchmark": _rets([0.05, 0.03, 0.04, 0.06]),
            "esg_tilted": _rets([0.06, 0.03, 0.05, 0.07]),
        }
    )
    t = summary_table(df, benchmark_col="benchmark")
    assert "downside_capture" in t.columns
    assert t.loc["benchmark", "CAGR"] == pytest.approx(
        (1.05 * 1.03 * 1.04 * 1.06) ** 0.25 - 1
    )


# ---------------- significance ----------------

def test_bootstrap_rejects_when_clearly_different():
    # strategy consistently beats benchmark -> two-sided p on mean should be tiny
    rng = np.random.default_rng(0)
    strat = pd.Series(rng.normal(0.10, 0.02, 24))
    bench = pd.Series(rng.normal(0.01, 0.02, 24))
    from mobilize.backtest.significance import bootstrap_mean_test
    obs, p, ci = bootstrap_mean_test(strat - bench, n_boot=2000)
    assert obs > 0.05
    assert p < 0.01
    assert ci[0] > 0  # CI excludes zero


def test_bootstrap_null_when_identical():
    from mobilize.backtest.significance import bootstrap_mean_test
    r = np.random.default_rng(1).normal(0, 0.02, 24)
    obs, p, _ = bootstrap_mean_test(pd.Series(r) - pd.Series(r), n_boot=2000)
    assert obs == pytest.approx(0.0)
    assert p >= 0.99  # identical series -> max p-value


def test_vol_statistic_detects_vol_difference():
    # same mean, different vol -> permutation p should be significant
    from mobilize.backtest.significance import permutation_vol_test
    rng = np.random.default_rng(2)
    calm = pd.Series(rng.normal(0.05, 0.01, 30))
    wild = pd.Series(rng.normal(0.05, 0.05, 30))
    obs, p, ci = permutation_vol_test(wild, calm, n_perm=2000)
    assert obs > 0  # wild is more volatile
    assert p < 0.05


def test_compare_portfolios_runs():
    df = pd.DataFrame(
        {
            "benchmark": _rets([0.05, 0.03, 0.04, 0.06, 0.02, 0.05]),
            "esg_tilted": _rets([0.06, 0.04, 0.03, 0.05, 0.03, 0.06]),
        }
    )
    out = compare_portfolios(df, benchmark_col="benchmark")
    assert "esg_tilted" in out.index
    assert out.loc["esg_tilted", "vol_p"] >= 0
    assert 0 <= out.loc["esg_tilted", "mean_ret_p"] <= 1
