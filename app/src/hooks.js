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

export const PORTFOLIO_META = {
  benchmark: { label: 'Benchmark', color: '#2563eb', desc: 'GDP-weighted, full universe' },
  esg_screened: { label: 'ESG-screened', color: '#0d9488', desc: 'Drops bottom quintile by ESG score' },
  esg_tilted: { label: 'ESG-tilted', color: '#7c3aed', desc: 'GDP weight × (ESG score)²' },
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
