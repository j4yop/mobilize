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
          <BarChart data={histData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
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
          <LineChart data={cumData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} interval={11} />
            <YAxis tick={{ fontSize: 11 }} unit="bp" />
            <Tooltip formatter={(v) => `${fmtNum(v, 1)}bp`} />
            <Line type="monotone" dataKey="cum" stroke="#0d9488" strokeWidth={2} dot={false} />
            <ReferenceLine y={0} stroke="#111827" />
          </LineChart>
        </ResponsiveContainer>
      </div>

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
