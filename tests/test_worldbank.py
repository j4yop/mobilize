"""Tests for the World Bank API client (offline: parsing/shape logic)."""

from __future__ import annotations

import pandas as pd

from mobilize.data.worldbank import wide


def test_wide_pivot_shape():
    tidy = pd.DataFrame(
        [
            {"iso3": "USA", "country": "United States", "year": 2020, "indicator": "EN.ATM.CO2E.PC", "value": 14.0},
            {"iso3": "USA", "country": "United States", "year": 2020, "indicator": "SP.POP.LE00.IN", "value": 78.0},
            {"iso3": "BRA", "country": "Brazil", "year": 2020, "indicator": "EN.ATM.CO2E.PC", "value": 2.0},
        ]
    )
    out = wide(tidy)
    assert set(out.columns) >= {"iso3", "year", "EN.ATM.CO2E.PC", "SP.POP.LE00.IN"}
    usa = out[out["iso3"] == "USA"].iloc[0]
    assert usa["EN.ATM.CO2E.PC"] == 14.0
    # Brazil missing LE00 -> NaN, not dropped row
    bra = out[out["iso3"] == "BRA"].iloc[0]
    assert pd.isna(bra["SP.POP.LE00.IN"])


def test_wide_drops_null_values():
    tidy = pd.DataFrame(
        [
            {"iso3": "USA", "country": "United States", "year": 2020, "indicator": "X", "value": None},
        ]
    )
    assert len(wide(tidy)) == 0
