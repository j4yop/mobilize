"""Tests for the keyless FRED csv client (parsing logic, offline)."""

from __future__ import annotations

import pandas as pd
import pytest

from mobilize.data.fred import FREDError, fetch_series


class _FakeResp:
    def __init__(self, text: str, status: int = 200):
        self.text = text
        self.status_code = status

    def raise_for_status(self):
        if self.status_code != 200:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_fetch_series_parses_csv(monkeypatch):
    csv = "DATE,DGS5\n2024-01-01,3.90\n2024-01-02,\n2024-01-03,3.95\n"
    monkeypatch.setattr(
        "mobilize.data.fred.requests.Session.get",
        lambda self, url, params, timeout: _FakeResp(csv),
    )
    df = fetch_series("DGS5")
    assert list(df.columns) == ["date", "value"]
    assert len(df) == 3
    assert pd.isna(df["value"].iloc[1])
    assert df["value"].iloc[2] == 3.95


def test_fetch_series_http_error(monkeypatch):
    monkeypatch.setattr(
        "mobilize.data.fred.requests.Session.get",
        lambda self, url, params, timeout: _FakeResp("boom", status=503),
    )
    with pytest.raises(FREDError):
        fetch_series("DGS5")
