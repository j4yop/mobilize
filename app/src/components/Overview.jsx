import { useDashboardData } from '../hooks.js'

const ENGINES = [
  {
    eyebrow: 'Engine 01 — Risk',
    title: 'Sovereign ESG Risk Engine',
    text: '35 sovereigns scored on a 16-indicator World Bank framework. Three portfolios — benchmark, screened, tilted — backtested across 143 months with significance tests and Fama–MacBeth pricing.',
    tab: 'risk',
    cta: 'Open the Risk Lab',
  },
  {
    eyebrow: 'Engine 02 — Pricing',
    title: 'Outcome Bond Pricing Lab',
    text: 'The $150M Wildlife Conservation ("Rhino") Bond, repriced by Monte Carlo: 100k stochastic rhino-population paths through the real deal terms, plus a novel governance sensitivity on the success premium.',
    tab: 'outcome',
    cta: 'Open the Outcome Bond Lab',
  },
]

const EVIDENCE = [
  {
    tab: 'risk',
    eyebrow: 'Backtests',
    title: 'Portfolio risk',
    text: 'Growth, drawdowns, and significance tables for all three strategies, monthly and annual.',
  },
  {
    tab: 'map',
    eyebrow: 'The panel',
    title: 'ESG Map',
    text: '455 country-years of scores. Click any sovereign for its pillars and all 16 indicators.',
  },
  {
    tab: 'pricing',
    eyebrow: 'The null result',
    title: 'Pricing Test',
    text: 'Fama–MacBeth cross-sections: is ESG priced into sovereign returns? (Spoiler: no.)',
  },
  {
    tab: 'method',
    eyebrow: 'The fine print',
    title: 'Methodology',
    text: 'Every proxy, assumption, and limitation disclosed — the part most dashboards hide.',
  },
]

