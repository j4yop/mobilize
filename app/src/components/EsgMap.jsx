import { useEffect, useMemo, useState } from 'react'
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

// Light mode needs darker fills for 3:1 non-text contrast on white cards;
// dark mode keeps the original lighter scale (passes on #111827).
function scoreColor(score, dark) {
  if (score === null || score === undefined) return '#d1d5db'
  const t = Math.max(0, Math.min(1, score / 100))
  const hue = t * 120 // 0 red -> 120 green
  return dark ? `hsl(${hue}, 65%, ${65 - t * 15}%)` : `hsl(${hue}, 70%, ${42 - t * 12}%)`
}

function useDarkMode() {
  const [dark] = useState(
    () => window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false
  )
  return dark
}

function deltaClass(d) {
  if (d === null || d === undefined || d === 0) return 'text-gray-600 dark:text-gray-300'
  return d > 0 ? 'text-emerald-700 dark:text-emerald-400' : 'text-red-700 dark:text-red-400'
}

function fmtDelta(d, digits = 1) {
  if (d === null || d === undefined) return '—'
  return `${d > 0 ? '+' : ''}${d.toFixed(digits)}`
}

function RankArrow({ change }) {
  if (change === null || change === undefined || change === 0) return null
  if (change > 0)
    return <span aria-label={`up ${change} places`}>↑</span>
  return <span aria-label={`down ${change} places`}>↓</span>
}

