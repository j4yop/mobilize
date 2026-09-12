import { useMemo, useState } from 'react'
import { fmtNum } from '../hooks.js'

// Country positions (approximate centroids) for the 35-country universe.
const POSITIONS = {
  USA: { x: -100, y: 40 }, CAN: { x: -106, y: 56 }, GBR: { x: -2, y: 54 },
  DEU: { x: 10, y: 51 }, FRA: { x: 2, y: 46 }, ITA: { x: 12, y: 42 },
  ESP: { x: -4, y: 40 }, NLD: { x: 5, y: 52 }, SWE: { x: 15, y: 62 },
  CHE: { x: 8, y: 47 }, JPN: { x: 138, y: 36 }, AUS: { x: 134, y: -25 },
  KOR: { x: 128, y: 36 }, CHN: { x: 104, y: 35 }, IND: { x: 78, y: 21 },
  IDN: { x: 113, y: -2 }, THA: { x: 101, y: 15 }, MYS: { x: 102, y: 4 },
  PHL: { x: 122, y: 12 }, VNM: { x: 106, y: 16 }, ZAF: { x: 24, y: -29 },
  EGY: { x: 30, y: 27 }, NGA: { x: 8, y: 10 }, KEN: { x: 38, y: 0 },
  MAR: { x: -6, y: 32 }, BRA: { x: -51, y: -10 }, MEX: { x: -102, y: 23 },
  CHL: { x: -71, y: -30 }, COL: { x: -73, y: 4 }, PER: { x: -75, y: -10 },
  ARG: { x: -64, y: -34 }, POL: { x: 19, y: 52 }, CZE: { x: 15, y: 50 },
  HUN: { x: 19, y: 47 }, TUR: { x: 35, y: 39 },
}

// Equirectangular projection to viewBox
const W = 720, H = 360
function project(x, y) {
  return { cx: ((x + 180) / 360) * W, cy: ((90 - y) / 180) * H }
}

function scoreColor(score) {
  // 0 -> deep red, 50 -> amber, 100 -> deep green
  if (score === null || score === undefined) return '#d1d5db'
  const t = Math.max(0, Math.min(1, score / 100))
  const hue = t * 120 // 0 red -> 120 green
  return `hsl(${hue}, 65%, ${65 - t * 15}%)`
}

function deltaClass(d) {
  if (d === null || d === undefined || d === 0) return 'text-gray-400'
  return d > 0 ? 'text-emerald-600' : 'text-red-600'
}

function fmtDelta(d, digits = 1) {
  if (d === null || d === undefined) return '—'
  return `${d > 0 ? '+' : ''}${d.toFixed(digits)}`
}

function RankArrow({ change }) {
  if (change === null || change === undefined || change === 0) return null
  if (change > 0)
    return <span className="text-emerald-600 text-[10px]" title={`Up ${change} from prior year`}>↑</span>
  return <span className="text-red-600 text-[10px]" title={`Down ${-change} from prior year`}>↓</span>
}

