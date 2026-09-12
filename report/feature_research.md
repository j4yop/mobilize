# Mobilize — Feature Research & Accessibility Audit

**Date:** 2026-09-12 · **Scope:** `app/` (React 18-class stack on React 19 + Vite 8 + Tailwind 4 + Recharts 3.10) and `src/mobilize/` (pandas/numpy/scipy pipeline), audited against primary sources (W3C, World Bank, Recharts, MDN, Notre Dame, WRI, FRED).

Current-state claims below are grounded in the actual repo files (`App.jsx`, `hooks.js`, all five components, `indicators.py`, `dashboard.json`, `index.css`, `vercel.json`). External claims carry a cited primary-source URL. Contrast ratios were computed from the WCAG relative-luminance formula against the exact colors used in the code.

---

## Executive summary

### Top 5 recommended next features

| # | Feature | Effort | Value | One-line case |
|---|---|---|---|---|
| 1 | **Extend data window to 2024** (panel, backtest, bundle) | M | High | World Bank API already serves 2024 values for most scored indicators (verified: life expectancy, WGI, CO₂ AR5); FRED is live through Sep 2026 — the app currently freezes at 2023 with 2024 public. |
| 2 | **Outcome Bond Lab: add the other 6 IBRD outcome bonds** (Clean Cooking $200M, Amazon $225M, Spekboom $120M, Plastic $100M, Emissions $50M, UNICEF $100M) | M | High | All six have official public case studies on the World Bank Treasury outcome-bonds page; the Monte Carlo engine is already bond-agnostic in structure. |
| 3 | **Indicator-level score drilldown** (show the 16 underlying indicators behind each country's score, not just E/S/G pillars) | M | High | The panel pipeline already fetches all 16 indicators; only pillars are exported to `dashboard.json`. Directly mirrors the WB Sovereign ESG framework's transparency emphasis (Gratcheva/Emery/Wang, "Demystifying Sovereign ESG"). |
| 4 | **Pillar-level Fama–MacBeth** (run the pricing test separately on E, S, G pillar scores) | S | Medium-High | `scorePca` and `pillarE/S/G` already ship in every panel row of the bundle; a Python re-run + a small UI toggle answers "is any single pillar priced?" — a natural next question after the null composite result. |
| 5 | **CSV export of the panel + URL deep-linking** (share a tab/year/country state) | S | Medium-High | Zero new data needed; static Vercel hosting supports hash-based state with no server; enables citability of the 420-country-year panel. |

### Top 5 accessibility fixes

| # | Fix | WCAG | Effort | Current failure (computed/measured) |
|---|---|---|---|---|
| 1 | Keyboard access to country selection (map circles + ranking rows are `onClick`-only) | 2.1.1 (A) | S-M | `EsgMap.jsx:147` and `EsgMap.jsx:197` attach selection only to `onClick`; no `tabIndex`, no `onKeyDown` — a keyboard user cannot select any country anywhere. |
| 2 | ARIA tabs pattern on the main nav | 4.1.2 (A), APG tabs | S | `App.jsx:44-53` renders plain buttons with no `role="tab"`, no `aria-selected`, no `aria-controls`, no arrow-key support; screen readers hear 5 unnamed toggle buttons. |
| 3 | Fix small-text contrast: `text-gray-400` and `text-emerald-600` at small sizes | 1.4.3 (AA) | S | Computed: `gray-400 #9ca3af` = **2.54:1** on white (FindingCard notes, Box notes, "no change" deltas — fail); `emerald-600 #059669` = **3.77:1** on white used at `text-xs` for positive deltas and significant p-values (fail); `red-600` = 4.83:1 (pass) — positive deltas fail while negative ones pass. |
| 4 | Text alternatives for every chart (Recharts `title`/`desc` + data tables or visually-hidden tables for the 5 chart groups that lack them) | 1.1.1 (A), 1.3.1 (A) | M | No Recharts chart passes `title`/`desc`; growth-of-$1, drawdown, Fama–MacBeth histogram/cumulative/monthly strips, and tier-probability charts have no tabular alternative (only the drift chart ships a table). Recharts 3.10 exposes `title`, `desc`, `role`, `tabIndex` props for exactly this. |
| 5 | Darken the `scoreColor` scale for light mode (and fix hardcoded SVG colors for dark mode) | 1.4.11 (AA) | S | Computed ratios vs white card: score≈25 → **2.35:1**, 50 → **1.50:1**, 75 → **1.79:1**, 100 → **2.03:1** — all below the 3:1 required for meaningful graphics (score bars at `EsgMap.jsx:208`, pillar bars, map circles). On dark cards the same scale passes (5.5–11.8:1). Also `EsgMap.jsx` hardcodes `#6b7280` ISO labels (3.67:1 on dark card) and `#e5e7eb` graticule regardless of theme. |

(Honorable mention, near-free win: add `html { scroll-padding-top: 90px }` so keyboard focus is never fully hidden behind the sticky header — WCAG 2.2 SC 2.4.11, W3C technique C43.)

---

## Section A — Feature opportunities

Effort: **S** ≤ half day · **M** 1–3 days · **L** ≥ a week (across Python pipeline + bundle + UI).

| Feature | Description | Primary source | Effort | Value |
|---|---|---|---|---|
| **A1. Extend panel & backtest to 2024** | `END_YEAR` is 2023 (`indicators.py:159`); bundle `meta.window` says 2013–2023. WB API now serves 2024 for most scored indicators (verified 2026-09-12: `SP.DYN.LE00.IN` USA 2024=78.89, `GOV_WGI_GE_EST` ZAF 2024=−0.226, `EN.GHG.CO2.PC.CE.AR5` USA 2024=13.62; PM2.5 and freshwater 2024 still null — existing ≤2-year interpolation rules already cover this). FRED DGS10 verified live through 2026-09-10; OECD monthly LT yields through Jun 2026. | api.worldbank.org (direct query, `lastupdated 2026-07-13`); fredgraph.csv (direct query) | M | High |
| **A2. More outcome bonds** | The Treasury page lists **six further outcome bonds with full public terms/case studies**: Clean Cooking ($200M, Ghana, Dec 2025), Amazon Reforestation ($225M, Aug 2024), Spekboom Restoration ($120M, 14y, Apr 2026), Plastic Waste Reduction ($100M, Jan 2024), Emissions Reduction Vietnam ($50M, Feb 2023), UNICEF ($100M, Mar 2021 — note: it is a COVID-resilience/vaccine-delivery bond, *not* an "education bond 2025" as sometimes described). Each has a PDF case study + Q&A on thedocs.worldbank.org. The `outcome/terms.py` design (deal terms + tiers) generalizes directly. | treasury.worldbank.org/en/about/unit/treasury/ibrd/outcome-bonds | M (S per additional bond after the first) | High |
| **A3. Indicator-level score drilldown** | Country detail currently shows 3 pillar scores only (`EsgMap.jsx:253-257`). Export the 16 indicator values + normalized z-scores from the scoring pipeline so users can see *which* indicators drive a score — the exact transparency the WB framework is built around. | WB Sovereign ESG framework: Gratcheva, Emery & Wang, "Demystifying Sovereign ESG" (OKR handle 10986/35586, verified via OKR API); WDI ESG source (`source=75`, 80 indicators, verified via API) | M | High |
| **A4. Pillar-level Fama–MacBeth** | Re-run FM with E, S, and G pillar scores as separate regressors (bundle already carries `pillarE/S/G` per country-year). Answers whether the composite's null pricing result hides offsetting pillar effects — a genuinely publishable extension. | Fama–MacBeth (1976) as already implemented in `backtest/fama_macbeth.py`; no new data source needed | S-M | Med-High |
| **A5. CSV export + chart image download** | Download the 420-row panel, weights, and metrics as CSV; serialize Recharts SVGs to PNG via `canvas`. Pure client-side Blob work. | No external source needed (data already in bundle) | S | Med-High |
| **A6. URL state / deep-linking** | `?tab=map&year=2021&country=ZAF` (or hash — safer with Vercel `cleanUrls: true`, no rewrite needed for `#` state). Currently all view state resets on reload. | MDN URL & History API docs | S | Medium |
| **A7. ESG score methodology toggle (equal vs PCA)** | `scorePca` is computed and shipped in every panel row but never rendered; Methodology discloses rank-corr 0.94. A toggle on the map/rankings proves robustness visually. | Already in bundle (`panel[].scorePca`); disclosed in `Methodology.jsx` | S | Medium |
| **A8. Country yield time-series drilldown** | Per-country observed (DM) / synthetic (EM) 10Y yield history in the country detail card. Requires exporting yields from `backtest/yields.py` into the bundle. Must be labeled "synthetic for EM" per the repo's own disclosure discipline. | FRED DGS10 + OECD LT yields (both verified live); repo's own disclosed EM spread model | M | Medium-High |
| **A9. ND-GAIN climate vulnerability overlay** | Free, open country-level climate index (185 countries, 45 indicators, vulnerability + readiness, annual). Merge by ISO3, render as a second map layer or a scatter (ESG score vs climate readiness). | gain.nd.edu (verified: "Free and open source… 45 indicators… 185 countries annually") | M | Med-High |
| **A10. WRI Aqueduct water-stress overlay** | Aqueduct Country Rankings are open data under CC BY 4.0 (verified license statement on the Aqueduct page) — a physical-risk pillar the WB framework flags as a data gap. | wri.org/aqueduct (license: CC BY 4.0, verified) | M | Medium |
| **A11. Rhino Bond outcome-vs-model validation** | The bond has now passed its outcome window; the Treasury page links official Implementation Status & Results Reports for the WCB. Compare actual rhino-growth KPI against the 4%-drift GBM assumption and the tier that actually paid. Highest-credibility possible update to M4. | treasury.worldbank.org outcome-bonds "Reporting & Disclosures" → documents.worldbank.org ISR reports | M | High |
| **A12. Portfolio optimization (ESG-constrained mean-variance, Black–Litterman)** | Replace/augment heuristic tilts (score²) with a frontier: min-var subject to weighted ESG ≥ threshold; BL with the GDP-benchmark as equilibrium. scipy already in the stack. Show turnover vs the current tilted portfolio. | scipy.optimize (repo dependency); Black–Litterman & Markowitz are standard published methods — no new external data | L | Medium |
| **A13. External benchmark comparison — EMBI/GBI reality check** | J.P. Morgan EMBI/GBI index values are **licensed commercial data** — not redistributable in a public static bundle (the public JPM "insights" page I attempted returned 404 and no official free-data page exists). Practical alternatives: (a) link out to provider pages for context, (b) construct a free internal comparison (e.g., GDP-weighted EM-only vs DM-only sub-portfolios from existing data), (c) note OECD/ETF proxies. Recommend (b). | J.P. Morgan index products (commercial; no free redistribution — no public terms page could be fetched; FRED ToS §III likewise forbids redistributing third-party proprietary series) | M (internal proxy) / not feasible (licensed indices) | Medium |
| **A14. Data-freshness footer** | `meta.generated` (2026-09-12T19:29) exists in the bundle but is never shown; WB API reports `lastupdated: 2026-07-13`. Render a "Data through 2023 · WB release 2026-07 · FRED through Sep 2026" line in the footer. | Bundle `meta`; WB API `lastupdated` field (verified) | S | Low-Med |
| **A15. Educational glossary + accessible tooltips** | Financial terms (Sharpe, VaR, Fama–MacBeth, drawdown, GBM, antithetic) used without definition; current "tooltips" are inaccessible `title` attributes (see B9). A glossary section + `<abbr>`-style definitions raises comprehension for the non-quant audience and fixes an a11y issue simultaneously. | W3C ARIA tooltip pattern; WCAG 1.1.1/1.4.13 (see Section B) | S | Medium |
| **A16. Yield-curve tenor suite** | `FRED_CURVE_SERIES` already defines DGS1/2/3/5/7/10/20 (`indicators.py:144-152`) but only DGS10 feeds returns. Build per-country synthetic curves (spread-mapped across tenors) and duration-matched multi-tenor portfolios. | FRED (series IDs verified in repo; data live) | L | Medium |

**Sourcing notes (verified vs not):**
- **Verified directly:** WB API 2024 data + `lastupdated` metadata; FRED daily/monthly liveness; all seven outcome bonds' sizes, dates, and public case-study links on the Treasury page; ND-GAIN scope/license; Aqueduct CC BY 4.0; Recharts 3.10 props for a11y; the WB Treasury Sustainable Fixed-Income Strategy page (now $3bn AUM, 2024 impact report — useful context citation for the README's motivating link, which is now a redirect-safe URL).
- **Could not verify/failed:** a public JPMorgan index licensing page (404 on jpmorgan.com/insights path; no free EMBI data page reachable) — treat EMBI/GBI as license-only; a reachable WB "Sovereign ESG Data Framework" landing page (multiple worldbank.org URLs 404/403 — the framework's canonical artifacts are the OKR publication "Demystifying Sovereign ESG" and WDI ESG source 75, both verified).

---

## Section B — Accessibility findings (WCAG 2.2)

Measured against the actual component code and computed contrast ratios (WCAG relative-luminance formula; white card `#ffffff`, dark card `#111827`, dark body `#0b0f19` from `index.css`).

| # | Criterion (level) | Current state in this app | Fix | Effort |
|---|---|---|---|---|
| **B1** | **2.1.1 Keyboard (A)** — w3.org/WAI/WCAG22/Understanding/keyboard | Map country selection is `onClick` on `<g>` (`EsgMap.jsx:147`) and ranking rows are `onClick` on `<tr>` (`EsgMap.jsx:197`). No `tabIndex`, no key handlers anywhere (repo-wide grep for `onKeyDown`/`tabIndex` = 0 hits). Keyboard users cannot select a country at all. | Make ranking rows focusable (`tabIndex={0}`, `role="button"`, `aria-label={country + score}`, Enter/Space → select; `onKeyDown`); give map circles a redundant `role="button"` + key handler or accept rows as the sole path (Equivalent). | S-M |
| **B2** | **4.1.2 Name, Role, Value (A)** + APG Tabs pattern — w3.org/WAI/ARIA/apg/patterns/tabs/ | Header nav (`App.jsx:43-57`): five native buttons, no `role="tablist"/"tab"`, no `aria-selected`, no `aria-controls`, no arrow-key support; the panel swap is DOM-conditional so `tabpanel` semantics are absent. Tabs are announced as plain buttons with no selected state. | Wrap nav in `role="tablist"`; per tab: `role="tab"`, `aria-selected`, `aria-controls={panelId}`, `id`; tab stop management (`tabIndex −1` on inactive); panels get `role="tabpanel"` + `aria-labelledby`; Left/Right/Home/End per APG. Content is preloaded → automatic activation on arrow-focus is APG-recommended here. | S |
| **B3** | **1.4.3 Contrast Minimum (AA)** — Understanding/contrast-minimum | Computed failures on white cards: `gray-400 #9ca3af` **2.54:1** at `text-xs`/`text-sm` (FindingCard note `App.jsx:122`, OutcomeLab `Box` note, "—" deltas `EsgMap.jsx:35`, `Pillar` label row); `emerald-600 #059669` **3.77:1** at small sizes (positive deltas `EsgMap.jsx:36`, significant p-values `RiskLab.jsx:195,201`, FM verdict accents). On dark card: `red-600` **3.67:1** and `gray-500` **3.67:1** fail small text. (Large `text-3xl` emerald at 30px passes at 3:1.) | Swap small-size grays to `gray-600` (7.56:1) / `dark:gray-300`; deltas to `emerald-700`/`red-700` in dark mode; p-value accents to `font-semibold` + darker tone or a non-color glyph (✓). | S |
| **B4** | **1.4.11 Non-text Contrast (AA)** — Understanding/non-text-contrast | `scoreColor` (`EsgMap.jsx:26-32`) on white cards: score 25→**2.35:1**, 50→**1.50:1**, 75→**1.79:1**, 100→**2.03:1** — below 3:1 for the score bars (`EsgMap.jsx:208`), pillar bars (`EsgMap.jsx:296`), map circle fills, and legend gradient. (All pass ≥3:1 on dark cards — the scale is dark-mode-tuned.) Map selection stroke `#111827` on dark cards ≈1:1 (selection boundary hard to see). | Re-map lightness for light mode, e.g. `hsl(h, 65%, ${52 − t*22}%)` → endpoints ≈4.5:1 and ≈3.9:1 on white while keeping dark-mode branch; or add a 1.5px `stroke` at 3:1; selected-circle stroke → `#e5e7eb` in dark. | S |
| **B5** | **1.1.1 Non-text Content (A)** / **1.3.1 Info & Relationships (A)** | Eight Recharts charts across RiskLab/PricingTest/OutcomeLab: none pass `title`/`desc` (grep: zero usages); Recharts 3.10 supports `accessibilityLayer` (default `true`), `role`, `title`, `desc`, `tabIndex` on charts (verified in official API docs). Growth, drawdown, FM histogram, cumulative γ, monthly γ, and tier-probability charts have **no** tabular alternative (only the drift chart has a table). The custom ESG map SVG (`EsgMap.jsx:129`) has no `role`, `<title>`, or `<desc>` and is effectively invisible-by-uninformative to AT. | Pass `title` (chart purpose) + `desc` (summary sentence with headline numbers) on every chart; add visually-hidden HTML tables or a "View data" toggle for chart-only groups; `<svg role="img"><title>ESG map, {year}</title>` on the custom map. | M |
| **B6** | **2.4.11 Focus Not Obscured (Minimum) (AA, WCAG 2.2 new)** — Understanding/focus-not-obscured-minimum | Sticky header `sticky top-0 z-20` (`App.jsx:35`, ≈76px tall). Focused elements scroll to viewport top and can be fully covered by the header (classic F110-adjacent failure mode; W3C technique C43 = `scroll-padding`). | `html { scroll-padding-top: 96px; }` (or `scroll-margin-top` on cards). | S |
| **B7** | **2.5.8 Target Size (Minimum) (AA, WCAG 2.2 new)** — Understanding/target-size-minimum | Map circles: r=8 in a 720-unit viewBox → diameter = `W × 16/720` CSS px: 25.6px at 1152px container (pass), **17px at 768px**, 8.9px at 400px (fail). Worse, adjacent circles are closer than 24px at any realistic width (e.g., KOR/JPN centers 10 units apart → 16px at 1152px), so the spacing exception fails too. The rankings table (~28px-tall full-width rows) provides an *Equivalent* control, which technically rescues conformance — but touch users on the map still suffer. | Keep rows as the conforming equivalent; additionally bump mobile hit-areas: add a transparent `<circle r={14}>` hit target per country, or scale `r` with a media/container query. | S |
| **B8** | **1.3.1 (A)** — tables & forms | (a) Rankings table (`EsgMap.jsx:181-214`) has **no header row** — `<table><tbody>` with rank/country/score/delta columns undocumented. (b) Year `<select>` (`EsgMap.jsx:104-113`) has a visible "Year" label in a separate flex div — no `htmlFor`/`id` association, so the control is unnamed ("select, group"?). (c) RiskLab/sig/drift tables do have proper `<thead>`/`<th>` (pass). | (a) Add a `<thead>` with `<th scope="col">` (Rank, Country, Score, Δ vs prior year); (b) `htmlFor`/`id` pair (or `aria-label="Score year"`); consider `<caption class="sr-only">`. | S |
| **B9** | **1.4.13 Content on Hover or Focus (AA)** | Rank arrows (`EsgMap.jsx:47-48`) and score-history bars (`EsgMap.jsx:278`) expose values **only** via `title` tooltips — hover-triggered, not dismissible, not hoverable, invisible to keyboard/touch. | Render the value inline (e.g., tiny delta text already exists for scores; add year+score under each history bar for the selected country, or an accessible details row). | S |
| **B10** | **2.3.3 Animation from Interactions (AAA)** + MDN prefers-reduced-motion | Map circles have `transition: fill 300ms` (`EsgMap.jsx:156`); Recharts default entrance animations are active (no `isAnimationActive={false}` anywhere). `prefers-reduced-motion` is not referenced in `index.css` or any component (grep: 0 hits). | `@media (prefers-reduced-motion: reduce) { circle { transition: none } }`; gate Recharts animation via a `matchMedia` hook or `isAnimationActive`. 2.3.3 is AAA so this is best practice, but trivially cheap. | S |
| **B11** | **1.4.4 Resize / 1.4.10 Reflow (AA)** (spot check) | Responsive: charts use `ResponsiveContainer`; `XAxis interval={xTick*2-1}` thins ticks at all widths; rankings table sits in `overflow-y-auto`. At 320px the map circles shrink below target size (B7) and the metrics table scrolls horizontally (`overflow-x-auto` present, pass). Minor: `interval` is static, so mobile ticks can look sparse but never overlap. | No conformance blocker found; optional tick-count media handling. | — |
| **B12** | **3.3.7 Redundant Entry / 2.5.7 Dragging (AA, WCAG 2.2 new)** | Not applicable — the dashboard has no forms with re-entry (single `select`), no drag interactions. | None. | — |
| **B13** | **2.4.7 Focus Visible (AA)** (positive finding) | No focus utilities are stripped: `index.css` contains no `:focus { outline: none }` and no component disables outlines — UA default focus rings render on tabs/select/buttons. Native `<select>`, native `<button>`s. | Passes by default. Optional: a visible 2px focus ring (`focus-visible:ring-2`) to also satisfy AAA 2.4.13 Focus Appearance. | S (optional) |

**Passes already in place** (worth keeping): `<html lang="en">` (3.1.1), meaningful `<title>` + meta description (2.4.2), single `h1` + `h2/h3` per section (1.3.1/2.4.10), color-coded charts carry text legends (Recharts `Legend`), dark-mode support via `prefers-color-scheme` (partially — see B4 hardcoded SVG colors), F-keyboard-operable native controls for tabs/frequency toggle.

---

## Audit method

- **Files read in full:** `README.md`, `app/src/App.jsx`, `hooks.js`, all 5 components in `app/src/components/`, `index.css`, `index.html`, `package.json`, `vercel.json`, `src/mobilize/data/indicators.py`, `scripts/` listing; `app/public/data/dashboard.json` inspected programmatically (keys, meta, panel schema, years).
- **Contrast math:** WCAG 2.x relative-luminance/contrast-ratio computed in Python from the exact `hsl()` values emitted by `scoreColor` and Tailwind palette hexes against `#ffffff` (`.card` light), `#111827` (`.card` dark), `#0b0f19` (body dark).
- **Target-size math:** circle diameter = `2r × (rendered width / viewBox 720)`; adjacency from the `POSITIONS` table (e.g., KOR 128,36 vs JPN 138,36 → 10-unit centers).
- **Live-data checks (2026-09-12):** WB API queries for 3 scored indicators × 2 countries (2024 availability); FRED `fredgraph.csv` for DGS10 (daily, through 2026-09-10) and OECD LT monthly (through 2026-06).

## Sources

**W3C / accessibility**
- WCAG 2.2 Quick Reference — https://www.w3.org/WAI/WCAG22/quickref/
- SC 2.5.8 Target Size (Minimum) — https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
- SC 2.4.11 Focus Not Obscured (Minimum) — https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html
- ARIA APG Tabs Pattern — https://www.w3.org/WAI/ARIA/apg/patterns/tabs/
- MDN `prefers-reduced-motion` — https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion

**Recharts**
- Recharts API (AreaChart props: `accessibilityLayer` default `true`, `role`, `title`, `desc`, `tabIndex`) — https://recharts.github.io/en-US/api/AreaChart/ (docs site moved from recharts.org to recharts.github.io; verified 2026-09-12)

**World Bank / outcome bonds**
- IBRD Outcome Bonds (all bond sizes, dates, case-study/Q&A links incl. Clean Cooking, Amazon, Spekboom, Plastic, Emissions, UNICEF, WCB ISR reports) — https://treasury.worldbank.org/en/about/unit/treasury/ibrd/outcome-bonds
- Sustainable Fixed-Income Strategy (2024 impact report, $3bn AUM) — https://treasury.worldbank.org/en/about/unit/treasury/impact/sustainable-fixed-income-strategy
- WB Open Knowledge Repository, "Demystifying Sovereign ESG" (Gratcheva, Emery, Wang; handle 10986/35586) — https://openknowledge.worldbank.org/ (retrieved via OKR search API)
- WB API live queries — https://api.worldbank.org/v2/country/{USA,ZAF}/indicator/{SP.DYN.LE00.IN,GOV_WGI_GE_EST,EN.GHG.CO2.PC.CE.AR5} (2024 values present; source `lastupdated 2026-07-13`)
- WDI ESG data source (id 75, 80 indicators) — https://api.worldbank.org/v2/indicator?source=75

**Climate / environmental risk**
- ND-GAIN Country Index (185 countries, 45 indicators, free/open) — https://gain.nd.edu/ and https://gain.nd.edu/our-work/country-index/
- WRI Aqueduct (CC BY 4.0 license statement) — https://www.wri.org/aqueduct

**FRED / market data**
- FRED fredgraph.csv (DGS10 daily through 2026-09-10; OECD LT monthly through 2026-06) — https://fred.stlouisfed.org/graph/fredgraph.csv
- FRED Terms of Use (no redistribution of third-party proprietary series; copyright notes per series) — https://fred.stlouisfed.org/legal/terms-of-use
- J.P. Morgan EMBI/GBI: no free/public data page could be fetched (jpmorgan.com/insights path 404; MSCI index-resources page behind bot challenge) — treated as licensed-only based on what is and is not publicly offered.

**Unreachable / could not verify (stated rather than guessed):** a canonical WB "Sovereign ESG Data Framework" landing page (worldbank.org URLs 404/403); any official JPM index-licensing terms page; the Recharts legacy wiki accessibility issue tracker was not needed since the current official API documents the a11y props.
