import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, ReferenceLine, Cell,
} from 'recharts'
import { CHART, fmtNum, fmtPct } from '../hooks.js'

export default function OutcomeLab({ data }) {
  const o = data.outcomeBond
  if (!o) {
    return (
      <div className="card text-sm" style={{ color: 'var(--muted)' }}>
        Outcome Bond Lab data not found — run <code className="num">python scripts/run_outcome.py</code>.
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

  const tierColors = ['var(--ser)', 'var(--gold)', 'var(--teal)', 'var(--sky)']

  return (
    <div className="space-y-8">
      <div>
        <div className="eyebrow mb-1">04 — Structuring</div>
        <h2 className="text-lg font-bold tracking-tight">Outcome Bond Lab — the “Rhino Bond”</h2>
        <p className="text-sm mt-0.5 max-w-3xl" style={{ color: 'var(--muted)' }}>
          The World Bank's Wildlife Conservation Bond (Mar 2022): USD {deal.sizeUsd / 1e6}m, 5-year,
          priced at {fmtPct(deal.issuePrice)} with no coupon — investors instead get a
          GEF-funded success payment tiered on black-rhino population growth at Addo Elephant NP
          and Great Fish River NR, South Africa. Principal is IBRD-protected. We price it with
          Monte Carlo (100k paths).
        </p>
      </div>

      {/* Deal anatomy */}
      <div className="card">
        <h3 className="font-semibold tracking-tight mb-3">Cash-flow envelope (per $1,000)</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
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
          <h3 className="font-semibold tracking-tight mb-1">Tier probabilities (baseline)</h3>
          <p className="text-xs mb-3" style={{ color: 'var(--muted)' }}>
            GBM population model: 4%/yr drift, 3% vol. KPI = annualized 5y growth rate.
          </p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={tiersData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
              role="img"
              title="Success payment tier probabilities"
              desc={`Probability of each rhino-growth outcome tier under the baseline model (4%/yr drift): no success ${fmtPct(base.pFail)}, 0–2% ${fmtPct(base.pTier1)}, 2–4% ${fmtPct(base.pTier2)}, >4% ${fmtPct(base.pTier3)}.`}
            >
              <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
              <XAxis dataKey="tier" tick={{ ...CHART.axisTick, fontSize: 12 }} axisLine={CHART.axisLine} tickLine={false} />
              <YAxis tick={CHART.axisTick} domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} axisLine={false} tickLine={false} />
              <Tooltip formatter={(v) => [fmtPct(v)]} {...CHART.tooltip} />
              <Bar dataKey="p" radius={[1, 1, 0, 0]}>
                {tiersData.map((_, i) => (
                  <Cell key={i} fill={tierColors[i]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="font-semibold tracking-tight mb-3">Investor economics</h3>
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
            <p className="text-xs mt-3 pt-3" style={{ borderTop: '1px solid var(--line)', color: 'var(--muted)' }}>
              With South Africa's governance score ({zafGov}/100, from this repo's ESG panel):
              E[success] ${fmtNum(sa.expectedSuccessPer1000, 2)}/$1k, E[return] {fmtPct(sa.expectedAnnualReturn)}.
            </p>
          )}
        </div>
      </div>

      {/* Drift sensitivity */}
      <div className="card overflow-x-auto">
        <h3 className="font-semibold tracking-tight mb-1">Sensitivity to conservation effectiveness</h3>
        <p className="text-sm mb-3" style={{ color: 'var(--muted)' }}>
          The drift (annual growth) assumption is the model's most sensitive input —
          the bond's economics swing from near-parity to a large investor premium.
        </p>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={drift} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
            role="img"
            title="Expected success payment by growth drift assumption"
            desc="Expected success payment per $1,000 as the assumed annual rhino population growth (drift) varies. Exact values in the table below."
          >
            <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
            <XAxis dataKey="drift" tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} tick={{ ...CHART.axisTick, fontSize: 12 }} axisLine={CHART.axisLine} tickLine={false} />
            <YAxis tick={CHART.axisTick} domain={[0, 100]} unit="$" axisLine={false} tickLine={false} />
            <Tooltip
              labelFormatter={(v) => `drift ${(v * 100).toFixed(0)}%`}
              formatter={(v, name) =>
                name === 'expectedSuccessPer1000' ? [`$${fmtNum(v, 2)}`, 'E[success]/$1k'] : [fmtPct(v), 'E[return]']
              }
              {...CHART.tooltip}
            />
            <Bar dataKey="expectedSuccessPer1000" fill="var(--sky)" radius={[1, 1, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        <table className="data text-xs mt-3">
          <thead>
            <tr>
              <th>Drift</th>
              <th className="text-right">P(&gt;4%)</th>
              <th className="text-right">E[success]/$1k</th>
              <th className="text-right">E[return]</th>
              <th className="text-right">Premium</th>
              <th className="text-right pr-4 last:pr-0">Leverage</th>
            </tr>
          </thead>
          <tbody>
            {drift.map((r) => (
              <tr key={r.drift}>
                <td className="num">{fmtPct(r.drift, 0)}</td>
                <td className="num text-right">{fmtPct(r.pTier3)}</td>
                <td className="num text-right">${fmtNum(r.expectedSuccessPer1000)}</td>
                <td className="num text-right">{fmtPct(r.expectedAnnualReturn)}</td>
                <td className="num text-right">{fmtNum(r.concessionPp, 2)}pp</td>
                <td className="num text-right pr-4 last:pr-0">{fmtNum(r.donorLeverage)}x</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Governance sensitivity — the novel link */}
      <div className="card">
        <h3 className="font-semibold tracking-tight mb-1">The governance success premium</h3>
        <p className="text-sm mb-3" style={{ color: 'var(--muted)' }}>
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
            desc="Success payment a donor must offer per $1,000 to hold investor economics fixed, as the issuer-country governance score ranges 10 to 90. The dashed line marks South Africa's score."
          >
            <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
            <XAxis dataKey="govScore" tick={CHART.axisTick} axisLine={CHART.axisLine} tickLine={false} />
            <YAxis tick={CHART.axisTick} domain={['auto', 'auto']} unit="$" axisLine={false} tickLine={false} />
            <Tooltip
              labelFormatter={(g) => `governance ${g}/100`}
              formatter={(v) => [`$${fmtNum(v, 2)}`, 'required success / $1,000']}
              {...CHART.tooltip}
            />
            <Line type="monotone" dataKey="requiredSuccessPer1000" stroke="var(--accent)" strokeWidth={2.5} dot={{ r: 2, fill: 'var(--accent)', strokeWidth: 0 }} activeDot={{ r: 4, strokeWidth: 0 }} />
            {zafGov && (
              <ReferenceLine x={zafGov} stroke="var(--ser)" strokeDasharray="4 4" label={{ value: 'South Africa', fill: 'var(--ser)', fontSize: 11, position: 'insideTopLeft' }} />
            )}
            <ReferenceLine y={91.73} stroke="var(--faint)" strokeDasharray="3 3" label={{ value: 'max tier', fill: 'var(--faint)', fontSize: 11, position: 'insideBottomRight' }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* IBRD outcome-bond family */}
      {data.outcomeBondFamily && data.outcomeBondFamily.length > 0 && (
        <div className="card overflow-x-auto">
          <h3 className="font-semibold tracking-tight mb-1">The IBRD outcome-bond family (all seven, official terms)</h3>
          <p className="text-sm mb-3" style={{ color: 'var(--muted)' }}>
            The Rhino Bond pioneered the structure in 2022; six more outcome bonds
            followed. All transfer project performance risk to investors via
            outcome-linked coupons or success payments — funded not by donors but by
            credit sales (ITMOs, CRUs, VCUs, plastic credits) with corporate offtakers.
          </p>
          <table className="data" aria-label="IBRD outcome bond family comparison">
            <thead>
              <tr>
                <th scope="col">Bond</th>
                <th scope="col" className="text-right">Size</th>
                <th scope="col" className="text-right">Tenor</th>
                <th scope="col" className="text-right">Min ret</th>
                <th scope="col" className="text-right">Max ret</th>
                <th scope="col">Outcome unit</th>
                <th scope="col">Offtake partner</th>
                <th scope="col">Structure</th>
              </tr>
            </thead>
            <tbody>
              {data.outcomeBondFamily.map((b) => (
                <tr
                  key={b.key}
                  className={b.key === 'rhino' ? 'rhino-row' : undefined}
                  style={b.key === 'rhino' ? { background: 'rgba(138,47,43,0.05)' } : undefined}
                >
                  <td className="py-2 pr-4">
                    {b.url ? (
                      <a href={b.url} target="_blank" rel="noreferrer" className="link font-medium">
                        {b.name}
                      </a>
                    ) : (
                      <span className="font-medium">{b.name}</span>
                    )}
                    <div className="text-xs" style={{ color: 'var(--faint)' }}>{b.country} · {b.theme}</div>
                  </td>
                  <td className="num text-right">${fmtNum(b.sizeUsd / 1e6, 0)}m</td>
                  <td className="num text-right">{fmtNum(b.tenorYears, 1)}y</td>
                  <td className="num text-right">{fmtPct(b.guaranteedReturn)}</td>
                  <td className="num text-right">{fmtPct(b.maxTotalReturn)}</td>
                  <td className="text-xs">{b.outcomeUnit}</td>
                  <td className="text-xs">{b.outcomePayer}</td>
                  <td className="text-xs">
                    {b.structure}
                    {!b.principalProtected && (
                      <span
                        className="ml-1 font-semibold"
                        style={{ color: 'var(--ser)' }}
                        title="50% of principal was conditional on donation receipts"
                      >
                        ⚠ principal at risk
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="tick-note mt-2">
            Min ret = guaranteed floor (fixed coupon or issue discount); Max ret = official
            maximum potential return from the World Bank Q&amp;A documents. The Rhino Bond's
            range spans the GEF success tiers; the UNICEF note's principal (50%) was
            conditional on donation receipts — the only capital-at-risk structure in the family.
          </p>
        </div>
      )}

      <p className="text-xs max-w-3xl" style={{ color: 'var(--faint)' }}>
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
    <div
      className="p-3.5"
      style={{
        border: '1px solid var(--line)',
        borderLeft: '3px solid var(--line-strong)',
        background: 'rgba(42,58,72,0.02)',
      }}
    >
      <div className="rule-label">{label}</div>
      <div className="num font-semibold text-lg mt-1 tracking-tight">{value}</div>
      <div className="text-xs mt-0.5" style={{ color: 'var(--faint)' }}>{note}</div>
    </div>
  )
}

function Row({ label, value, strong }) {
  return (
    <div className="flex justify-between items-baseline py-1.5" style={{ borderBottom: '1px solid var(--line)' }}>
      <span style={{ color: 'var(--muted)' }}>{label}</span>
      <span
        className="num"
        style={strong ? { color: 'var(--teal)', fontWeight: 600 } : undefined}
      >
        {value}
      </span>
    </div>
  )
}