export default function EsgMap({ data }) {
  const years = useMemo(() => {
    const ys = [...new Set(data.panel.map((r) => r.year))].sort()
    return ys
  }, [data])
  const [year, setYear] = useState(Math.max(...years))
  const [selected, setSelected] = useState(null)

  const rows = useMemo(
    () => data.panel.filter((r) => r.year === year),
    [data, year]
  )
  const byIso = {}
  for (const r of rows) byIso[r.iso3] = r

  const prevByIso = useMemo(() => {
    const m = {}
    for (const r of data.panel) if (r.year === year - 1) m[r.iso3] = r
    return m
  }, [data, year])

  const ranked = [...rows]
    .filter((r) => r.scoreEqual !== null)
    .sort((a, b) => b.scoreEqual - a.scoreEqual)
  const rankByIso = {}
  ranked.forEach((r, i) => { rankByIso[r.iso3] = i + 1 })

  const prevRanked = Object.values(prevByIso)
    .filter((r) => r.scoreEqual !== null)
    .sort((a, b) => b.scoreEqual - a.scoreEqual)
  const prevRankByIso = {}
  prevRanked.forEach((r, i) => { prevRankByIso[r.iso3] = i + 1 })

  const scored = rows.filter((r) => r.scoreEqual !== null)
  const avg = scored.length
    ? scored.reduce((s, r) => s + r.scoreEqual, 0) / scored.length
    : null
  const prevScored = Object.values(prevByIso).filter((r) => r.scoreEqual !== null)
  const prevAvg = prevScored.length
    ? prevScored.reduce((s, r) => s + r.scoreEqual, 0) / prevScored.length
    : null
  const avgDelta = avg !== null && prevAvg !== null ? avg - prevAvg : null

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-lg font-bold">Sovereign ESG scores</h2>
          <p className="text-sm text-gray-500">
            World Bank Sovereign-ESG-style composite (equal-weight pillars). Click a country for detail.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-500">Year</label>
          <select
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-1.5 text-sm bg-white dark:bg-gray-900"
          >
            {years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between text-sm mb-2">
          <span className="text-gray-500">Universe average — {year}</span>
          <span className="font-mono">
            <span className="font-semibold">{fmtNum(avg, 1)}</span>
            {avgDelta !== null && (
              <span className={`ml-2 text-xs ${deltaClass(avgDelta)}`}>
                {fmtDelta(avgDelta)} vs {year - 1}
              </span>
            )}
          </span>
        </div>
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
          <text x={10} y={18} fontSize={11} fill="#6b7280" fontWeight="600">{year}</text>
          {/* graticule */}
          {[0, 60, 120, 180, 240, 300].map((x) => (
            <line key={`v${x}`} x1={x} y1={0} x2={x} y2={H} stroke="#e5e7eb" strokeWidth={0.5} />
          ))}
          {[30, 60, 90, 120, 150].map((y) => (
            <line key={`h${y}`} x1={0} y1={y} x2={W} y2={H} stroke="#e5e7eb" strokeWidth={0.5} />
          ))}

          {Object.entries(POSITIONS).map(([iso3, { x, y }]) => {
            const r = byIso[iso3]
            if (!r) return null
            const { cx, cy } = project(x, y)
            const score = r.scoreEqual
            const radius = 8
            const isSel = selected === iso3
            return (
              <g key={iso3} onClick={() => setSelected(iso3)} className="cursor-pointer">
                <circle
                  cx={cx}
                  cy={cy}
                  r={isSel ? radius + 3 : radius}
                  fill={scoreColor(score)}
                  fillOpacity={0.85}
                  stroke={isSel ? '#111827' : 'white'}
                  strokeWidth={isSel ? 2 : 1}
                  style={{ transition: 'fill 300ms' }}
                />
                <text x={cx + radius + 3} y={cy + 3} fontSize={9} fill="#6b7280">
                  {iso3}
                </text>
              </g>
            )
          })}
        </svg>
        {/* legend */}
        <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
          <span>Low ESG</span>
          <div
            className="h-2 w-40 rounded"
            style={{ background: 'linear-gradient(to right, hsl(0,65%,65%), hsl(60,65%,57%), hsl(120,65%,50%))' }}
          />
          <span>High ESG</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Rankings */}
        <div className="card overflow-hidden">
          <h3 className="font-semibold mb-2">Rankings — {year}</h3>
          <div className="max-h-96 overflow-y-auto">
            <table className="w-full text-sm">
              <tbody>
                {ranked.map((r, i) => {
                  const prev = prevByIso[r.iso3]
                  const delta =
                    prev && prev.scoreEqual !== null && r.scoreEqual !== null
                      ? r.scoreEqual - prev.scoreEqual
                      : null
                  const rankChg =
                    prevRankByIso[r.iso3] && rankByIso[r.iso3]
                      ? prevRankByIso[r.iso3] - rankByIso[r.iso3]
                      : null
                  return (
                    <tr
                      key={r.iso3}
                      className="border-b border-gray-100 dark:border-gray-800 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                      onClick={() => setSelected(r.iso3)}
                    >
                      <td className="py-1.5 pr-2 text-gray-400 w-12 whitespace-nowrap">
                        {i + 1} <RankArrow change={rankChg} />
                      </td>
                      <td className="py-1.5 pr-2">{r.country}</td>
                      <td className="py-1.5 pr-2 text-right font-mono">{fmtNum(r.scoreEqual, 1)}</td>
                      <td className={`py-1.5 pr-2 text-right font-mono text-xs ${deltaClass(delta)}`}>
                        {fmtDelta(delta)}
                      </td>
                      <td className="w-20">
                        <div className="h-2 rounded" style={{ width: `${r.scoreEqual}%`, background: scoreColor(r.scoreEqual) }} />
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Drilldown */}
        <div className="card">
          {selected && byIso[selected] ? (
            <CountryDetail data={data} iso3={selected} row={byIso[selected]} />
          ) : (
            <p className="text-sm text-gray-500">Select a country on the map or in the rankings.</p>
          )}
        </div>
      </div>
    </div>
  )
}

function CountryDetail({ data, iso3, row }) {
  const hist = data.panel.filter((r) => r.iso3 === iso3 && r.scoreEqual !== null)
  const prev = data.panel.find((r) => r.iso3 === iso3 && r.year === row.year - 1)
  const delta =
    prev && prev.scoreEqual !== null && row.scoreEqual !== null
      ? row.scoreEqual - prev.scoreEqual
      : null
  const inTilt = (data.weights.esg_tilted?.[iso3] ?? 0) * 100
  const inBench = (data.weights.benchmark?.[iso3] ?? 0) * 100

  return (
    <div>
      <h3 className="font-bold text-lg">{row.country}</h3>
      <p className="text-xs text-gray-400 mb-3">
        {iso3} · score {fmtNum(row.scoreEqual, 1)}/100 ({row.year})
        {delta !== null && (
          <span className={`ml-1 ${deltaClass(delta)}`}>
            ({fmtDelta(delta)} vs {row.year - 1})
          </span>
        )}
      </p>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <Pillar label="Environmental" value={row.pillarE} />
        <Pillar label="Social" value={row.pillarS} />
        <Pillar label="Governance" value={row.pillarG} />
      </div>

      <div className="text-sm space-y-1 mb-4">
        <div className="flex justify-between">
          <span className="text-gray-500">Benchmark weight ({data.meta.latestWeightsYear})</span>
          <span className="font-mono">{fmtNum(inBench, 2)}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">ESG-tilted weight</span>
          <span className="font-mono">{fmtNum(inTilt, 2)}%</span>
        </div>
      </div>

      <div>
        <div className="text-sm text-gray-500 mb-1">Score history (equal-weight vs PCA)</div>
        <div className="flex items-end gap-1 h-24">
          {hist.map((h) => (
            <div key={h.year} className="flex-1 flex flex-col items-center gap-0.5">
              <div
                className={`w-full rounded-t ${h.year === row.year ? 'bg-blue-600' : 'bg-blue-200 dark:bg-blue-900'}`}
                style={{ height: `${Math.max(h.scoreEqual, 2)}%` }}
                title={`${h.year}: ${fmtNum(h.scoreEqual, 1)}`}
              />
              <span className={`text-[9px] ${h.year === row.year ? 'text-blue-600 font-bold' : 'text-gray-400'}`}>
                {String(h.year).slice(2)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function Pillar({ label, value }) {
  return (
    <div>
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-lg font-bold font-mono">{value === null ? '—' : fmtNum(value, 0)}</div>
      <div className="h-1.5 rounded mt-1" style={{ width: '100%', background: scoreColor(value) }} />
    </div>
  )
}