function exportPanelCsv(data) {
  const cols = ['iso3', 'country', 'year', 'scoreEqual', 'scorePca', 'pillarE', 'pillarS', 'pillarG']
  const lines = [cols.join(',')]
  for (const r of data.panel) {
    lines.push(
      cols
        .map((c) => {
          const v = r[c]
          if (v === null || v === undefined) return ''
          return typeof v === 'string' && v.includes(',') ? `"${v}"` : v
        })
        .join(',')
    )
  }
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `mobilize-esg-panel-${data.meta.window.replace(/\//g, '')}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

export default function EsgMap({ data, initialYear, initialCountry }) {
  const years = useMemo(() => {
    const ys = [...new Set(data.panel.map((r) => r.year))].sort()
    return ys
  }, [data])
  const [year, setYear] = useState(() =>
    initialYear && years.includes(initialYear) ? initialYear : Math.max(...years)
  )
  const [selected, setSelected] = useState(() =>
    initialCountry && data.panel.some((r) => r.iso3 === initialCountry) ? initialCountry : null
  )

  // Follow deep-link prop changes (e.g. hashchange navigation without a reload)
  useEffect(() => {
    if (initialYear !== undefined && years.includes(initialYear)) setYear(initialYear)
  }, [initialYear]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (initialCountry !== undefined) setSelected(initialCountry)
  }, [initialCountry]) // eslint-disable-line react-hooks/exhaustive-deps

  const dark = useDarkMode()
  const color = (score) => scoreColor(score, dark)

  // Deep-link write-back: keep the URL in sync with year/country selection
  useEffect(() => {
    const params = new URLSearchParams(window.location.hash.replace(/^#/, ''))
    const currentTab = params.get('tab') ?? 'risk'
    if (currentTab === 'map') {
      if (year !== Math.max(...years)) params.set('year', String(year))
      else params.delete('year')
      if (selected) params.set('country', selected)
      else params.delete('country')
      const hash = params.toString()
      window.history.replaceState(
        null,
        '',
        `${window.location.pathname}${window.location.search}${hash ? `#${hash}` : ''}`
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [year, selected])

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

  const select = (iso3) => setSelected(iso3 === selected ? null : iso3)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-lg font-bold">Sovereign ESG scores</h2>
          <p className="text-sm text-gray-500">
            World Bank Sovereign-ESG-style composite (equal-weight pillars). Click or focus + Enter a country for detail.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="esg-year-select" className="text-sm text-gray-500">Year</label>
          <select
            id="esg-year-select"
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
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="w-full"
          role="img"
          aria-label={`World map of sovereign ESG scores for ${year}. Scores also listed in the rankings table.`}
        >
          <title>ESG score map, {year}</title>
          {/* graticule */}
          {[0, 60, 120, 180, 240, 300].map((x) => (
            <line key={`v${x}`} x1={x} y1={0} x2={x} y2={H} stroke="#e5e7eb" strokeWidth={0.5} className="map-graticule" />
          ))}
          {[30, 60, 90, 120, 150].map((y) => (
            <line key={`h${y}`} x1={0} y1={y} x2={W} y2={H} stroke="#e5e7eb" strokeWidth={0.5} className="map-graticule" />
          ))}

          {Object.entries(POSITIONS).map(([iso3, { x, y }]) => {
            const r = byIso[iso3]
            if (!r) return null
            const { cx, cy } = project(x, y)
            const score = r.scoreEqual
            const radius = 8
            const isSel = selected === iso3
            return (
              <g
                key={iso3}
                role="button"
                tabIndex={0}
                aria-label={`${r.country}: ESG score ${fmtNum(score, 1)} of 100`}
                aria-pressed={isSel}
                onClick={() => select(iso3)}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(iso3) } }}
                className="cursor-pointer focus:outline-none"
              >
                <circle cx={cx} cy={cy} r={radius + 6} fill="transparent" />
                <circle
                  cx={cx}
                  cy={cy}
                  r={isSel ? radius + 3 : radius}
                  fill={color(score)}
                  fillOpacity={0.9}
                  stroke={isSel ? (dark ? '#f9fafb' : '#111827') : 'white'}
                  strokeWidth={isSel ? 2 : 1}
                  style={{ transition: 'fill 300ms' }}
                />
                <text x={cx + radius + 3} y={cy + 3} fontSize={9} fill={dark ? '#d1d5db' : '#4b5563'}>
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
            style={{ background: 'linear-gradient(to right, hsl(0,70%,42%), hsl(60,70%,38%), hsl(120,70%,30%))' }}
            aria-hidden="true"
          />
          <span>High ESG</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Rankings */}
        <div className="card overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold" id="rankings-heading">Rankings — {year}</h3>
            <button
              onClick={() => exportPanelCsv(data)}
              className="text-xs px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-300"
            >
              Download panel (CSV)
            </button>
          </div>
          <div className="max-h-96 overflow-y-auto">
            <table className="w-full text-sm" aria-labelledby="rankings-heading">
              <caption className="sr-only">
                Countries ranked by sovereign ESG score for {year}, with change versus {year - 1 || 'prior year'}.
              </caption>
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-200 dark:border-gray-700">
                  <th scope="col" className="py-1.5 pr-2 font-medium">Rank</th>
                  <th scope="col" className="py-1.5 pr-2 font-medium">Country</th>
                  <th scope="col" className="py-1.5 pr-2 font-medium text-right">Score</th>
                  <th scope="col" className="py-1.5 pr-2 font-medium text-right">Δ vs prior yr</th>
                  <th scope="col" className="py-1.5 w-20"><span className="sr-only">Score bar</span></th>
                </tr>
              </thead>
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
                      tabIndex={0}
                      role="button"
                      aria-label={`${r.country}, rank ${i + 1}, score ${fmtNum(r.scoreEqual, 1)}`}
                      aria-pressed={selected === r.iso3}
                      className="border-b border-gray-100 dark:border-gray-800 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 focus:bg-gray-100 dark:focus:bg-gray-800 focus:outline-none"
                      onClick={() => select(r.iso3)}
                      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(r.iso3) } }}
                    >
                      <td className="py-1.5 pr-2 text-gray-500 w-12 whitespace-nowrap">
                        {i + 1} <RankArrow change={rankChg} />
                      </td>
                      <td className="py-1.5 pr-2">{r.country}</td>
                      <td className="py-1.5 pr-2 text-right font-mono">{fmtNum(r.scoreEqual, 1)}</td>
                      <td className={`py-1.5 pr-2 text-right font-mono text-xs ${deltaClass(delta)}`}>
                        {fmtDelta(delta)}
                      </td>
                      <td className="w-20">
                        <div className="h-2 rounded" style={{ width: `${r.scoreEqual}%`, background: color(r.scoreEqual) }} />
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
            <CountryDetail data={data} iso3={selected} row={byIso[selected]} color={color} />
          ) : (
            <p className="text-sm text-gray-500">Select a country on the map or in the rankings.</p>
          )}
        </div>
      </div>
    </div>
  )
}

function CountryDetail({ data, iso3, row, color }) {
  const hist = data.panel.filter((r) => r.iso3 === iso3 && r.scoreEqual !== null)
  const prev = data.panel.find((r) => r.iso3 === iso3 && r.year === row.year - 1)
  const delta =
    prev && prev.scoreEqual !== null && row.scoreEqual !== null
      ? row.scoreEqual - prev.scoreEqual
      : null
  const inTilt = (data.weights.esg_tilted?.[iso3] ?? 0) * 100
  const inBench = (data.weights.benchmark?.[iso3] ?? 0) * 100
  const indicatorMeta = data.meta?.indicatorMeta ?? {}
  const indicators = row.indicators ?? {}
  const indicatorRows = Object.entries(indicators)
    .map(([code, value]) => {
      const meta = indicatorMeta[code] ?? {}
      return { code, value, name: meta.name ?? code, pillar: meta.pillar ?? '' }
    })
    .sort((a, b) => a.pillar.localeCompare(b.pillar) || a.name.localeCompare(b.name))

  return (
    <div>
      <h3 className="font-bold text-lg">{row.country}</h3>
      <p className="text-xs text-gray-500 mb-3">
        {iso3} · score {fmtNum(row.scoreEqual, 1)}/100 ({row.year})
        {delta !== null && (
          <span className={`ml-1 ${deltaClass(delta)}`}>
            ({fmtDelta(delta)} vs {row.year - 1})
          </span>
        )}
      </p>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <Pillar label="Environmental" value={row.pillarE} color={color} />
        <Pillar label="Social" value={row.pillarS} color={color} />
        <Pillar label="Governance" value={row.pillarG} color={color} />
      </div>

      {indicatorRows.length > 0 && (
        <details className="mb-4">
          <summary className="text-sm text-blue-700 dark:text-blue-300 cursor-pointer select-none">
            Show the {indicatorRows.length} indicators behind this score
          </summary>
          <table className="w-full text-xs mt-2" aria-label={`Indicator values for ${row.country}, ${row.year}`}>
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-200 dark:border-gray-700">
                <th scope="col" className="py-1 pr-2 font-medium">Indicator</th>
                <th scope="col" className="py-1 pr-2 font-medium">Pillar</th>
                <th scope="col" className="py-1 font-medium text-right">Normalized (0–1)</th>
              </tr>
            </thead>
            <tbody>
              {indicatorRows.map((ind) => (
                <tr key={ind.code} className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-1 pr-2">{ind.name}</td>
                  <td className="py-1 pr-2 text-gray-500">{ind.pillar}</td>
                  <td className="py-1 text-right font-mono">
                    {ind.value === null ? '—' : ind.value.toFixed(3)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-[10px] text-gray-500 mt-1">
            Direction-adjusted, min-max normalized per year. Missing = not published for this year.
          </p>
        </details>
      )}

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
        <ScoreHistory hist={hist} selectedYear={row.year} />
      </div>
    </div>
  )
}

function ScoreHistory({ hist, selectedYear }) {
  const label = 'Score history ' + hist.map((h) => h.year + ': ' + fmtNum(h.scoreEqual, 1)).join(', ')
  return (
    <div className="flex items-end gap-1 h-24" role="img" aria-label={label}>
      {hist.map((h) => (
        <div key={h.year} className="flex-1 flex flex-col items-center gap-0.5">
          <div
            className={`w-full rounded-t ${h.year === selectedYear ? 'bg-blue-600' : 'bg-blue-200 dark:bg-blue-900'}`}
            style={{ height: Math.max(h.scoreEqual, 2) + '%' }}
            title={h.year + ': ' + fmtNum(h.scoreEqual, 1)}
          />
          <span
            className={
              'text-[9px] ' +
              (h.year === selectedYear
                ? 'text-blue-700 dark:text-blue-300 font-bold'
                : 'text-gray-500')
            }
          >
            {String(h.year).slice(2)}
          </span>
        </div>
      ))}
    </div>
  )
}

function Pillar({ label, value, color }) {
  return (
    <div>
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-lg font-bold font-mono">{value === null ? '—' : fmtNum(value, 0)}</div>
      <div className="h-1.5 rounded mt-1" style={{ width: '100%', background: color(value) }} />
    </div>
  )
}
