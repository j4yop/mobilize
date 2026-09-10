"""Tests for portfolio construction (weights + no-look-ahead)."""

from __future__ import annotations

import pandas as pd
import pytest

from mobilize.portfolio.construction import (
    BENCHMARK,
    SCREENED,
    TILTED,
    composition_summary,
    weight_panel,
    weights_for_year,
)


def _panel() -> pd.DataFrame:
    """Tiny panel: 6 countries, GDP and scores for 2012-2014.

    C1..C6 have scores 100,80,60,40,20,10 in 2012 and identical in 2013.
    GDP: 30,20,15,12,10,8 (so benchmark weights vary).
    """
    rows = []
    gdp = [30.0, 20.0, 15.0, 12.0, 10.0, 8.0]
    scores = [100.0, 80.0, 60.0, 40.0, 20.0, 10.0]
    for i in range(6):
        for year in (2012, 2013):
            rows.append(
                {
                    "iso3": f"C{i+1}",
                    "year": year,
                    "NY.GDP.MKTP.CD": gdp[i],
                    "score_equal": scores[i],
                }
            )
    return pd.DataFrame(rows)


def test_benchmark_weights_sum_to_one_and_follow_gdp():
    w = weights_for_year(_panel(), hold_year=2013)
    assert set(w) == {BENCHMARK, TILTED, SCREENED}
    b = w[BENCHMARK]
    assert b.sum() == pytest.approx(1.0)
    assert b.loc["C1"] == pytest.approx(30.0 / 95.0)


def test_no_lookahead_uses_only_prior_year_scores():
    # Change scores in 2013 completely: weights for hold_year=2013 must not move
    p = _panel()
    p.loc[p["year"] == 2013, "score_equal"] = [10, 20, 40, 60, 80, 100]
    w_a = weights_for_year(_panel(), hold_year=2013)
    w_b = weights_for_year(p, hold_year=2013)
    pd.testing.assert_series_equal(w_a[TILTED], w_b[TILTED])


def test_tilt_overweights_high_scorers():
    w = weights_for_year(_panel(), hold_year=2013)
    t = w[TILTED]
    b = w[BENCHMARK]
    assert t.loc["C1"] > b.loc["C1"]  # highest scorer gets more than benchmark
    assert t.loc["C6"] < b.loc["C6"]  # lowest scorer gets less


def test_screened_drops_bottom_quintile():
    w = weights_for_year(_panel(), hold_year=2013)
    s = w[SCREENED]
    # bottom 20% of 6 countries by score -> C6 (score 10) excluded
    assert "C6" not in s.index
    assert "C1" in s.index
    assert s.sum() == pytest.approx(1.0)


def test_weight_panel_covers_all_years_and_portfolios():
    wp = weight_panel(_panel(), start_year=2013, end_year=2014)
    assert set(wp["portfolio"]) == {BENCHMARK, TILTED, SCREENED}
    assert set(wp["hold_year"]) == {2013, 2014}
    for _key, g in wp.groupby(["portfolio", "hold_year"]):
        assert g["weight"].sum() == pytest.approx(1.0, abs=1e-8)


def test_composition_summary_effective_n():
    wp = weight_panel(_panel(), start_year=2013, end_year=2013)
    comp = composition_summary(wp)
    bench_row = comp[comp["portfolio"] == BENCHMARK].iloc[0]
    # 6 countries, unequal GDP weights -> effective N between 1 and 6
    assert 1 < bench_row["effective_n"] < 6
    assert bench_row["n_holdings"] == 6


def test_empty_panel_returns_empty():
    assert weights_for_year(pd.DataFrame(), hold_year=2013) == {}
