import { useMemo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, ReferenceLine,
} from 'recharts'
import { fmtNum } from '../hooks.js'

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
        <h2 className="text-lg font-bold">Is the ESG score priced?</h2>
        <p className="text-sm text-gray-500 max-w-3xl">
          Fama–MacBeth (1976): each month, regress country returns on their ESG scores
          (observable a period earlier — no look-ahead). The resulting coefficient
          series γ tells us whether higher-ESG countries systematically earn different returns.
        </p>
      </div>

      {/* Verdict */}
      <div className={`card border-l-4 ${significant ? 'border-l-emerald-500' : 'border-l-gray-400'}`}>
        <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
          <div>
            <div className="text-sm text-gray-500">Mean γ</div>
            <div className="text-2xl font-bold font-mono">
              {fmtNum(fm.gammaMean * 100, 2)}bp<span className="text-sm text-gray-400">/month</span>
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Newey–West t</div>
            <div className="text-2xl font-bold font-mono">{fmtNum(fm.tNeweyWest, 2)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">p-value</div>
            <div className="text-2xl font-bold font-mono">{fmtNum(fm.pValue, 2)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Months</div>
            <div className="text-2xl font-bold font-mono">{fm.nMonths}</div>
          </div>
        </div>
        <p className="text-sm mt-3 text-gray-600 dark:text-gray-300">
          {significant
            ? 'The ESG score is statistically priced in this sample.'
            : 'Verdict: the ESG score is NOT significantly priced — γ is statistically indistinguishable from zero. The ESG tilt shifts the risk profile; it is not an alpha source.'}
        </p>
      </div>

      {/* Histogram of monthly gammas */}
      <div className="card">
        <h3 className="font-semibold mb-1">Distribution of monthly γ (bp)</h3>
        <p className="text-sm text-gray-500 mb-2">Each bar = 2bp bin of the cross-sectional ESG coefficient.</p>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={histData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
            role="img"
            title="Distribution of monthly ESG factor coefficients"
            desc={`Histogram of the ${fm.nMonths} monthly cross-sectional ESG coefficients (γ), in 2bp bins. Mean ${fmtNum(fm.gammaMean * 100, 2)}bp/month.`}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="bin"
              tickFormatter={(b) => (b * 100).toFixed(0)}
              tick={{ fontSize: 11 }}
            />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip
              labelFormatter={(b) => `${(b * 100).toFixed(1)}bp`}
              formatter={(v) => [`${v} months`, 'count']}
            />
            <Bar dataKey="count" fill="#7c3aed" fillOpacity={0.7} />
            <ReferenceLine x={0} stroke="#111827" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Cumulative gamma */}
      <div className="card">
        <h3 className="font-semibold mb-1">Cumulative γ (bp, summed over months)</h3>
        <p className="text-sm text-gray-500 mb-2">
          A persistent drift would indicate pricing; here it wanders around zero.
        </p>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={cumData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
            role="img"
            title="Cumulative ESG factor coefficient over time"
            desc="Sum of monthly γ coefficients in basis points; a persistent drift away from zero would indicate pricing."
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} interval={11} />
            <YAxis tick={{ fontSize: 11 }} unit="bp" />
            <Tooltip formatter={(v) => `${fmtNum(v, 1)}bp`} />
            <Line type="monotone" dataKey="cum" stroke="#0d9488" strokeWidth={2} dot={false} />
            <ReferenceLine y={0} stroke="#111827" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Pillar-level Fama-MacBeth */}
      {data.famaMacbethPillars && (
        <div className="card">
          <h3 className="font-semibold mb-1">Pillar-level test: is any single pillar priced?</h3>
          <p className="text-sm text-gray-500 mb-3">
            The composite null could hide offsetting pillar effects — so we re-run the
            Fama–MacBeth regression on each pillar score separately (same months, same
            Newey–West correction).
          </p>
          <table className="w-full text-sm" aria-label="Pillar-level Fama-MacBeth results">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-200 dark:border-gray-700">
                <th scope="col" className="py-2 pr-4 font-medium">Pillar</th>
                <th scope="col" className="py-2 pr-4 font-medium">γ (bp/month)</th>
                <th scope="col" className="py-2 pr-4 font-medium">Newey–West t</th>
                <th scope="col" className="py-2 pr-4 font-medium">p-value</th>
                <th scope="col" className="py-2 pr-4 font-medium">Verdict</th>
              </tr>
            </thead>
            <tbody>
              {data.famaMacbethPillars.map((p) => {
                const significant = Math.abs(p.tNeweyWest) > 1.96
                return (
                  <tr key={p.pillar} className="border-b border-gray-100 dark:border-gray-800">
                    <td className="py-2 pr-4 font-medium">
                      {{ E: 'Environmental', S: 'Social', G: 'Governance' }[p.pillar] ?? p.pillar}
                    </td>
                    <td className="py-2 pr-4 font-mono">{fmtNum(p.gammaMean * 100, 2)}</td>
                    <td className="py-2 pr-4 font-mono">{fmtNum(p.tNeweyWest, 2)}</td>
                    <td className="py-2 pr-4 font-mono">{fmtNum(p.pValue, 2)}</td>
                    <td className={`py-2 pr-4 font-semibold ${significant ? 'text-emerald-700 dark:text-emerald-400' : 'text-gray-600 dark:text-gray-300'}`}>
                      {significant ? 'priced' : 'not priced'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <p className="text-xs text-gray-500 mt-2">
            {data.famaMacbethPillars.every((p) => Math.abs(p.tNeweyWest) <= 1.96)
              ? 'None of the three pillars is individually priced either — the null is a pillar-level result too, not an artifact of aggregation.'
              : 'At least one pillar shows significant pricing.'}
          </p>
        </div>
      )}

      {/* Monthly gamma strip */}
      <div className="card">
        <h3 className="font-semibold mb-1">Monthly γ (bp)</h3>
        <ResponsiveContainer width="100%" height={160}>
          <LineChart data={monthlyData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} interval={11} />
            <YAxis tick={{ fontSize: 11 }} unit="bp" />
            <Tooltip formatter={(v) => `${fmtNum(v, 2)}bp`} />
            <Line type="monotone" dataKey="gamma" stroke="#2563eb" strokeWidth={1} dot={false} />
            <ReferenceLine y={0} stroke="#111827" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
