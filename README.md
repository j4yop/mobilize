# Mobilize

> **Mobilizing private capital for development — measuring the risk on the asset side, pricing the risk transfer on the capital-markets side.**

**Live dashboard:** [mobilize-phi.vercel.app](https://mobilize-phi.vercel.app)

---

## The Problem

Two real frictions exist in development finance today:

1. **Institutional capital wants to go "ESG" into sovereign debt — but nobody agrees what that buys.** Huge pools of capital (pensions, sovereign wealth funds) are being steered toward sovereign fixed-income with ESG overlays. Yet the marketing claims — "ESG reduces risk", "ESG protects downside" — are rarely tested on actual sovereign bond data. Does an ESG tilt genuinely change the risk profile of a sovereign bond portfolio, or is it just a label? And if it does change the risk, what does it cost in return?

2. **Outcome bonds pay for results, but nobody prices the outcome.** The World Bank's IBRD has issued a family of "outcome bonds" (Rhino, Clean Cooking, Amazon Reforestation, Plastic Waste, Vietnam ER, Spekboom, UNICEF CAR-129) where investors take a lower guaranteed floor in exchange for a payment linked to a real-world outcome — like black rhino population growth. These instruments are exciting, but their pricing has mostly been treated as a structuring exercise. If we model the KPI (rhino population) as a stochastic process, what is that outcome actually worth? What premium does an investor require for taking on outcome risk?

Mobilize is a two-part quantitative research project that answers both questions directly.

## The Question

> **Does ESG integration limit downside risk in sovereign fixed-income portfolios — and if so, at what cost in return? And what is a development outcome worth, priced as a security?**

---

## What Mobilize Does

Mobilize attacks the question in two parts:

### Part 1 — Sovereign ESG Risk Engine (the core)

1. **Score** ~35 sovereigns on a World Bank Sovereign-ESG-style indicator framework (16 indicators, built from World Bank open data) — producing a 455 country-year panel (2012–2024).
2. **Construct three portfolios** from the same universe:
   - **Benchmark** — GDP-weighted, no ESG view
   - **ESG-screened** — drop the bottom ESG quintile
   - **ESG-tilted** — weight by GDP × score²
   All rebalanced annually with no look-ahead (year-*t* weights use year-*t−1* information only).
3. **Backtest** all three (monthly, 143 months) and measure the actual question: drawdowns, volatility, returns — with statistical significance tests, not just eyeballing two lines.
4. **Price the ESG factor itself** via a Fama–MacBeth cross-sectional regression (monthly, Newey–West corrected t-stats) — is sovereign ESG actually priced into returns?

### Part 2 — Outcome Bond Pricing Lab (the stretch)

1. **Model the KPI as a stochastic process** — rhino population as geometric Brownian motion, with disclosed judgment calibrations (4%/yr drift baseline, 3% vol).
2. **Monte-Carlo the cash-flows** — 100k antithetic paths through the Rhino Bond's actual deal terms (USD 150M, 5-year, issue at 94.84, no coupon, GEF success-payment tiers of $0/$36.69/$73.38/$91.73 per $1,000).
3. **Solve the pricing** — expected success payment, P(any success), expected investor return, and the implied premium vs. a vanilla IBRD bond.
4. **Governance sensitivity** (novel) — holding investor economics fixed, sweep the issuer-country's governance score (from this repo's own ESG panel) and watch the required success payment change. Weak institutions must be compensated more for the same outcome.

---

## What We Found (Inference)

### Sovereign ESG tilt: real volatility effect, no free lunch, no protection

Backtesting 35 sovereigns over 143 months:

| Portfolio | Ann. Return | Ann. Vol | Sharpe | Max DD |
|---|---|---|---|---|
| Benchmark (GDP-weighted) | 0.99% | 5.03% | -0.17 | -21.3% |
| ESG-screened (drop bottom quintile) | 0.98% | 4.99% | -0.18 | -21.3% |
| ESG-tilted (GDP × score²) | 0.90% | 4.78% | -0.20 | -20.9% |

**The inference, stated honestly:**

- **Volatility**: ESG-tilting significantly reduces portfolio volatility (~0.7–0.8pp annualized, p<0.001) — driven by the tilt's shift toward low-beta developed-market sovereigns.
- **Return cost**: small and not statistically distinguishable from zero (p=0.25–0.35).
- **Drawdowns**: near-identical (~-21%); ESG tilting did **not** limit the worst loss.
- **Pricing**: the ESG factor is **not significantly priced** (Fama–MacBeth gamma = -28bp/month per 100 ESG points, Newey–West t = -0.91, p = 0.36) — and this null holds at pillar level too: none of E (p=0.86), S (p=0.68), or G (p=0.40) is individually priced. The tilt is a **risk-profile shift, not an alpha source**.

