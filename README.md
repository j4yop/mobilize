# Mobilize

**Does ESG integration limit downside risk in sovereign fixed-income portfolios? And what is a development outcome worth?**

Mobilize is a two-part quantitative research project inspired by the World Bank Group Treasury's own mandates — its [Sustainable Fixed-Income Strategy](https://treasury.worldbank.org/en/about/unit/treasury/impact/sustainable-fixed-income-strategy) and its [outcome bonds](https://treasury.worldbank.org/en/about/unit/treasury/ibrd/outcome-bonds) (UNICEF, Rhino, Amazon, Clean Cooking, Spekboom):

1. **ESG Risk Engine (core)** — Scores ~35 sovereigns on a World Bank Sovereign-ESG-style indicator framework (World Bank open data), constructs ESG-tilted vs. benchmark vs. screened fixed-income portfolios, and backtests 2013–2023 to measure the actual question: *does an ESG tilt limit drawdowns, and at what cost in return?*

2. **Outcome Bond Lab (stretch)** — A Monte Carlo pricing engine for the Wildlife Conservation Bond ("Rhino Bond", $150M, 5-year, IBRD 2022): vanilla leg vs. outcome-linked leg, KPI as a stochastic process, success-payment solving, and a novel sensitivity linking the issuer-country's governance score (from this repo's own ESG panel) to the required success premium.

> Thesis: *Mobilizing private capital for development — measuring the risk on the asset side, pricing the risk transfer on the capital-markets side.*

## Status

| Milestone | Scope | Status |
|---|---|---|
| M1 | Data pipeline + sovereign ESG scoring panel | ✅ Done — 420 country-years, 35/35 coverage, equal-vs-PCA rank corr ρ=0.94 |
| M2 | Portfolio construction + 10-year backtest + risk metrics | ✅ Done — results below |
| M3 | Streamlit app (3 tabs) + 6–8 page research report + deploy | ⏳ Planned |
| M4 | Rhino Bond Monte Carlo pricing lab | ⏳ Planned |

## M2 Results (2013–2023, annual rebalancing, 35 sovereigns)

| Portfolio | CAGR | Vol | Sharpe | Max DD | Downside Capture |
|---|---|---|---|---|---|
| Benchmark (GDP-weighted) | 1.66% | 4.38% | -0.06 | -8.7% | — |
| ESG-screened (drop bottom quintile) | 1.44% | 4.33% | -0.11 | -8.8% | 104% |
| ESG-tilted (GDP × score²) | 1.24% | 4.10% | -0.17 | -9.3% | 108% |

**Findings (statistically honest):**

- **Volatility**: ESG portfolios show slightly lower vol (tilted: -0.28pp), but the difference is **not statistically significant** (paired permutation test, p≈0.32).
- **Return**: ESG portfolios **significantly underperform** on average annual return (tilted: -0.44pp/yr, bootstrap p=0.002; screened: -0.23pp/yr, p=0.001). Mechanism: the tilt overweights high-ESG DM sovereigns (Sweden, Switzerland, Netherlands) which carry low yields — the ESG premium is paid as carry.
- **Drawdowns**: Max drawdowns are similar across portfolios (-8.7% to -9.3%); ESG tilting did not limit the worst loss in this window.

**Headline (the defensible version):** *In this 35-country, 10-year, yield-proxy backtest, ESG integration did not meaningfully reduce downside risk but carried a measurable return cost of ~20–45bp per year — a "quality tilt" effect consistent with ESG literature.* This is exactly the kind of nuance the World Bank Treasury's own Sustainable Fixed-Income Strategy research engages with.

*Methodological notes: bond returns proxied via duration×Δyield from observed DM yields (FRED) and fundamentals-based synthetic EM yields (EMBI-calibrated spread model). Annual frequency. No look-ahead: year-t weights use only year-(t-1) scores and GDP. All proxy assumptions disclosed in the report (M3).*

## Data sources (100% free, no API keys required)

- **World Bank API** (`api.worldbank.org`) — macro & sovereign-ESG indicators, 35 countries × 15 years
- **FRED** (`fredgraph.csv`, keyless) — US Treasury yield curve for bond-return proxies & pricing

All proxy assumptions (e.g., sovereign bond returns proxied from yield data) are disclosed in the report's limitations section.

## Stack

Python 3.11+ · pandas · numpy · scipy · statsmodels · scikit-learn (PCA) · Streamlit · Plotly · pytest · ruff

## Usage

```bash
pip install -e ".[dev]"
make data          # build the cached indicator panel + ESG scores
pytest             # run the test suite
```

## Repository layout

```
src/
  data/       WB + FRED clients, cleaning, caching
  scoring/    pillar normalization, composite + PCA scores
  portfolio/  universe, benchmark/tilted/screened, rebalancing   (M2)
  backtest/   returns engine, drawdown/VaR/CVaR metrics          (M2)
  outcome/    rhino bond cash-flows, Monte Carlo, pricing        (M4)
  viz/        chart builders                                     (M3)
app/          Streamlit app                                      (M3)
report/       research write-up                                  (M3)
tests/
notebooks/    report figures only
```

## License

MIT
