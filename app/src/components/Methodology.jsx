export default function Methodology() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h2 className="text-lg font-bold">Methodology</h2>
        <p className="text-sm text-gray-500">
          Every assumption that could bias these results, disclosed in one place.
        </p>
      </div>

      <Section title="Data">
        <Ul>
          <li>
            <b>Macro & ESG indicators</b>: World Bank Open Data API (keyless), 35 countries,
            annual, 2012–2023. ESG composite follows the World Bank Sovereign ESG framework
            style: 5 environmental, 5 social, 6 governance (WGI) indicators — direction-adjusted,
            min-max normalized per year, equal-weight pillars, composite = mean of pillars.
            A PCA composite is computed alongside (rank correlation ≈ 0.94).
          </li>
          <li>
            <b>Cleaning</b>: gaps ≤ 2 years interpolated; country-indicator series with
            &lt;80% coverage dropped for that indicator; scored indicators winsorized at
            1%/99% per year. Debt/GDP (gappy publication) backfilled from the nearest
            available year within country.
          </li>
          <li>
            <b>2024 extension caveat</b>: for 2024, renewable-energy consumption and
            natural-resource depletion are not yet published by the World Bank (latest
            2021; &gt;2-year gaps cannot be interpolated), so the 2024 Environmental
            pillar rests on the remaining indicators (CO₂, PM2.5 and freshwater carried
            forward per the interpolation rule). This changes the E-pillar's composition
            for 2024 and can shift E-pillar levels vs 2023 — disclosed, not hidden.
          </li>
          <li>
            <b>Yields</b>: DM (12 countries) observed — US 10Y CMT (FRED DGS10, daily) and
            OECD long-term government bond yields (FRED monthly, ~10Y tenor). EM yields
            synthetic — see below.
          </li>
          <li>
            <b>Outcome-bond family</b>: terms for all seven IBRD outcome bonds (Rhino,
            Clean Cooking, Amazon Reforestation, Plastic Waste, Emissions Reduction,
            Spekboom, UNICEF) taken from official World Bank press releases and Treasury
            Q&amp;A documents; minimum/maximum returns are the official disclosed figures,
            not modeled. The Rhino Bond's governance sensitivity remains the only modeled
            pricing lab.
          </li>
        </Ul>
      </Section>

      <Section title="Portfolio construction">
        <Ul>
          <li>
            <b>Benchmark</b>: GDP-weighted (prior-year GDP), full 35-country universe.
          </li>
          <li>
            <b>ESG-tilted</b>: GDP weight × (ESG score/100)².
          </li>
          <li>
            <b>ESG-screened</b>: drops the bottom quintile by score, GDP-weighted remainder.
          </li>
          <li>
            <b>No look-ahead</b>: weights for holding-year t use only information from the
            end of t−1 (scores and GDP). Enforced and unit-tested.
          </li>
          <li>Annual rebalancing; weights held fixed within the year even at monthly frequency.</li>
        </Ul>
      </Section>

      <Section title="Return proxy (the big assumption)">
        <Ul>
          <li>
            Real sovereign bond prices are paywalled; returns are proxied via the standard
            duration approximation: <code>r ≈ y<sub>t−1</sub> − D·(y<sub>t</sub> − y<sub>t−1</sub>)</code>,
            D = 8 (~10Y modified duration), applied to year-end (annual) or month-end (monthly)
            yield levels.
          </li>
          <li>
            <b>EM synthetic yields</b>: US 10Y + fitted spread. Spread model calibrated on
            observed DM spreads (sign-constrained least squares: debt ≥ 0, reserves ≤ 0,
            inflation ≥ 0, governance ≤ 0). The unconstrained DM fit produces wrong-signed
            coefficients — a disclosed weakness of using DM data to price EM credit risk.
            Both fits' R² are reported in the repo.
          </li>
          <li>
            <b>EM monthly variation</b>: EM monthly yields = observed US 10Y monthly path +
            linearly interpolated annual spread. EM-specific monthly dynamics are NOT modeled —
            EM co-moves with the US curve by construction. This inflates EM–US return
            correlations and understates diversification; it is the bundle's largest known bias.
          </li>
          <li>
            Missing debt data (e.g. KEN pre-2015, CHN central government debt) is backfilled
            from the nearest year within ±4 years; countries without any debt observation
            use the calibration medians for the spread model.
          </li>
        </Ul>
      </Section>

      <Section title="Statistics">
        <Ul>
          <li>
            <b>Volatility difference</b>: paired permutation test (within-year swaps), 10,000
            permutations — appropriate for a non-pairwise statistic on a short sample.
          </li>
          <li>
            <b>Mean return difference</b>: H0-recentered block bootstrap (block size 2, 10,000
            resamples) on the paired difference series.
          </li>
          <li>
            <b>Fama–MacBeth</b>: monthly cross-sectional regressions of country returns on
            lagged ESG scores; Newey–West (10% lag truncation) t-statistic on the mean γ.
            Minimum cross-section: 8 countries.
          </li>
          <li>
            Annual-frequency tests run on 11 observations — treat those p-values as weak
            evidence; monthly (131 obs) is the primary frequency for inference.
          </li>
        </Ul>
      </Section>

      <Section title="Known limitations">
        <Ul>
          <li>35-country universe; results need not generalize to broader EM universes.</li>
          <li>2013–2023 window: a falling-then-rising US rate cycle; no GFC-type regime.</li>
          <li>Duration approximation ignores convexity and roll-down; fine for small moves.</li>
          <li>Scores rely on annual macro data — no news/sentiment component.</li>
          <li>
            PCA composite reported but the app displays the equal-weight composite; conclusions
            are robust across both (rank corr ≈ 0.94).
          </li>
        </Ul>
      </Section>

      <Section title="Outcome Bond Lab (Rhino Bond) model">
        <Ul>
          <li>
            <b>Deal terms</b>: all from the official World Bank press release (Mar 23, 2022) —
            USD 150m, 5y, issue 94.84, no coupon, par redemption, GEF success-payment tiers
            ($0/$36.69/$73.38/$91.73 per $1,000 on annualized rhino growth under 0% / 0–2% / 2–4% / over 4%).
          </li>
          <li>
            <b>Population model</b>: geometric Brownian motion, annualized growth KPI over 5
            years, 100k antithetic paths. Baseline drift 4%/yr (parks' reported recent growth),
            vol 3%/yr — calibration is judgment, not fit to private data.
          </li>
          <li>
            <b>Governance link</b>: drift shifts +0.5pp and vol scales −10% per 10 governance
            points above 50. These elasticities are DISCLOSED ASSUMPTIONS — no public dataset
            links country governance to conservation-outcome variance. The schedule is a
            structuring illustration, not an empirical estimate.
          </li>
          <li>
            <b>FX</b>: conservation payments ZAR 152m converted at 15.0 ZAR/USD (March 2022 rate).
          </li>
          <li>
            <b>Vanilla comparison</b>: IBRD 5y USD area ~1.75% (Mar 2022 AAA curve, approximate).
          </li>
          <li>
            Baseline drift sits at the tier-3 boundary (4%), so expected pricing is highly
            drift-sensitive — see the drift table in the lab. The KPI definition (annualized
            compound growth) is our interpretation of the official growth-rate metric.
          </li>
        </Ul>
      </Section>

      <Section title="Reproduce">
        <p className="text-sm text-gray-600 dark:text-gray-300">
          <code>make data</code> → <code>python scripts/run_backtest.py</code> →{' '}
          <code>python scripts/build_dashboard_data.py</code>. All data from free public APIs
          (World Bank, FRED); no API keys required. Tests: <code>pytest</code> (46 passing).
        </p>
      </Section>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div className="card">
      <h3 className="font-semibold mb-2">{title}</h3>
      <div className="space-y-2">{children}</div>
    </div>
  )
}

function Ul({ children }) {
  return (
    <ul className="list-disc pl-5 space-y-1.5 text-sm text-gray-600 dark:text-gray-300">
      {children}
    </ul>
  )
}