> **Headline:** *In this 35-country backtest, ESG integration acted as a significant volatility reducer at no statistically significant return cost, but provided no drawdown protection and no evidence of ESG being priced into sovereign returns.* This nuance — not "ESG wins" or "ESG loses" — is exactly the kind of result the World Bank Treasury's own [Sustainable Fixed-Income Strategy](https://treasury.worldbank.org/en/about/unit/treasury/impact/sustainable-fixed-income-strategy) research engages with.

### Rhino Bond: a positive expected premium, but drift is everything

| Metric | Baseline | With SA governance (38/100) |
|---|---|---|
| E[success payment] | $80.11/$1k ($12.0m) | $73.40/$1k ($11.0m) |
| P(any success) | 99.9% | 99.3% |
| Investor E[return] | 2.63%/yr | 2.51%/yr |
| Premium vs vanilla IBRD (1.75%) | +0.88pp | +0.76pp |
| Donor leverage (conservation $ / expected subsidy $) | 1.4x | — |

**The inference:**

- At the parks' reported growth track (~4%/yr), the tiered success payments imply a **positive investor premium** over the vanilla IBRD yield — the issue discount plus expected success payment outweighs the forgone coupon.
- Pricing is **hyper-sensitive to the drift assumption** (it sits on a tier boundary): at 2%/yr drift the premium nearly vanishes (0.37pp), at 6% it reaches 1.08pp.
- **Governance matters for structuring**: the required donor success payment spans $80–$87 per $1,000 as governance scores range 90→10 — weak institutions must be compensated ~9% more per $1,000.

---

## Workflow

```
World Bank API ─┐
                ├─> data/ (clean + cache, 455 country-years)
FRED (yields) ──┘         │
                          ▼
                    scoring/  (pillar normalization, composite + PCA scores)
                          │
                          ▼
                    portfolio/  (universe, benchmark / tilted / screened, rebalancing)
                          │
                          ▼
                    backtest/  (returns, metrics, significance tests, Fama-MacBeth)
                          │
                          ▼
                    outcome/  (Rhino Bond cash-flows, Monte Carlo, pricing)
                          │
                          ▼
                    build_dashboard_data.py  (export static JSON)
                          │
                          ▼
                    app/  (static React dashboard, deployed to Vercel)
```

### Quant methods used

| Stage | Method |
|---|---|
| Scoring | Indicator normalization (min-max within pillar), equal-weight vs. PCA composite (rank correlation ρ=0.94 between the two) |
| Portfolio construction | GDP-weighted benchmark, quintile screening, score² tilt — annual rebalance, no look-ahead |
| Bond returns | Duration×Δyield proxy (D=8, ~10Y tenor) |
| Yield modeling | DM yields observed (FRED + OECD); EM yields = US 10Y + sign-constrained model-fitted annual spread (calibrated on DM spreads, R² disclosed) |
| Risk metrics | CAGR, annualized vol, Sharpe, max drawdown, downside capture |
| Significance testing | Paired portfolio differences with p-values (monthly + annual), Fama–MacBeth with Newey–West correction |
| Outcome-bond pricing | Monte Carlo (100k antithetic GBM paths), tiered payoff valuation, governance sensitivity sweep |

---

## Tech Stack

**Analysis** — Python 3.11+ · pandas · numpy · scipy · pytest · ruff

**Dashboard** — React 18 · Vite · Tailwind CSS 4 · Recharts (fully static, no server)

**Data** — 100% free, no API keys required:
- **World Bank API** (`api.worldbank.org`) — macro & sovereign-ESG indicators, 35 countries × 15 years
- **FRED** (`fredgraph.csv`, keyless) — US Treasury yield curve for bond-return proxies & pricing

All proxy assumptions (e.g., sovereign bond returns proxied from yield data) are disclosed in the app's Methodology tab.

---

## Usage

```bash
# Analysis
pip install -e ".[dev]"
make data                            # fetch WB indicators -> ESG score panel
python scripts/run_backtest.py      # annual + monthly backtests + Fama-MacBeth
python scripts/build_dashboard_data.py  # export static JSON bundle

# Dashboard (app/)
cd app && npm install
npm run dev      # local dev server
npm run build    # static build -> dist/
vercel           # deploy from repo root (vercel.json config included)
```

## Repository layout

```
src/
  data/       WB + FRED clients, cleaning, caching
  scoring/    pillar normalization, composite + PCA scores
  portfolio/  universe, benchmark/tilted/screened, rebalancing
  backtest/   returns, metrics, significance, yields, monthly, Fama-MacBeth
  outcome/    rhino bond cash-flows, Monte Carlo, pricing
app/          static React dashboard (Vercel-ready)
scripts/      pipeline entry points
tests/        46 passing tests
data/         cached panels (gitignored, reproducible)
```

## License

MIT
