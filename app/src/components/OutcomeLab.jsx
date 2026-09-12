import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, ReferenceLine, Cell,
} from 'recharts'
import { fmtNum, fmtPct } from '../hooks.js'

export default function OutcomeLab({ data }) {
  const o = data.outcomeBond
  if (!o) {
    return (
      <div className="card text-sm text-gray-500">
        Outcome Bond Lab data not found — run <code>python scripts/run_outcome.py</code>.
      </div>
    )
  }
  const deal = o.deal
  const base = o.baseline
  const sa = o.southAfrica
  const sens = data.outcomeSensitivity ?? []
  const drift = data.outcomeDrift ?? []
  const zafGov = data.zafGovernance

  const tiersData = [
    { tier: '≤0%', payment: 0, p: base.pFail },
    { tier: '0–2%', payment: 36.69, p: base.pTier1 },
    { tier: '2–4%', payment: 73.38, p: base.pTier2 },
    { tier: '>4%', payment: 91.73, p: base.pTier3 },
  ]

  const tierColors = ['#dc2626', '#f59e0b', '#10b981', '#0369a1']

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-lg font-bold">Outcome Bond Lab — the "Rhino Bond"</h2>
        <p className="text-sm text-gray-500 max-w-3xl">
          The World Bank's Wildlife Conservation Bond (Mar 2022): USD {deal.sizeUsd / 1e6}m, 5-year,
          priced at {fmtPct(deal.issuePrice)} with no coupon — investors instead get a
          GEF-funded success payment tiered on black-rhino population growth at Addo Elephant NP
          and Great Fish River NR, South Africa. Principal is IBRD-protected. We price it with
          Monte Carlo (100k paths).
        </p>
      </div>

      {/* Deal anatomy */}
      <div className="card">
        <h3 className="font-semibold mb-2">Cash-flow envelope (per $1,000)</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
          <Box label="Pay at t=0" value={`$${(deal.issuePrice * 1000).toFixed(2)}`} note="issue price 94.84" />
          <Box label="Receive at T" value="$1,000" note="par redemption (AAA)" />
          <Box label="Success payment" value="$0 – $91.73" note="GEF-funded, tiered on growth" />
          <Box
            label="Conservation funded"
            value={`$${(deal.conservationUsd / 1e6).toFixed(1)}m`}
            note="ZAR 152m / 15.0 (Mar-2022 FX)"
          />
        </div>
      </div>

      {/* Baseline pricing */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="font-semibold mb-1">Tier probabilities (baseline)</h3>
          <p className="text-xs text-gray-500 mb-2">
            GBM population model: 4%/yr drift, 3% vol. KPI = annualized 5y growth rate.
          </p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={tiersData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
              role="img"
              title="Success payment tier probabilities"
              desc={`Probability of each rhino-growth outcome tier under the baseline model (4%/yr drift): no success ${fmtPct(base.pFail)}, 0–2% ${fmtPct(base.pTier1)}, 2–4% ${fmtPct(base.pTier2)}, >4% ${fmtPct(base.pTier3)}.`}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="tier" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 11 }} domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
              <Tooltip formatter={(v) => `${fmtPct(v)}`} />
              <Bar dataKey="p" radius={[4, 4, 0, 0]}>
                {tiersData.map((_, i) => (
                  <Cell key={i} fill={tierColors[i]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="font-semibold mb-3">Investor economics</h3>
          <Row label="Expected success payment" value={`$${fmtNum(base.expectedSuccessPer1000, 2)} / $1,000`} />
          <Row label="Expected total (GEF)" value={`$${fmtNum(base.expectedTotalSuccessUsd, 2)}m`} />
          <Row label="Investor E[return]" value={fmtPct(base.expectedAnnualReturn)} strong />
          <Row label="Vanilla IBRD 5y yield" value={fmtPct(base.vanillaYield)} />
          <Row
            label="Premium vs vanilla"
            value={`${base.concessionPp > 0 ? '+' : ''}${fmtNum(base.concessionPp, 2)}pp`}
            strong={base.concessionPp < 0}
          />
          <Row label="Donor E[outlay] (GEF)" value={`$${fmtNum(base.donorExpectedOutlayUsd, 2)}m`} />
          <Row label="Donor leverage" value={`${fmtNum(base.donorLeverage, 2)}x`} />
          {sa && (
            <p className="text-xs text-gray-500 mt-3 pt-2 border-t border-gray-200 dark:border-gray-700">
              With South Africa's governance score ({zafGov}/100, from this repo's ESG panel):
              E[success] ${fmtNum(sa.expectedSuccessPer1000, 2)}/$1k, E[return] {fmtPct(sa.expectedAnnualReturn)}.
            </p>
          )}
        </div>
      </div>

      {/* Drift sensitivity */}
      <div className="card">
        <h3 className="font-semibold mb-1">Sensitivity to conservation effectiveness</h3>
        <p className="text-sm text-gray-500 mb-2">
          The drift (annual growth) assumption is the model's most sensitive input —
          the bond's economics swing from near-parity to a large investor premium.
        </p>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={drift} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
            role="img"
            title="Expected success payment by growth drift assumption"
            desc="Expected success payment per $1,000 as the assumed annual rhino population growth (drift) varies. Exact values in the table below."
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="drift" tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 11 }} domain={[0, 100]} unit="$" />
            <Tooltip
              labelFormatter={(v) => `drift ${(v * 100).toFixed(0)}%`}
              formatter={(v, name) =>
                name === 'expectedSuccessPer1000' ? [`$${fmtNum(v, 2)}`, 'E[success]/$1k'] : [fmtPct(v), 'E[return]']
              }
            />
            <Bar dataKey="expectedSuccessPer1000" fill="#0369a1" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        <table className="w-full text-xs mt-3">
          <thead>
            <tr className="text-left text-gray-500 border-b border-gray-200 dark:border-gray-700">
              <th className="py-1">Drift</th>
              <th>P(&gt;4%)</th>
              <th>E[success]/$1k</th>
              <th>E[return]</th>
              <th>Premium vs vanilla</th>
              <th>Leverage</th>
            </tr>
          </thead>
          <tbody>
            {drift.map((r) => (
              <tr key={r.drift} className="border-b border-gray-100 dark:border-gray-800">
                <td className="py-1 font-mono">{fmtPct(r.drift, 0)}</td>
                <td className="py-1 font-mono">{fmtPct(r.pTier3)}</td>
                <td className="py-1 font-mono">${fmtNum(r.expectedSuccessPer1000)}</td>
                <td className="py-1 font-mono">{fmtPct(r.expectedAnnualReturn)}</td>
                <td className="py-1 font-mono">{fmtNum(r.concessionPp, 2)}pp</td>
                <td className="py-1 font-mono">{fmtNum(r.donorLeverage)}x</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Governance sensitivity — the novel link */}
      <div className="card">
        <h3 className="font-semibold mb-1">The governance success premium</h3>
        <p className="text-sm text-gray-500 mb-2">
          Holding investor economics fixed, how large a success payment must a donor offer as
          country governance (execution capacity) varies? Lower governance → lower conservation
          success probability → the donor must compensate more. This links the repo's ESG panel
          to outcome-bond structuring.
          {zafGov && ` South Africa scores ${zafGov}/100.`}
        </p>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={sens} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
            role="img"
            title="Required success payment by governance score"
            desc="Success payment a donor must offer per $1,000 to hold investor economics fixed, as the issuer-country governance score ranges 10 to 90. The red dashed line marks South Africa's score."
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="govScore" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} domain={['auto', 'auto']} unit="$" />
            <Tooltip
              labelFormatter={(g) => `governance ${g}/100`}
              formatter={(v) => [`$${fmtNum(v, 2)}`, 'required success / $1,000']}
            />
            <Line type="monotone" dataKey="requiredSuccessPer1000" stroke="#7c3aed" strokeWidth={2.5} dot />
            {zafGov && (
              <ReferenceLine x={zafGov} stroke="#dc2626" strokeDasharray="4 4" label="South Africa" />
            )}
            <ReferenceLine y={91.73} stroke="#9ca3af" strokeDasharray="3 3" label="max tier" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* IBRD outcome-bond family */}
      {data.outcomeBondFamily && data.outcomeBondFamily.length > 0 && (
        <div className="card overflow-x-auto">
          <h3 className="font-semibold mb-1">The IBRD outcome-bond family (all seven, official terms)</h3>
          <p className="text-sm text-gray-500 mb-3">
            The Rhino Bond pioneered the structure in 2022; six more outcome bonds
            followed. All transfer project performance risk to investors via
            outcome-linked coupons or success payments — funded not by donors but by
            credit sales (ITMOs, CRUs, VCUs, plastic credits) with corporate offtakers.
          </p>
          <table className="w-full text-sm" aria-label="IBRD outcome bond family comparison">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-200 dark:border-gray-700">
                <th scope="col" className="py-2 pr-4 font-medium">Bond</th>
                <th scope="col" className="py-2 pr-4 font-medium">Size</th>
                <th scope="col" className="py-2 pr-4 font-medium">Tenor</th>
                <th scope="col" className="py-2 pr-4 font-medium">Min ret</th>
                <th scope="col" className="py-2 pr-4 font-medium">Max ret</th>
                <th scope="col" className="py-2 pr-4 font-medium">Outcome unit</th>
                <th scope="col" className="py-2 pr-4 font-medium">Offtake partner</th>
                <th scope="col" className="py-2 font-medium">Structure</th>
              </tr>
            </thead>
            <tbody>
              {data.outcomeBondFamily.map((b) => (
                <tr
                  key={b.key}
                  className={`border-b border-gray-100 dark:border-gray-800 ${
                    b.key === 'rhino' ? 'bg-blue-50 dark:bg-blue-900/30' : ''
                  }`}
                >
                  <td className="py-2 pr-4">
                    {b.url ? (
                      <a href={b.url} target="_blank" rel="noreferrer" className="text-blue-700 dark:text-blue-300 hover:underline">
                        {b.name}
                      </a>
                    ) : (
                      b.name
                    )}
                    <div className="text-xs text-gray-500">{b.country} · {b.theme}</div>
                  </td>
                  <td className="py-2 pr-4 font-mono">${fmtNum(b.sizeUsd / 1e6, 0)}m</td>
                  <td className="py-2 pr-4 font-mono">{fmtNum(b.tenorYears, 1)}y</td>
                  <td className="py-2 pr-4 font-mono">{fmtPct(b.guaranteedReturn)}</td>
                  <td className="py-2 pr-4 font-mono">{fmtPct(b.maxTotalReturn)}</td>
                  <td className="py-2 pr-4 text-xs">{b.outcomeUnit}</td>
                  <td className="py-2 pr-4 text-xs">{b.outcomePayer}</td>
                  <td className="py-2 text-xs">
                    {b.structure}
                    {!b.principalProtected && (
                      <span className="ml-1 text-red-700 dark:text-red-400 font-semibold" title="50% of principal was conditional on donation receipts">
                        ⚠ principal at risk
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs text-gray-500 mt-2">
            Min ret = guaranteed floor (fixed coupon or issue discount); Max ret = official
            maximum potential return from the World Bank Q&amp;A documents. The Rhino Bond's
            range spans the GEF success tiers; the UNICEF note's principal (50%) was
            conditional on donation receipts — the only capital-at-risk structure in the family.
          </p>
        </div>
      )}

      <p className="text-xs text-gray-400 max-w-3xl">
        Model: GBM rhino population (annualized growth KPI), antithetic 100k paths. Deal terms from
        the official World Bank press release (all public). Drift/vol calibrated to the parks'
        reported track record; governance elasticities are disclosed assumptions, not fitted
        values. See the Methodology tab.
      </p>
    </div>
  )
}

function Box({ label, value, note }) {
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
        <div className="text-gray-600 dark:text-gray-300 text-xs">{label}</div>
        <div className="font-bold text-lg font-mono mt-0.5">{value}</div>
      <div className="text-gray-600 dark:text-gray-300 text-xs">{note}</div>
    </div>
  )
}

function Row({ label, value, strong }) {
  return (
    <div className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-800">
      <span className="text-gray-500">{label}</span>
      <span className={`font-mono ${strong ? 'font-bold text-emerald-600 dark:text-emerald-400' : ''}`}>
        {value}
      </span>
    </div>
  )
}
