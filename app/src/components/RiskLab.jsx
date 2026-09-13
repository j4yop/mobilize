import { useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, Legend,
} from 'recharts'
import { PORTFOLIO_META, CHART, fmtPct, fmtNum } from '../hooks.js'

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
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <div className="eyebrow mb-1">01 — Backtest</div>
          <h2 className="text-lg font-bold tracking-tight">Portfolio risk, 2013–2023</h2>
          <p className="text-sm mt-0.5 max-w-xl" style={{ color: 'var(--muted)' }}>
            Three portfolios of the same {data.meta.universe}-country universe, annual rebalancing,
            no look-ahead. {freq === 'monthly' ? '131 monthly observations' : '11 annual observations'}.
          </p>
        </div>
        <div className="seg" role="group" aria-label="Sampling frequency">
          {['annual', 'monthly'].map((f) => (
            <button
              key={f}
              onClick={() => setFreq(f)}
              aria-pressed={freq === f}
              className="capitalize"
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Growth of $1 */}
      <div className="card">
        <h3 className="font-semibold tracking-tight mb-3">Growth of $1</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
            role="img"
            title="Growth of one dollar, 2013 to 2023"
            desc={`Cumulative growth of $1 for the three portfolios over 2013–2023 (${freq} sampling). Full values in the metrics table below.`}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
            <XAxis dataKey="label" tick={CHART.axisTick} interval={xTick * 2 - 1} axisLine={CHART.axisLine} tickLine={false} />
            <YAxis tick={CHART.axisTick} domain={['auto', 'auto']} axisLine={false} tickLine={false} />
            <Tooltip formatter={(v) => [`$${Number(v).toFixed(3)}`]} {...CHART.tooltip} />
            <Legend
              iconType="plainline"
              iconSize={14}
              wrapperStyle={{ fontSize: 12, color: 'var(--muted)', paddingTop: 8 }}
            />
            {portfolios.map((p) => (
              <Line
                key={p}
                type="monotone"
                dataKey={p}
                name={PORTFOLIO_META[p]?.label ?? p}
                stroke={PORTFOLIO_META[p]?.color}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 3, strokeWidth: 0 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Drawdown */}
      <div className="card">
        <h3 className="font-semibold tracking-tight mb-1">Drawdown (%)</h3>
        <p className="text-sm mb-3" style={{ color: 'var(--muted)' }}>
          Monthly sampling reveals intra-year drawdowns annual sampling misses.
        </p>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={ddData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
            role="img"
            title="Drawdown from running peak"
            desc={`Percentage decline from the running peak for each portfolio (${freq} sampling). Worst drawdown around −19% to −21%.`}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
            <XAxis dataKey="label" tick={CHART.axisTick} interval={xTick * 2 - 1} axisLine={CHART.axisLine} tickLine={false} />
            <YAxis tick={CHART.axisTick} unit="%" axisLine={false} tickLine={false} />
            <Tooltip formatter={(v) => [`${Number(v).toFixed(2)}%`]} {...CHART.tooltip} />
            {portfolios.map((p) => (
              <Area
                key={p}
                type="monotone"
                dataKey={p}
                name={PORTFOLIO_META[p]?.label ?? p}
                stroke={PORTFOLIO_META[p]?.color}
                fill={PORTFOLIO_META[p]?.color}
                fillOpacity={0.07}
                strokeWidth={1.5}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Metrics table */}
      <div className="card overflow-x-auto">
        <h3 className="font-semibold tracking-tight mb-3">Metrics ({freq})</h3>
        <table className="data">
          <thead>
            <tr>
              <th>Metric</th>
              {portfolios.map((p) => (
                <th key={p} className="text-right pr-4 last:pr-0">
                  <span className="flex items-center justify-end gap-1.5 normal-case tracking-normal text-[11px]" style={{ color: 'var(--ink)' }}>
                    <span className="inline-block w-2 h-2 rounded-[1px]" style={{ background: PORTFOLIO_META[p]?.color }} />
                    {PORTFOLIO_META[p]?.label ?? p}
                  </span>
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
                <tr key={row.key}>
                  <td style={{ color: 'var(--muted)' }}>{row.label}</td>
                  {portfolios.map((p) => (
                    <td key={p} className="num text-right pr-4 last:pr-0">
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
        <h3 className="font-semibold tracking-tight mb-1">Statistical significance vs benchmark</h3>
        <p className="text-sm mb-3" style={{ color: 'var(--muted)' }}>
          Vol: paired permutation test. Return: H0-recentered block bootstrap.
          {perMonthNote}
        </p>
        <table className="data">
          <thead>
            <tr>
              <th>Strategy</th>
              <th className="text-right">Vol diff{perMonthNote ? ' (monthly)' : ''}</th>
              <th className="text-right">Vol p</th>
              <th className="text-right">Ret diff{perMonthNote ? ' (monthly)' : ''}</th>
              <th className="text-right pr-4 last:pr-0">Ret p</th>
            </tr>
          </thead>
          <tbody>
            {sigs.map((s) => (
              <tr key={s.strategy}>
                <td>{PORTFOLIO_META[s.strategy]?.label ?? s.strategy}</td>
                <td className="num text-right">{fmtNum(s.volDiff * 100, 3)}pp</td>
                <td className="num text-right">
                  <span
                    className={
                      s.volP < 0.05
                        ? 'font-semibold px-1.5 py-0.5 rounded-sm'
                        : ''
                    }
                    style={
                      s.volP < 0.05
                        ? { background: 'rgba(46,107,94,0.12)', color: 'var(--teal)' }
                        : undefined
                    }
                  >
                    {s.volP < 0.001 ? '<0.001' : s.volP.toFixed(3)}
                  </span>
                </td>
                <td className="num text-right">{fmtNum(s.meanRetDiff * 100, 3)}pp</td>
                <td className="num text-right pr-4 last:pr-0">
                  <span
                    className={
                      s.meanRetP < 0.05
                        ? 'font-semibold px-1.5 py-0.5 rounded-sm'
                        : ''
                    }
                    style={
                      s.meanRetP < 0.05
                        ? { background: 'rgba(46,107,94,0.12)', color: 'var(--teal)' }
                        : undefined
                    }
                  >
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
