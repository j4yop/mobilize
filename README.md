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
| M2 | Portfolio construction + backtest + risk metrics | ✅ Done — results below |
| M2.5 | Monthly frequency + Fama–MacBeth + calibrated spread model | ✅ Done — results below |
| M3 | Streamlit app (3 tabs) + 6–8 page research report + deploy | ⏳ Planned |
| M4 | Rhino Bond Monte Carlo pricing lab | ⏳ Planned |

## M2 Results (2013–2023, 35 sovereigns, year-end yields, ~10Y duration)

### Annual backtest (11 year-end observations)

| Portfolio | CAGR | Vol | Sharpe | Max DD | Downside Capture |
|---|---|---|---|---|---|
| Benchmark (GDP-weighted) | 0.72% | 7.26% | -0.14 | -18.7% | — |
| ESG-screened (drop bottom quintile) | 0.72% | 7.24% | -0.14 | -18.8% | 99.6% |
| ESG-tilted (GDP × score²) | 0.65% | 7.06% | -0.16 | -18.5% | 97.8% |

### Monthly backtest (131 month-end observations, annualized)

| Portfolio | Ann. Return | Ann. Vol | Sharpe | Max DD |
|---|---|---|---|---|
| Benchmark | 0.99% | 5.03% | -0.17 | -21.3% |
| ESG-screened | 0.98% | 4.99% | -0.18 | -21.3% |
| ESG-tilted | 0.90% | 4.78% | -0.20 | -20.9% |

### Significance tests

| Comparison | Vol diff (ann.) | Vol p-value | Mean ret diff | Ret p-value |
|---|---|---|---|---|
| Tilted vs benchmark (monthly) | -0.7pp | **<0.001** | -0.1pp/yr | 0.35 |
| Tilted vs benchmark (annual) | -2.0pp | 0.02 | -0.9pp/yr | 0.25 |
| Screened vs benchmark (monthly) | -0.1pp | <0.001 | ~0 | 0.73 |

### Fama–MacBeth pricing test (monthly, 131 months, avg 23-country cross-sections)

- ESG factor gamma: **-28bp/month per 100 ESG points, Newey–West t = -0.91, p = 0.36**
- **The sovereign ESG score is not significantly priced** in this universe/window — a null result reported as such.

**Findings (statistically honest):**

- **Volatility**: ESG-tilting significantly reduces portfolio volatility (~0.7pp annualized at monthly frequency, p<0.001) — driven by the tilt's shift toward low-beta DM sovereigns.
- **Return**: the tilt's return cost is small and not statistically distinguishable from zero (p=0.25–0.35) — the earlier "significant cost" finding was an artifact of year-end-only sampling.
- **Drawdowns**: near-identical across portfolios (~-19% annual / ~-21% monthly); ESG tilting did not limit the worst loss.
- **Pricing**: ESG is not a priced factor here — the tilt is a risk-profile shift, not an alpha source.

**Headline (the defensible version):** *In this 35-country backtest, ESG integration acted as a significant volatility reducer (~0.7pp) at no statistically significant return cost, but provided no drawdown protection and no evidence of ESG being priced into sovereign returns.* This nuance — not "ESG wins" or "ESG loses" — is exactly the kind of result the World Bank Treasury's own Sustainable Fixed-Income Strategy research engages with.

*Methodological notes: bond returns proxied via duration×Δyield with full duration against each period's yield move (D=8, ~10Y benchmark tenor). DM yields observed (FRED: US DGS10 + OECD long-term monthly). EM yields = observed US 10Y + sign-constrained model-fitted annual spread (calibrated on DM observed spreads, R² reported; debt/GDP backfilled from nearest available year within country). EM monthly yields inherit observed US curve dynamics; EM-specific monthly variation is macro-only — disclosed. Scores annual, no look-ahead: year-t weights use year-(t-1) information. Fama–MacBeth: monthly cross-sectional regressions with Newey–West corrected t-stats.*

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
