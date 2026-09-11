import { useState } from 'react'
import { useDashboardData, PORTFOLIO_META } from './hooks.js'
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

export default function App() {
  const { data, error } = useDashboardData()
  const [tab, setTab] = useState('risk')

  if (error) {
    return (
      <div className="max-w-3xl mx-auto p-8 text-red-600">
        Failed to load data bundle: {error}. Run{' '}
        <code>python scripts/build_dashboard_data.py</code>.
      </div>
    )
  }
  if (!data) return <div className="max-w-3xl mx-auto p-8">Loading analysis bundle…</div>

  const f = data.findings

  return (
    <div className="min-h-screen">
      <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 sticky top-0 z-20">
        <div className="max-w-6xl mx-auto px-6 py-4 flex flex-wrap items-center gap-x-8 gap-y-3">
          <div>
            <h1 className="text-xl font-bold tracking-tight">Mobilize</h1>
            <p className="text-sm text-gray-500">
              Sovereign ESG fixed-income risk engine — {data.meta.universe} countries, {data.meta.window}
            </p>
          </div>
          <nav className="flex gap-1">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  tab === t.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {/* Headline findings strip */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <FindingCard
            title="Volatility"
            value="−0.7pp"
            tone="good"
            note={`p ${f.volReduction.p_value}`}
            text="ESG tilt significantly reduces vol."
          />
          <FindingCard
            title="Return cost"
            value="≈ −0.1pp"
            tone="neutral"
            note={`p ${f.returnCost.p_value}`}
            text="Not statistically distinguishable from zero."
          />
          <FindingCard
            title="Max drawdown"
            value="~ −19%"
            tone="neutral"
            note="similar across portfolios"
            text="No drawdown protection from the tilt."
          />
          <FindingCard
            title="ESG priced?"
            value="No"
            tone="neutral"
            note={`F-M t = ${f.pricing.t_newey_west}, p = ${f.pricing.p_value}`}
            text="Score is not a priced factor."
          />
        </div>

        {tab === 'risk' && <RiskLab data={data} />}
        {tab === 'map' && <EsgMap data={data} />}
        {tab === 'pricing' && <PricingTest data={data} />}
        {tab === 'outcome' && <OutcomeLab data={data} />}
        {tab === 'method' && <Methodology />}
      </main>

      <footer className="border-t border-gray-200 dark:border-gray-800 mt-12">
        <div className="max-w-6xl mx-auto px-6 py-6 text-sm text-gray-500 flex flex-wrap gap-x-6 justify-between">
          <span>
            Built with public data: World Bank API, FRED. Bond returns proxied — see Methodology.
          </span>
          <span>{PORTFOLIO_META[data.meta.benchmark] ? 'Benchmark: GDP-weighted' : ''}</span>
        </div>
      </footer>
    </div>
  )
}

function FindingCard({ title, value, note, text, tone }) {
  const toneClass =
    tone === 'good'
      ? 'text-emerald-600 dark:text-emerald-400'
      : 'text-gray-900 dark:text-gray-100'
  return (
    <div className="card">
      <div className="text-sm text-gray-500 font-medium">{title}</div>
      <div className={`text-3xl font-bold mt-1 ${toneClass}`}>{value}</div>
      <div className="text-xs text-gray-400 mt-0.5">{note}</div>
      <div className="text-sm mt-2 text-gray-600 dark:text-gray-300">{text}</div>
    </div>
  )
}
