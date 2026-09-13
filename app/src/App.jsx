import { useEffect, useRef, useState } from 'react'
import { useDashboardData } from './hooks.js'
import RiskLab from './components/RiskLab.jsx'
import EsgMap from './components/EsgMap.jsx'
import PricingTest from './components/PricingTest.jsx'
import OutcomeLab from './components/OutcomeLab.jsx'
import Methodology from './components/Methodology.jsx'

const TABS = [
  { id: 'risk', label: 'Risk Lab' },
  { id: 'map', label: 'ESG Map' },
  { id: 'pricing', label: 'Pricing Test' },
  { id: 'outcome', label: 'Outcome Bond Lab' },
  { id: 'method', label: 'Methodology' },
]

// ---- URL hash deep-linking: #tab=map&year=2021&country=ZAF ----
function readHash() {
  const raw = new URLSearchParams(window.location.hash.replace(/^#/, ''))
  const out = {}
  for (const k of ['tab', 'year', 'country']) {
    const v = raw.get(k)
    if (v) out[k] = v
  }
  return out
}

function writeHash(state) {
  const params = new URLSearchParams()
  if (state.tab && state.tab !== 'risk') params.set('tab', state.tab)
  if (state.year) params.set('year', String(state.year))
  if (state.country) params.set('country', state.country)
  const hash = params.toString()
  const url = `${window.location.pathname}${window.location.search}${hash ? `#${hash}` : ''}`
  window.history.replaceState(null, '', url)
}

export default function App() {
  const { data, error } = useDashboardData()
  const initial = useRef(readHash())
  const [tab, setTab] = useState(() => {
    const t = initial.current.tab
    return TABS.some((x) => x.id === t) ? t : 'risk'
  })
  const [deepLink, setDeepLink] = useState(() => {
    const s = initial.current
    return { year: s.year ? Number(s.year) : null, country: s.country ?? null }
  })
  const tabsRef = useRef({})

  // Sync tab changes into the URL
  useEffect(() => {
    writeHash({ tab, year: deepLink.year, country: deepLink.country })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab])

  // Respond to browser back/forward on the hash
  useEffect(() => {
    const onHashChange = () => {
      const h = readHash()
      if (h.tab && TABS.some((x) => x.id === h.tab)) setTab(h.tab)
      setDeepLink({ year: h.year ? Number(h.year) : null, country: h.country ?? null })
    }
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  // Clear country/year deep-link state when leaving the map tab
  const onTabChange = (id) => {
    setTab(id)
    if (id !== 'map') setDeepLink({ year: null, country: null })
  }

  const onTabKeyDown = (e, i) => {
    let next = null
    if (e.key === 'ArrowRight') next = (i + 1) % TABS.length
    else if (e.key === 'ArrowLeft') next = (i - 1 + TABS.length) % TABS.length
    else if (e.key === 'Home') next = 0
    else if (e.key === 'End') next = TABS.length - 1
    if (next !== null) {
      e.preventDefault()
      onTabChange(TABS[next].id)
      tabsRef.current[TABS[next].id]?.focus()
    }
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto p-8" style={{ color: 'var(--accent)' }}>
        <h1 className="text-xl font-bold tracking-tight mb-2">Mobilize</h1>
        <p className="text-sm">
          Failed to load data bundle: {error}. Run{' '}
          <code className="num">python scripts/build_dashboard_data.py</code>.
        </p>
      </div>
    )
  }
  if (!data) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-16">
        <div className="rule-label mb-2">Mobilize</div>
        <div className="num text-sm" style={{ color: 'var(--muted)' }}>
          Loading analysis bundle…
        </div>
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="card" style={{ minHeight: 132 }}>
              <div className="h-2.5 w-20 rounded-sm" style={{ background: 'var(--line)' }} />
              <div className="h-7 w-28 mt-3 rounded-sm" style={{ background: 'var(--line-strong)' }} />
              <div className="h-2.5 w-full mt-3 rounded-sm" style={{ background: 'var(--line)' }} />
            </div>
          ))}
        </div>
      </div>
    )
  }

  const f = data.findings

  return (
    <div className="min-h-screen">
      <header
        className="sticky top-0 z-20"
        style={{
          background: 'rgba(253, 252, 249, 0.92)',
          backdropFilter: 'saturate(1.4) blur(8px)',
          borderBottom: '1px solid var(--line-strong)',
        }}
      >
        <div className="max-w-6xl mx-auto px-6 pt-5 pb-0 flex flex-wrap items-end justify-between gap-x-8 gap-y-3">
          <div>
            <div className="flex items-baseline gap-3">
              <h1
                className="text-[1.65rem] font-bold leading-none"
                style={{ letterSpacing: '-0.03em' }}
              >
                Mobilize
              </h1>
              <span className="num text-[11px]" style={{ color: 'var(--faint)' }}>
                {data.meta.universe} sovereigns · {data.meta.window}
              </span>
            </div>
            <p className="text-[13px] mt-1" style={{ color: 'var(--muted)' }}>
              Sovereign ESG fixed-income risk engine, {data.meta.window} — does the tilt limit downside, and is it priced?
            </p>
          </div>
          <nav className="flex flex-wrap gap-0.5 -mb-px" role="tablist" aria-label="Dashboard sections">
            {TABS.map((t, i) => {
              const selected = tab === t.id
              return (
                <button
                  key={t.id}
                  ref={(el) => { tabsRef.current[t.id] = el }}
                  role="tab"
                  id={`tab-${t.id}`}
                  aria-selected={selected}
                  aria-controls={`panel-${t.id}`}
                  tabIndex={selected ? 0 : -1}
                  onClick={() => onTabChange(t.id)}
                  onKeyDown={(e) => onTabKeyDown(e, i)}                  className="tab-btn"
                >
                  {t.label}
                </button>
              )
            })}
          </nav>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 pt-8 pb-16 space-y-8" id={`panel-${tab}`} role="tabpanel" aria-labelledby={`tab-${tab}`}>
        {/* Headline findings strip */}
        <section aria-label="Headline findings">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-px rounded-sm overflow-hidden"
            style={{ background: 'var(--line-strong)', boxShadow: 'var(--shadow)' }}>
            <FindingCard
              eyebrow="Volatility"
              value="−0.7pp"
              note={`p ${f.volReduction.p_value}`}
              text="ESG tilt significantly reduces vol."
              positive
            />
            <FindingCard
              eyebrow="Return cost"
              value="≈ −0.1pp"
              note={`p ${f.returnCost.p_value}`}
              text="Not statistically distinguishable from zero."
            />
            <FindingCard
              eyebrow="Max drawdown"
              value="~ −19%"
              note="similar across portfolios"
              text="No drawdown protection from the tilt."
            />
            <FindingCard
              eyebrow="ESG priced?"
              value="No"
              note={`F-M t = ${f.pricing.t_newey_west}, p = ${f.pricing.p_value}`}
              text="Score is not a priced factor."
            />
          </div>
        </section>

        {tab === 'risk' && <RiskLab data={data} />}
        {tab === 'map' && (
          <EsgMap
            data={data}
            initialYear={deepLink.year}
            initialCountry={deepLink.country}
          />
        )}
        {tab === 'pricing' && <PricingTest data={data} />}
        {tab === 'outcome' && <OutcomeLab data={data} />}
        {tab === 'method' && <Methodology />}
      </main>

      <footer className="mt-12" style={{ borderTop: '1px solid var(--line-strong)' }}>
        <div className="max-w-6xl mx-auto px-6 py-6 flex flex-wrap gap-x-6 gap-y-2 justify-between text-[12px]" style={{ color: 'var(--muted)' }}>
          <span>
            Built with public data: World Bank API, FRED. Bond returns proxied — see Methodology.
          </span>
          <span>Panel generated {data.meta.generated.slice(0, 10)}</span>
        </div>
      </footer>
    </div>
  )
}

function FindingCard({ eyebrow, value, note, text, positive }) {
  return (
    <div className="finding-card p-5" style={{ background: 'var(--paper)' }}>
      <div className="eyebrow">{eyebrow}</div>
      <div className="flex items-baseline gap-2 mt-1.5">
        <span
          className="text-[1.9rem] font-bold leading-none num"
          style={{ letterSpacing: '-0.02em', color: positive ? 'var(--teal)' : 'var(--ink)' }}
        >
          {value}
        </span>
      </div>
      <div className="text-[11px] num mt-1" style={{ color: 'var(--faint)' }}>{note}</div>
      <div className="text-[13px] mt-2 leading-snug" style={{ color: 'var(--muted)' }}>{text}</div>
    </div>
  )
}