export default function Overview({ onNavigate }) {
  const { data } = useDashboardData()

  const findings = data?.findings
  const bond = data?.outcomeBond

  const headline = [
    {
      eyebrow: 'Volatility',
      value: '−0.7pp',
      note: findings ? `p ${findings.volReduction.p_value}` : 'p <0.001',
      text: 'The ESG tilt is a significant volatility reducer.',
      positive: true,
    },
    {
      eyebrow: 'Return cost',
      value: '≈ −0.1pp',
      note: findings ? `p ${findings.returnCost.p_value}` : 'p 0.25–0.35',
      text: 'Not statistically distinguishable from zero.',
    },
    {
      eyebrow: 'Drawdowns',
      value: '≈ −21%',
      note: 'similar across portfolios',
      text: 'No drawdown protection from the tilt.',
    },
    {
      eyebrow: 'Rhino Bond premium',
      value: bond ? `+${Math.abs(bond.baseline.concessionPp).toFixed(2)}pp` : '+0.88pp',
      note: bond ? `vs vanilla IBRD (${(bond.baseline.vanillaYield * 100).toFixed(2)}%)` : 'vs vanilla IBRD (1.75%)',
      text: 'Outcome risk pays — but is hyper-sensitive to drift.',
      positive: true,
    },
  ]

  return (
    <div className="space-y-10">
      {/* Hero */}
      <section aria-label="About this project">
        <p className="eyebrow mb-3">Quant research · World Bank open data · 2012–2024</p>
        <h2
          className="max-w-3xl text-[1.75rem] md:text-[2.1rem] font-bold leading-[1.15]"
          style={{ letterSpacing: '-0.02em' }}
        >
          Does ESG integration limit downside risk in sovereign fixed-income —{' '}
          <span style={{ color: 'var(--accent)' }}>and what is a development outcome worth?</span>
        </h2>
        <p className="max-w-2xl text-[15px] leading-relaxed mt-4" style={{ color: 'var(--muted)' }}>
          Mobilize is a two-engine answer to that question. It measures the risk on the asset side
          — scoring, tilting, and backtesting sovereign bond portfolios — and prices the risk
          transfer on the capital-markets side, valuing the World Bank's outcome bonds as the
          securities they are. Every number is public data; every assumption is disclosed.
        </p>
      </section>

      {/* Headline findings */}
      <section aria-label="Headline findings">
        <div className="rule-label mb-3">The short answers</div>
        <div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-px rounded-sm overflow-hidden"
          style={{ background: 'var(--line-strong)', boxShadow: 'var(--shadow)' }}
        >
          {headline.map((h) => (
            <div key={h.eyebrow} className="finding-card p-5" style={{ background: 'var(--paper)' }}>
              <div className="eyebrow">{h.eyebrow}</div>
              <div
                className="text-[1.9rem] font-bold leading-none num mt-1.5"
                style={{ letterSpacing: '-0.02em', color: h.positive ? 'var(--teal)' : 'var(--ink)' }}
              >
                {h.value}
              </div>
              <div className="text-[11px] num mt-1" style={{ color: 'var(--faint)' }}>{h.note}</div>
              <div className="text-[13px] mt-2 leading-snug" style={{ color: 'var(--muted)' }}>{h.text}</div>
            </div>
          ))}
        </div>
        <p className="text-[12px] mt-3" style={{ color: 'var(--faint)' }}>
          The defensible version: ESG here is a risk-profile shift, not an alpha source — a
          volatility reducer at no significant return cost, with no drawdown protection and no
          evidence of pricing.
        </p>
      </section>

      {/* The two engines */}
      <section aria-label="The two engines">
        <div className="rule-label mb-3">How the question is answered</div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {ENGINES.map((e) => (
            <div key={e.title} className="card flex flex-col">
              <div className="eyebrow">{e.eyebrow}</div>
              <h3 className="text-lg font-bold mt-1.5" style={{ letterSpacing: '-0.01em' }}>{e.title}</h3>
              <p className="text-[13.5px] leading-relaxed mt-2 flex-1" style={{ color: 'var(--muted)' }}>
                {e.text}
              </p>
              <button
                className="btn mt-4 self-start"
                onClick={() => onNavigate(e.tab)}
                aria-label={`${e.cta} — ${e.title}`}
              >
                {e.cta} →
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Explore the evidence */}
      <section aria-label="Explore the evidence">
        <div className="rule-label mb-3">Explore the evidence</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {EVIDENCE.map((v) => (
            <button
              key={v.tab}
              className="card text-left cursor-pointer transition-transform hover:-translate-y-0.5"
              style={{ padding: '1.25rem' }}
              onClick={() => onNavigate(v.tab)}
              aria-label={`Open ${v.title} tab`}
            >
              <div className="eyebrow">{v.eyebrow}</div>
              <div className="text-[15px] font-bold mt-1.5">{v.title}</div>
              <p className="text-[12.5px] leading-snug mt-1.5" style={{ color: 'var(--muted)' }}>{v.text}</p>
              <span className="link text-[12px] num mt-2 inline-block">view →</span>
            </button>
          ))}
        </div>
      </section>

      {/* Provenance strip */}
      <section aria-label="Data provenance" className="card" style={{ padding: '1.25rem 1.5rem' }}>
        <div className="flex flex-wrap gap-x-10 gap-y-3 justify-between items-center">
          <div className="text-[12.5px]" style={{ color: 'var(--muted)' }}>
            <span className="rule-label block mb-1">Data</span>
            100% free, keyless sources — World Bank API (35 countries × 13 years), FRED (US yield curve)
          </div>
          <div className="text-[12.5px]" style={{ color: 'var(--muted)' }}>
            <span className="rule-label block mb-1">Code</span>
            Python 3.11 · pandas · numpy · scipy — 46 passing tests, fully reproducible
          </div>
          <a
            className="link text-[12.5px] num"
            href="https://github.com/j4yop/mobilize"
            target="_blank"
            rel="noreferrer"
          >
            github.com/j4yop/mobilize →
          </a>
        </div>
      </section>
    </div>
  )
}
