"""Tests for the cleaning protocol."""

from __future__ import annotations

import numpy as np
import pandas as pd

from mobilize.data.clean import (
    coverage_matrix,
    drop_low_coverage,
    interpolate_short_gaps,
    winsorize_cross_section,
)


def _toy() -> pd.DataFrame:
    # USA has a 1-year gap in X; BRA has mostly-missing X
    return pd.DataFrame(
        {
            "iso3": ["USA"] * 5 + ["BRA"] * 5,
            "year": [2019, 2020, 2021, 2022, 2023] * 2,
            "X": [1.0, np.nan, 3.0, 4.0, 5.0] + [1.0, np.nan, np.nan, np.nan, 2.0],
            "Y": list(range(5)) + list(range(5, 10)),
        }
    )


def test_interpolate_short_gaps_fills_one_year_gap():
    out = interpolate_short_gaps(_toy(), ["X", "Y"])
    usa_x = out[(out["iso3"] == "USA")].set_index("year")["X"]
    assert usa_x.loc[2020] == 2.0  # linear interp between 1 and 3


def test_interpolate_does_not_fill_long_gaps():
    out = interpolate_short_gaps(_toy(), ["X", "Y"], gap_limit=2)
    bra_x = out[(out["iso3"] == "BRA")].set_index("year")["X"]
    # BRA X = [1.0, nan, nan, nan, 2.0]: forward-fill with limit=2 fills only
    # the first two NaNs of the run; 2022 stays NaN (effective gap of 3 > 2)
    assert pd.isna(bra_x.loc[2022]) and bra_x.loc[2023] == 2.0


def test_coverage_matrix_and_drop():
    df = _toy()
    cov = coverage_matrix(df, ["X", "Y"])
    assert cov.loc["USA", "X"] == 0.8
    assert cov.loc["BRA", "X"] == 0.4
    out = drop_low_coverage(df, ["X", "Y"], min_coverage=0.5)
    bra_x = out[(out["iso3"] == "BRA")]["X"]
    assert bra_x.isna().all()
    usa_x = out[(out["iso3"] == "USA")]["X"]
    # USA X coverage is 0.8 >= 0.5, so observed values are kept (incl. its NaN year)
    assert usa_x.notna().sum() == 4


def test_winsorize_clips_extremes():
    df = pd.DataFrame(
        {
            "iso3": [f"C{i}" for i in range(100)],
            "year": [2020] * 100,
            "X": list(range(100)),
        }
    )
    out = winsorize_cross_section(df, ["X"])
    lo, hi = out["X"].min(), out["X"].max()
    assert lo > 0 and hi < 99  # clipped at 1%/99%
