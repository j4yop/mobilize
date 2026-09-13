import { useEffect, useState } from 'react'

export function useDashboardData() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/dashboard.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(setData)
      .catch((e) => setError(e.message))
  }, [])

  return { data, error }
}

// Pencil-toned portfolio identity, matched to CSS variables
export const PORTFOLIO_META = {
  benchmark: { label: 'Benchmark', color: '#37536b', desc: 'GDP-weighted, full universe' },
  esg_screened: { label: 'ESG-screened', color: '#9a7b2e', desc: 'Drops bottom quintile by ESG score' },
  esg_tilted: { label: 'ESG-tilted', color: '#8a2f2b', desc: 'GDP weight × (ESG score)²' },
}

export const CHART = {
  grid: '#e6e1d6',
  axisTick: { fontSize: 11, fill: '#98a099' },
  axisLine: { stroke: '#d5cfc2' },
  tooltip: {
    contentStyle: {
      background: '#fdfcf9',
      border: '1px solid #d5cfc2',
      borderRadius: '2px',
      boxShadow: '0 1px 2px rgba(60,50,35,0.05), 0 12px 32px -18px rgba(60,50,35,0.25)',
      fontSize: '12px',
      padding: '8px 10px',
    },
    labelStyle: {
      color: '#6b7168',
      fontSize: '11px',
      letterSpacing: '0.02em',
    },
    cursor: { stroke: '#d5cfc2', strokeDasharray: '3 3' },
  },
}

export function fmtPct(x, digits = 2) {
  if (x === null || x === undefined || Number.isNaN(x)) return '—'
  return `${(x * 100).toFixed(digits)}%`
}

export function fmtPctRaw(x, digits = 2) {
  if (x === null || x === undefined || Number.isNaN(x)) return '—'
  return `${x.toFixed(digits)}%`
}

export function fmtNum(x, digits = 2) {
  if (x === null || x === undefined || Number.isNaN(x)) return '—'
  return x.toFixed(digits)
}
