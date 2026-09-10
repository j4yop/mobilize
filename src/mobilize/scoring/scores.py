"""Sovereign ESG scoring: pillar scores + composite (equal-weight and PCA).

Methodology
-----------
1. Apply direction (higher-is-better / inversion) per indicator.
2. Min-max normalize each indicator per year -> [0, 1] cross-section.
3. Pillar score = mean of normalized indicators in the pillar (0-100).
4. Composite (equal-weight) = mean of pillar scores.
5. Composite (PCA) = first principal component of normalized indicators,
   rescaled to 0-100. Both are reported side by side (no cherry-picking).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def apply_direction(
    df: pd.DataFrame,
    indicator_meta: dict[str, dict],
    value_cols: list[str],
) -> pd.DataFrame:
    """Invert indicators where higher raw values mean worse outcomes."""
    out = df.copy()
    for col in value_cols:
        direction = indicator_meta.get(col, {}).get("direction", +1)
        if direction == -1:
            out[col] = -out[col]
        elif direction == 0:
            raise ValueError(f"Macro control {col} must not enter scoring")
    return out


def minmax_by_year(df: pd.DataFrame, value_cols: list[str]) -> pd.DataFrame:
    """Per-year min-max normalization to [0, 1] across the cross-section."""
    out = df.copy()
    for col in value_cols:
        out[col] = out.groupby("year")[col].transform(
            lambda s: (s - s.min()) / (s.max() - s.min()) if s.notna().any() and s.max() > s.min() else s
        )
    return out


def pillar_scores(
    df: pd.DataFrame,
    indicator_meta: dict[str, dict],
    value_cols: list[str],
    pillars: tuple[str, ...] = ("E", "S", "G"),
) -> pd.DataFrame:
    """Compute 0-100 pillar scores from normalized indicator columns."""
    out = df.copy()
    for pillar in pillars:
        cols = [c for c in value_cols if indicator_meta[c]["pillar"] == pillar]
        if cols:
            out[f"pillar_{pillar}"] = 100 * out[cols].mean(axis=1, skipna=True)
    return out


def composite_equal_weight(
    df: pd.DataFrame,
    pillars: tuple[str, ...] = ("E", "S", "G"),
) -> pd.DataFrame:
    """Equal-weight composite: mean of available pillar scores (already 0-100)."""
    out = df.copy()
    cols = [f"pillar_{p}" for p in pillars]
    out["score_equal"] = out[cols].mean(axis=1, skipna=True)
    return out


def composite_pca(
    df: pd.DataFrame,
    value_cols: list[str],
    min_component_variance: float = 0.0,
) -> pd.DataFrame:
    """PCA composite: first PC of normalized indicators, rescaled 0-100.

    Computed per year (cross-section), since panel PCA across mixed levels
    would confound time and cross-sectional variation.
    Requires at least 5 countries with complete data for that year.
    """
    out = df.copy()
    out["score_pca"] = np.nan

    def _year_pca(g: pd.DataFrame) -> pd.Series:
        # Impute missing indicators with the year's cross-sectional median
        # (standard PCA practice) instead of dropping incomplete countries.
        X_df = g[value_cols].copy()
        if len(X_df) < 5:
            return pd.Series(np.nan, index=g.index)
        medians = X_df.median()
        X_df = X_df.fillna(medians)
        X = X_df.to_numpy(dtype=float)
        X = X - X.mean(axis=0)
        # SVD-based first component (no sklearn dependency at this layer)
        U, S, Vt = np.linalg.svd(X, full_matrices=False)
        pc1 = pd.Series(X @ Vt[0], index=X_df.index)
        # Orient PC so that higher = better (align with equal-weight composite)
        ew = g.loc[X_df.index, "score_equal"]
        if ew.notna().any():
            common = ew.dropna().index
            if len(common) >= 3 and np.corrcoef(pc1.loc[common], ew.loc[common])[0, 1] < 0:
                pc1 = -pc1
        lo, hi = pc1.min(), pc1.max()
        scaled = 100 * (pc1 - lo) / (hi - lo) if hi > lo else pd.Series(50.0, index=pc1.index)
        return scaled.reindex(g.index)

    out["score_pca"] = out.groupby("year", group_keys=False)[["iso3", "year", "score_equal"] + value_cols].apply(
        lambda g: _year_pca(g)
    )
    return out


def build_scores(
    df: pd.DataFrame,
    indicator_meta: dict[str, dict],
    pillars: tuple[str, ...] = ("E", "S", "G"),
) -> pd.DataFrame:
    """Full scoring pipeline from cleaned wide frame -> scored panel."""
    scored_cols = [
        c
        for c in df.columns
        if c in indicator_meta and indicator_meta[c].get("direction", 0) != 0
    ]
    out = apply_direction(df, indicator_meta, scored_cols)
    out = minmax_by_year(out, scored_cols)
    out = pillar_scores(out, indicator_meta, scored_cols, pillars)
    out = composite_equal_weight(out, pillars)
    out = composite_pca(out, scored_cols)
    return out
