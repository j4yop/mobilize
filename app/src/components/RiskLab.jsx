import { useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, Legend,
} from 'recharts'
import { PORTFOLIO_META, fmtPct, fmtNum } from '../hooks.js'

const METRIC_ROWS = [
  { key: 'CAGR', label: 'CAGR (annual)', pct: true, freq: 'annual' },
  { key: 'Volatility', label: 'Volatility (annualized)', pct: true, freq: 'monthly' },
  { key: 'Sharpe', label: 'Sharpe', pct: false, freq: 'monthly' },
  { key: 'Sortino', label: 'Sortino', pct: false, freq: 'monthly' },
  { key: 'Max Drawdown', label: 'Max Drawdown', pct: true, freq: 'monthly' },
  { key: 'VaR 95%', label: 'VaR 95% (monthly)', pct: true, freq: 'monthly' },
  { key: 'CVaR 95%', label: 'CVaR 95% (monthly)', pct: true, freq: 'monthly' },
]

export default function RiskLab({ data }) {
  const [freq, setFreq] = useState('monthly')
  const portfolios = data.meta.portfolios
  const series = data.series[freq]

  // growth + drawdown chart data
  const labels = series[portfolios[0]]?.labels ?? []
  const chartData = labels.map((label, i) => {
    const row = { label }
    for (const p of portfolios) {
      row[p] = series[p]?.growth?.[i]
    }
    return row
  })
  const ddData = labels.map((label, i) => {
    const row = { label }
    for (const p of portfolios) {
      row[p] = series[p]?.drawdown?.[i]
    }
    return row
  })

  // metrics table
  const metricsByPortfolio = {}
  for (const m of data.metrics) {
    if (m.frequency !== freq) continue
    metricsByPortfolio[m.portfolio] = m
  }

  // significance
  const sigs = data.significance.filter((s) => s.frequency === freq)
  const perMonthNote = freq === 'monthly' ? ' (per month — ×12 for annualized)' : ''

  const xTick = freq === 'monthly' ? 12 : 1

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-lg font-bold">Portfolio risk, 2013–2023</h2>
          <p className="text-sm text-gray-500">
            Three portfolios of the same {data.meta.universe}-country universe, annual rebalancing,
            no look-ahead. {freq === 'monthly' ? '131 monthly observations' : '11 annual observations'}.
          </p>
        </div>
        <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1" role="group" aria-label="Sampling frequency">
          {['annual', 'monthly'].map((f) => (
            <button
              key={f}
              onClick={() => setFreq(f)}
              aria-pressed={freq === f}
              className={`px-3 py-1.5 rounded-md text-sm font-medium capitalize ${
                freq === f ? 'bg-white dark:bg-gray-900 shadow' : 'text-gray-600 dark:text-gray-300'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Growth of $1 */}
      <div className="card">
        <h3 className="font-semibold mb-1">Growth of $1</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
            role="img"
            title="Growth of one dollar, 2013 to 2023"
            desc={`Cumulative growth of $1 for the three portfolios over 2013–2023 (${freq} sampling). Full values in the metrics table below.`}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} interval={xTick * 2 - 1} />
            <YAxis tick={{ fontSize: 11 }} domain={['auto', 'auto']} />
            <Tooltip formatter={(v) => `$${Number(v).toFixed(3)}`} />
            <Legend />
            {portfolios.map((p) => (
              <Line
                key={p}
                type="monotone"
                dataKey={p}
                name={PORTFOLIO_META[p]?.label ?? p}
                stroke={PORTFOLIO_META[p]?.color}
                strokeWidth={2}
                dot={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Drawdown */}
      <div className="card">
        <h3 className="font-semibold mb-1">Drawdown (%)</h3>
        <p className="text-sm text-gray-500 mb-2">
          Monthly sampling reveals intra-year drawdowns annual sampling misses.
        </p>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={ddData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
            role="img"
            title="Drawdown from running peak"
            desc={`Percentage decline from the running peak for each portfolio (${freq} sampling). Worst drawdown around −19% to −21%.`}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} interval={xTick * 2 - 1} />
            <YAxis tick={{ fontSize: 11 }} unit="%" />
            <Tooltip formatter={(v) => `${Number(v).toFixed(2)}%`} />
            {portfolios.map((p) => (
              <Area
                key={p}
                type="monotone"
                dataKey={p}
                name={PORTFOLIO_META[p]?.label ?? p}
                stroke={PORTFOLIO_META[p]?.color}
                fill={PORTFOLIO_META[p]?.color}
                fillOpacity={0.08}
                strokeWidth={1.5}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Metrics table */}
      <div className="card overflow-x-auto">
        <h3 className="font-semibold mb-3">Metrics ({freq})</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 border-b border-gray-200 dark:border-gray-700">
              <th className="py-2 pr-4 font-medium">Metric</th>
              {portfolios.map((p) => (
                <th key={p} className="py-2 pr-4 font-medium">
                  {PORTFOLIO_META[p]?.label ?? p}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {METRIC_ROWS.map((row) => {
              const useFreq = metricsByPortfolio[portfolios[0]]?.[row.key] !== undefined
                ? freq
                : row.freq
              const mp = {}
              for (const p of portfolios) {
                const m = data.metrics.find(
                  (x) => x.portfolio === p && x.frequency === useFreq
                )
                mp[p] = m?.[row.key]
              }
              return (
                <tr key={row.key} className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-2 pr-4 text-gray-600 dark:text-gray-300">{row.label}</td>
                  {portfolios.map((p) => (
                    <td key={p} className="py-2 pr-4 font-mono">
                      {row.pct ? fmtPct(mp[p]) : fmtNum(mp[p], 2)}
                    </td>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Significance */}
      <div className="card overflow-x-auto">
        <h3 className="font-semibold mb-1">Statistical significance vs benchmark</h3>
        <p className="text-sm text-gray-500 mb-3">
          Vol: paired permutation test. Return: H0-recentered block bootstrap.
          {perMonthNote}
        </p>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 border-b border-gray-200 dark:border-gray-700">
              <th className="py-2 pr-4 font-medium">Strategy</th>
              <th className="py-2 pr-4 font-medium">Vol diff{perMonthNote ? ' (monthly)' : ''}</th>
              <th className="py-2 pr-4 font-medium">Vol p</th>
              <th className="py-2 pr-4 font-medium">Ret diff{perMonthNote ? ' (monthly)' : ''}</th>
              <th className="py-2 pr-4 font-medium">Ret p</th>
            </tr>
          </thead>
          <tbody>
            {sigs.map((s) => (
              <tr key={s.strategy} className="border-b border-gray-100 dark:border-gray-800">
                <td className="py-2 pr-4">{PORTFOLIO_META[s.strategy]?.label ?? s.strategy}</td>
                <td className="py-2 pr-4 font-mono">{fmtNum(s.volDiff * 100, 3)}pp</td>
                <td className="py-2 pr-4 font-mono">
                  <span className={s.volP < 0.05 ? 'text-emerald-700 dark:text-emerald-400 font-semibold' : ''}>
                    {s.volP < 0.001 ? '<0.001' : s.volP.toFixed(3)}
                  </span>
                </td>
                <td className="py-2 pr-4 font-mono">{fmtNum(s.meanRetDiff * 100, 3)}pp</td>
                <td className="py-2 pr-4 font-mono">
                  <span className={s.meanRetP < 0.05 ? 'text-emerald-700 dark:text-emerald-400 font-semibold' : ''}>
                    {s.meanRetP < 0.001 ? '<0.001' : s.meanRetP.toFixed(3)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
