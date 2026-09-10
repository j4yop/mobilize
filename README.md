# Mobilize

**Does ESG integration limit downside risk in sovereign fixed-income portfolios? And what is a development outcome worth?**

Mobilize is a two-part quantitative research project inspired by the World Bank Group Treasury's own mandates — its [Sustainable Fixed-Income Strategy](https://treasury.worldbank.org/en/about/unit/treasury/impact/sustainable-fixed-income-strategy) and its [outcome bonds](https://treasury.worldbank.org/en/about/unit/treasury/ibrd/outcome-bonds) (UNICEF, Rhino, Amazon, Clean Cooking, Spekboom):

1. **ESG Risk Engine (core)** — Scores ~35 sovereigns on a World Bank Sovereign-ESG-style indicator framework (World Bank open data), constructs ESG-tilted vs. benchmark vs. screened fixed-income portfolios, and backtests 2013–2023 to measure the actual question: *does an ESG tilt limit drawdowns, and at what cost in return?*

2. **Outcome Bond Lab (stretch)** — A Monte Carlo pricing engine for the Wildlife Conservation Bond ("Rhino Bond", $150M, 5-year, IBRD 2022): vanilla leg vs. outcome-linked leg, KPI as a stochastic process, success-payment solving, and a novel sensitivity linking the issuer-country's governance score (from this repo's own ESG panel) to the required success premium.

> Thesis: *Mobilizing private capital for development — measuring the risk on the asset side, pricing the risk transfer on the capital-markets side.*

## Status

| Milestone | Scope | Status |
|---|---|---|
| M1 | Data pipeline + sovereign ESG scoring panel | 🚧 In progress |
| M2 | Portfolio construction + 10-year backtest + risk metrics | ⏳ Planned |
| M3 | Streamlit app (3 tabs) + 6–8 page research report + deploy | ⏳ Planned |
| M4 | Rhino Bond Monte Carlo pricing lab | ⏳ Planned |

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
