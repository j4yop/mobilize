"""Build the sovereign ESG panel: fetch -> clean -> score -> cache.

Run via `make data`. Outputs parquet caches under data/.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from mobilize.data.clean import (  # noqa: E402
    drop_low_coverage,
    interpolate_short_gaps,
    winsorize_cross_section,
)
from mobilize.data.indicators import (  # noqa: E402
    COUNTRIES,
    END_YEAR,
    INDICATORS,
    PANEL_START_YEAR,
)
from mobilize.data.worldbank import WorldBankClient, wide  # noqa: E402
from mobilize.scoring.scores import build_scores  # noqa: E402

DATA_DIR = REPO_ROOT / "data"
RAW_PATH = DATA_DIR / "raw" / "wb_indicators.parquet"
PANEL_PATH = DATA_DIR / "processed" / "esg_panel.parquet"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "raw").mkdir(exist_ok=True)
    (DATA_DIR / "processed").mkdir(exist_ok=True)

    iso3s = list(COUNTRIES.keys())
    codes = list(INDICATORS.keys())

    print(f"[1/4] Fetching {len(codes)} indicators for {len(iso3s)} countries, "
          f"{PANEL_START_YEAR - 2}-{END_YEAR} ...")
    client = WorldBankClient()
    tidy = client.fetch_many(codes, iso3s, PANEL_START_YEAR - 2, END_YEAR)
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    tidy.to_parquet(RAW_PATH)
    print(f"      cached raw tidy data -> {RAW_PATH} ({len(tidy)} rows)")

    print("[2/4] Cleaning (gap interpolation, coverage filter, winsorizing) ...")
    df_wide = wide(tidy)
    esg_cols = [
        c for c in df_wide.columns
        if c in INDICATORS and INDICATORS[c]["direction"] != 0
    ]
    df_clean = interpolate_short_gaps(df_wide, esg_cols + ["NY.GDP.MKTP.CD"])
    df_clean = drop_low_coverage(df_clean, esg_cols)
    # Winsorize only scored indicators (macro controls keep raw distributions)
    df_clean = winsorize_cross_section(df_clean, esg_cols)
    df_clean = df_clean[
        (df_clean["year"] >= PANEL_START_YEAR) & (df_clean["year"] <= END_YEAR)
    ]

    print("[3/4] Scoring (pillars, equal-weight composite, PCA composite) ...")
    scored = build_scores(df_clean, INDICATORS)

    print("[4/4] Writing scored panel ...")
    PANEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    scored.to_parquet(PANEL_PATH)
    print(f"      scored panel -> {PANEL_PATH} ({len(scored)} rows)")

    n_scored = scored["score_equal"].notna().sum()
    print(f"\nDone. {n_scored} country-years have equal-weight composite scores.")
    latest = scored[scored["year"] == END_YEAR]["score_equal"].dropna()
    if len(latest):
        print(f"Latest-year composite coverage: {len(latest)}/{len(iso3s)} countries")
        print(latest.sort_values(ascending=False).head(5).to_string())


if __name__ == "__main__":
    main()
