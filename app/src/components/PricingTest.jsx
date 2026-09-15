import { useMemo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, ReferenceLine,
} from 'recharts'
import { CHART, fmtNum } from '../hooks.js'

export default function PricingTest({ data }) {
  const fm = data.famaMacbeth
  const g = fm.series

  const histData = useMemo(() => {
    const bins = {}
    const width = 0.02
    for (const v of g.gamma) {
      const b = Math.floor(v / width) * width
      bins[b] = (bins[b] ?? 0) + 1
    }
    return Object.entries(bins)
      .map(([b, count]) => ({ bin: Number(b), count }))
      .sort((a, b) => a.bin - b.bin)
  }, [g])

  const cumData = g.labels.map((label, i) => ({ label, cum: g.cumGamma[i] * 100 }))
  const monthlyData = g.labels.map((label, i) => ({ label, gamma: g.gamma[i] * 100 }))

  const significant = Math.abs(fm.tNeweyWest) > 1.96

  return (
    <div className="space-y-8">
      <div>
        <div className="eyebrow mb-1">03 — Pricing</div>
        <h2 className="text-lg font-bold tracking-tight">Is the ESG score priced?</h2>
        <p className="text-sm mt-0.5 max-w-3xl" style={{ color: 'var(--muted)' }}>
          Fama–MacBeth (1976): each month, regress country returns on their ESG scores
          (observable a period earlier — no look-ahead). The resulting coefficient
          series γ tells us whether higher-ESG countries systematically earn different returns.
        </p>
      </div>

      {/* Verdict */}
      <div
        className="card"
        style={
          significant
            ? { borderLeft: '4px solid var(--teal)' }
            : { borderLeft: '4px solid var(--line-strong)' }
        }
      >
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-4">
          <Stat label="Mean γ" value={`${fmtNum(fm.gammaMean * 100, 2)}bp`} sub="/month" />
          <Stat label="Newey–West t" value={fmtNum(fm.tNeweyWest, 2)} />
          <Stat label="p-value" value={fmtNum(fm.pValue, 2)} />
          <Stat label="Months" value={fm.nMonths} />
        </div>
        <p className="text-sm mt-4 pt-3" style={{ borderTop: '1px solid var(--line)', color: 'var(--muted)' }}>
          {significant
            ? 'The ESG score is statistically priced in this sample.'
            : 'Verdict: the ESG score is NOT significantly priced — γ is statistically indistinguishable from zero. The ESG tilt shifts the risk profile; it is not an alpha source.'}
        </p>
      </div>

      {/* Histogram of monthly gammas */}
      <div className="card">
        <h3 className="font-semibold tracking-tight mb-1">Distribution of monthly γ (bp)</h3>
        <p className="text-sm mb-3" style={{ color: 'var(--muted)' }}>
          Each bar = 2bp bin of the cross-sectional ESG coefficient.
        </p>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={histData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
            role="img"
            title="Distribution of monthly ESG factor coefficients"
            desc={`Histogram of the ${fm.nMonths} monthly cross-sectional ESG coefficients (γ), in 2bp bins. Mean ${fmtNum(fm.gammaMean * 100, 2)}bp/month.`}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
            <XAxis
              dataKey="bin"
              tickFormatter={(b) => (b * 100).toFixed(0)}
              tick={CHART.axisTick}
              axisLine={CHART.axisLine}
              tickLine={false}
            />
            <YAxis tick={CHART.axisTick} axisLine={false} tickLine={false} />
            <Tooltip
              labelFormatter={(b) => `${(b * 100).toFixed(1)}bp`}
              formatter={(v) => [`${v} months`, 'count']}
              {...CHART.tooltip}
            />
            <Bar dataKey="count" fill="var(--sky)" fillOpacity={0.75} radius={[1, 1, 0, 0]} />
            <ReferenceLine x={0} stroke="var(--ink)" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Cumulative gamma */}
      <div className="card">
        <h3 className="font-semibold tracking-tight mb-1">Cumulative γ (bp, summed over months)</h3>
        <p className="text-sm mb-3" style={{ color: 'var(--muted)' }}>
          A persistent drift would indicate pricing; here it wanders around zero.
        </p>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={cumData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
            role="img"
            title="Cumulative ESG factor coefficient over time"
            desc="Sum of monthly γ coefficients in basis points; a persistent drift away from zero would indicate pricing."
          >
            <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
            <XAxis dataKey="label" tick={CHART.axisTick} interval={11} axisLine={CHART.axisLine} tickLine={false} />
            <YAxis tick={CHART.axisTick} unit="bp" axisLine={false} tickLine={false} />
            <Tooltip formatter={(v) => [`${fmtNum(v, 1)}bp`]} {...CHART.tooltip} />
            <Line type="monotone" dataKey="cum" stroke="var(--teal)" strokeWidth={2} dot={false} activeDot={{ r: 3, strokeWidth: 0 }} />
            <ReferenceLine y={0} stroke="var(--ink)" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Pillar-level Fama-MacBeth */}
      {data.famaMacbethPillars && (
        <div className="card overflow-x-auto">
          <h3 className="font-semibold tracking-tight mb-1">Pillar-level test: is any single pillar priced?</h3>
          <p className="text-sm mb-3" style={{ color: 'var(--muted)' }}>
            The composite null could hide offsetting pillar effects — so we re-run the
            Fama–MacBeth regression on each pillar score separately (same months, same
            Newey–West correction).
          </p>
          <table className="data" aria-label="Pillar-level Fama-MacBeth results">
            <thead>
              <tr>
                <th scope="col">Pillar</th>
                <th scope="col" className="text-right">γ (bp/month)</th>
                <th scope="col" className="text-right">Newey–West t</th>
                <th scope="col" className="text-right">p-value</th>
                <th scope="col" className="text-right pr-4 last:pr-0">Verdict</th>
              </tr>
            </thead>
            <tbody>
              {data.famaMacbethPillars.map((p) => {
                const significant = Math.abs(p.tNeweyWest) > 1.96
                return (
                  <tr key={p.pillar}>
                    <td className="font-medium">
                      {{ E: 'Environmental', S: 'Social', G: 'Governance' }[p.pillar] ?? p.pillar}
                    </td>
                    <td className="num text-right">{fmtNum(p.gammaMean * 100, 2)}</td>
                    <td className="num text-right">{fmtNum(p.tNeweyWest, 2)}</td>
                    <td className="num text-right">{fmtNum(p.pValue, 2)}</td>
                    <td className="text-right pr-4 last:pr-0">
                      <span
                        className="px-1.5 py-0.5 rounded-sm text-xs font-semibold"
                        style={
                          significant
                            ? { background: 'rgba(46,107,94,0.12)', color: 'var(--teal)' }
                            : { background: 'rgba(42,58,72,0.07)', color: 'var(--muted)' }
                        }
                      >
                        {significant ? 'priced' : 'not priced'}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <p className="tick-note mt-2">
            {data.famaMacbethPillars.every((p) => Math.abs(p.tNeweyWest) <= 1.96)
              ? 'None of the three pillars is individually priced either — the null is a pillar-level result too, not an artifact of aggregation.'
              : 'At least one pillar shows significant pricing.'}
          </p>
        </div>
      )}

      {/* Monthly gamma strip */}
      <div className="card">
        <h3 className="font-semibold tracking-tight mb-3">Monthly γ (bp)</h3>
        <ResponsiveContainer width="100%" height={160}>
          <LineChart data={monthlyData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
            <XAxis dataKey="label" tick={CHART.axisTick} interval={11} axisLine={CHART.axisLine} tickLine={false} />
            <YAxis tick={CHART.axisTick} unit="bp" axisLine={false} tickLine={false} />
            <Tooltip formatter={(v) => [`${fmtNum(v, 2)}bp`]} {...CHART.tooltip} />
            <Line type="monotone" dataKey="gamma" stroke="var(--sky)" strokeWidth={1} dot={false} />
            <ReferenceLine y={0} stroke="var(--ink)" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function Stat({ label, value, sub }) {
  return (
    <div>
      <div className="rule-label">{label}</div>
      <div className="flex items-baseline gap-1 mt-1">
        <span className="text-[1.55rem] font-semibold num leading-none" style={{ letterSpacing: '-0.02em' }}>
          {value}
        </span>
        {sub && <span className="text-xs num" style={{ color: 'var(--faint)' }}>{sub}</span>}
      </div>
    </div>
  )
}
