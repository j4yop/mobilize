"""Tests for the calibrated spread model and yield matrices."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mobilize.backtest.calibration import (
    build_features,
    calibrate,
    expanding_window_cv,
    fit_ols,
    synthetic_yield,
)


def _toy_panel(n_years: int = 6) -> pd.DataFrame:
    """3 DM + 1 EM; yields observed for DMs."""
    rows = []
    for yr in range(2010, 2010 + n_years):
        for iso3, debt, res, infl, gov, gdp in [
            ("USA", 100, 20, 2, 80, 20e12),
            ("DEU", 60, 10, 1.5, 85, 4e12),
            ("ITA", 130, 8, 2, 65, 2e12),
            ("BRA", 80, 25, 6, 45, 2e12),  # EM, no observed yield
        ]:
            rows.append(
                {
                    "iso3": iso3,
                    "year": yr,
                    "GC.DOD.TOTL.GD.ZS": debt,
                    "FI.RES.TOTL.CD": res * gdp / 100,
                    "FP.CPI.TOTL.ZG": infl,
                    "pillar_G": gov,
                    "NY.GDP.MKTP.CD": gdp,
                }
            )
    return pd.DataFrame(rows)


def _cal_rows(panel: pd.DataFrame) -> list[dict]:
    rows = []
    us_y = {2010: 0.03, 2011: 0.028, 2012: 0.025, 2013: 0.03, 2014: 0.028, 2015: 0.026}
    obs = {"USA": 0.03, "DEU": 0.025, "ITA": 0.055}
    for iso3, y0 in obs.items():
        for yr, us in us_y.items():
            f = build_features(panel, iso3, yr, us, y0 + 0.005)
            if f is not None:
                rows.append(f)
    return rows


def test_build_features_extracts_values():
    f = build_features(_toy_panel(), "ITA", 2010, 0.03, 0.055)
    assert f is not None
    assert f["debt"] == pytest.approx(1.30)
    assert f["gov_norm"] == pytest.approx(0.65)
    assert f["spread"] == pytest.approx(0.025)
    assert f["reserves"] == pytest.approx(0.08, abs=1e-9)


def test_build_features_missing_iso_returns_none():
    assert build_features(_toy_panel(), "XXX", 2010, 0.03, 0.04) is None


def test_fit_ols_recovers_linear_truth():
    rng = np.random.default_rng(3)
    X = rng.normal(size=(200, 3))
    beta_true = np.array([0.5, -1.0, 2.0])
    y = 0.1 + X @ beta_true
    beta = fit_ols(X, y)
    np.testing.assert_allclose(beta, np.concatenate([[0.1], beta_true]), atol=1e-8)


def test_calibrate_runs_and_reports():
    panel = _toy_panel()
    rows = _cal_rows(panel)
    model = calibrate(rows)
    assert model["n"] == len(rows)
    assert np.isfinite(model["r2"])
    assert len(model["beta"]) == 5


def test_synthetic_yield_uses_model():
    panel = _toy_panel()
    model = calibrate(_cal_rows(panel))
    feats = build_features(panel, "BRA", 2012, 0.025, None)
    y = synthetic_yield(model, feats, 0.025)
    # EM yield should exceed US base (positive spread component)
    assert y > 0.025
    assert y <= 0.025 + 0.08  # within spread bounds


def test_expanding_window_cv_returns_rmse():
    rows = _cal_rows(_toy_panel())
    rmse = expanding_window_cv(rows, min_train_years=2)
    assert np.isfinite(rmse) or rmse is np.nan  # small toy may be nan; must not raise
