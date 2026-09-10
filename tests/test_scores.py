"""Tests for the scoring pipeline (direction, normalization, composites)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mobilize.data.indicators import INDICATORS
from mobilize.scoring.scores import (
    apply_direction,
    build_scores,
    composite_equal_weight,
    minmax_by_year,
    pillar_scores,
)

META = {
    "CO2": {"pillar": "E", "name": "co2", "direction": -1},
    "REN": {"pillar": "E", "name": "ren", "direction": +1},
    "LE": {"pillar": "S", "name": "le", "direction": +1},
    "GINI": {"pillar": "S", "name": "gini", "direction": -1},
    "RL": {"pillar": "G", "name": "rule of law", "direction": +1},
    "VA": {"pillar": "G", "name": "voice", "direction": +1},
}


def _toy(n_countries: int = 8) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    rows = []
    for i in range(n_countries):
        for year in (2020, 2021):
            rows.append(
                {
                    "iso3": f"C{i:02d}",
                    "year": year,
                    "CO2": rng.uniform(1, 20),
                    "REN": rng.uniform(0, 60),
                    "LE": rng.uniform(55, 85),
                    "GINI": rng.uniform(25, 60),
                    "RL": rng.uniform(-2, 2),
                    "VA": rng.uniform(-2, 2),
                }
            )
    return pd.DataFrame(rows)


def test_apply_direction_inverts_worse_is_higher():
    df = pd.DataFrame({"CO2": [5.0], "REN": [10.0]})
    out = apply_direction(df, META, ["CO2", "REN"])
    assert out["CO2"].iloc[0] == -5.0
    assert out["REN"].iloc[0] == 10.0


def test_apply_direction_rejects_macro_controls():
    df = pd.DataFrame({"GDP": [1.0]})
    with pytest.raises(ValueError):
        apply_direction(df, {"GDP": {"pillar": "MACRO", "direction": 0}}, ["GDP"])


def test_minmax_bounds():
    df = _toy(6)
    cols = list(META.keys())
    out = minmax_by_year(df, cols)
    for year in (2020, 2021):
        sub = out[out["year"] == year]
        for col in cols:
            assert sub[col].min() == pytest.approx(0.0, abs=1e-9)
            assert sub[col].max() == pytest.approx(1.0, abs=1e-9)


def test_pillar_scores_range():
    df = minmax_by_year(_toy(), list(META.keys()))
    out = pillar_scores(df, META, list(META.keys()))
    for p in ("E", "S", "G"):
        col = out[f"pillar_{p}"]
        assert col.between(0, 100).all()


def test_composite_equal_weight_uses_all_pillars():
    df = minmax_by_year(_toy(), list(META.keys()))
    out = pillar_scores(df, META, list(META.keys()))
    out = composite_equal_weight(out)
    expected = out[["pillar_E", "pillar_S", "pillar_G"]].mean(axis=1)
    pd.testing.assert_series_equal(out["score_equal"], expected, check_names=False)

def test_build_scores_end_to_end_runs():
    df = _toy()
    out = build_scores(df, META)
    for col in ("pillar_E", "pillar_S", "pillar_G", "score_equal", "score_pca"):
        assert col in out.columns
    # PCA requires >=5 countries with complete rows -> all 8 qualify
    assert out["score_pca"].notna().all()
    assert out["score_equal"].between(0, 100).all()


def test_real_indicator_metadata_is_consistent():
    for code, meta in INDICATORS.items():
        assert meta["pillar"] in ("E", "S", "G", "MACRO"), code
        assert meta["direction"] in (-1, 0, +1), code
        if meta["pillar"] in ("E", "S", "G"):
            assert meta["direction"] != 0, f"scored indicator must have direction: {code}"
