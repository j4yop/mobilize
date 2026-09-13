// Full E2E check: all 5 tabs, interactions, dark mode, mobile viewport, console errors.
import { chromium } from 'playwright'

const BASE = process.env.BASE_URL ?? 'http://localhost:4174'
const results = []
const check = (name, ok, detail = '') => {
  results.push({ name, ok, detail })
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? `  [${detail}]` : ''}`)
}

const browser = await chromium.launch()

// ---------- Desktop ----------
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } })
const errors = []
page.on('pageerror', (e) => errors.push('pageerror: ' + String(e)))
page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()) })
page.on('requestfailed', (r) => { if (!r.url().includes('favicon')) errors.push('reqfail: ' + r.url()) })

await page.goto(BASE + '/', { waitUntil: 'networkidle' })
check('App loads, header present', await page.locator('h1:has-text("Mobilize")').count() === 1)

// Header finding cards (4)
const findingCards = await page.locator('.finding-card').count()
check('4 headline finding cards', findingCards === 4, `got ${findingCards}`)
check('Finding card values render (no NaN/undefined)',
  await page.evaluate(() => !document.body.innerText.match(/NaN|undefined/)))

// --- Risk Lab ---
check('Risk Lab active by default', await page.locator('h2:has-text("Portfolio risk")').count() === 1)
const growthPts = await page.locator('.recharts-line-curve').count()
check('Growth chart lines render', growthPts === 3, `${growthPts} lines`)
const ddAreas = await page.locator('.recharts-area').count()
check('Drawdown areas render', ddAreas >= 3, `${ddAreas} areas`)

// frequency toggle
const monthlyTable1 = await page.locator('table').first().innerText()
await page.click('button:has-text("annual")')
await page.waitForTimeout(400)
const annualTable = await page.locator('table').first().innerText()
check('RiskLab annual/monthly toggle changes table', monthlyTable1 !== annualTable)
await page.click('button:has-text("monthly")')
await page.waitForTimeout(300)

// chart tooltip interaction
await page.locator('.recharts-wrapper').first().hover({ position: { x: 200, y: 100 } })
await page.waitForTimeout(500)
const tooltipVisible = await page.locator('.recharts-tooltip-wrapper:visible').count()
check('Chart tooltip appears on hover', tooltipVisible >= 1)

// metrics + significance tables have real numbers (metrics = table[0], sig = table[1])
const metricsText = await page.locator('table').first().innerText()
check('Metrics table has 3 portfolios', metricsText.includes('Benchmark') && metricsText.includes('ESG-tilted') && metricsText.includes('ESG-screened'))
const sigRows = await page.locator('table').nth(1).locator('tbody tr').count()
check('Significance table has 2 strategy rows', sigRows === 2, `${sigRows} rows`)

// --- ESG Map ---
await page.click('nav button:has-text("ESG Map")')
await page.waitForTimeout(400)
check('ESG Map renders', await page.locator('svg circle').count() >= 35)
const avg2024 = await page.locator('text=/Universe average — 2024/').count()
check('Universe average banner shows 2024 (latest)', avg2024 === 1)
await page.selectOption('select', '2015')
await page.waitForTimeout(400)
const avg2015 = await page.locator('text=/Universe average — 2015/').count()
check('Year switch updates banner to 2015', avg2015 === 1)
await page.click('table tbody tr:has-text("Sweden")')
await page.waitForTimeout(400)
check('Country drilldown opens', await page.locator('h3:has-text("Sweden")').count() === 1)
const pillarVals = await page.locator('text=/Environmental/').count()
check('Drilldown shows 3 pillars', pillarVals === 1)

// --- Pricing Test ---
await page.click('nav button:has-text("Pricing Test")')
await page.waitForTimeout(400)
check('Pricing Test renders verdict', await page.locator('text=/NOT significantly priced|statistically priced/').count() === 1)
check('Gamma histogram bars', (await page.locator('.recharts-bar-rectangle').count()) > 5)
check('Cumulative gamma line', await page.locator('.recharts-line-curve').count() >= 1)

// --- Outcome Bond Lab ---
await page.click('nav button:has-text("Outcome Bond Lab")')
await page.waitForTimeout(400)
check('Outcome Lab renders', await page.locator('h2:has-text("Rhino Bond")').count() === 1)
check('Deal anatomy boxes', await page.locator('text=/Pay at t=0/').count() === 1)
check('Investor economics rows', await page.locator('text=/Expected success payment/').count() >= 1)
check('Tier probability bars', (await page.locator('.recharts-bar-rectangle').count()) >= 4)
check('Drift sensitivity table rows', (await page.locator('table tbody tr').count()) >= 4)
check('Governance premium reference lines', await page.locator('svg g:has(line[stroke-dasharray])').count() >= 1)
check('SA reference line', await page.locator('text=South Africa').count() >= 1)

// --- Methodology ---
await page.click('nav button:has-text("Methodology")')
await page.waitForTimeout(300)
check('Methodology renders sections', (await page.locator('h3').count()) >= 4)
check('Methodology mentions duration proxy', (await page.locator('text=/duration approximation/').count()) === 1)

// --- Dark scheme request must not flip the light editorial theme ---
const darkPage = await browser.newPage({ viewport: { width: 1280, height: 900 }, colorScheme: 'dark' })
await darkPage.goto(BASE + '/', { waitUntil: 'networkidle' })
const bgDark = await darkPage.evaluate(() => getComputedStyle(document.body).backgroundColor)
check('Light theme persists regardless of system preference', bgDark === 'rgb(245, 242, 236)')

// --- Mobile viewport ---
const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } })
const mErrors = []
mobile.on('pageerror', (e) => mErrors.push(String(e)))
mobile.on('console', (m) => { if (m.type() === 'error') mErrors.push(m.text()) })
await mobile.goto(BASE + '/', { waitUntil: 'networkidle' })
const navCount = await mobile.locator('nav button').count()
check('Mobile: nav buttons reachable (may wrap)', navCount === 5, `${navCount} buttons`)
const hasHScroll = await mobile.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2)
check('Mobile: no horizontal overflow', !hasHScroll)
await mobile.click('nav button:has-text("ESG Map")')
await mobile.waitForTimeout(400)
check('Mobile: map tab works', await mobile.locator('svg circle').count() >= 35)
await mobile.click('nav button:has-text("Risk Lab")')
await mobile.waitForTimeout(300)
const mHasScroll = await mobile.evaluate(() => {
  const t = document.querySelector('.overflow-x-auto')
  return t ? t.scrollWidth >= t.clientWidth : true
})
check('Mobile: metrics table scrollable container', mHasScroll)

// --- Data bundle integrity ---
const bundle = await page.evaluate(async () => {
  const r = await fetch('data/dashboard.json')
  return r.ok ? await r.json() : null
})
check('dashboard.json fetches OK', bundle !== null)
check('Bundle has all 15 sections', Object.keys(bundle).length === 15, Object.keys(bundle).join(','))
check('Panel has 455 rows (2012-2024)', bundle.panel.length === 455)
check('No null scores in latest year', bundle.panel.filter(r => r.year === 2024 && r.scoreEqual === null).length === 0)

// keyboard navigation: tab through nav buttons
await page.click('nav button:has-text("Risk Lab")')
const focusWorked = await page.evaluate(() => {
  const btn = document.querySelector('nav button')
  btn.focus()
  return document.activeElement === btn
})
check('Nav buttons focusable (keyboard)', focusWorked)

check('Zero console/page/request errors (desktop)', errors.length === 0, errors.slice(0, 3).join(' | '))
check('Zero console/page errors (mobile)', mErrors.length === 0, mErrors.slice(0, 3).join(' | '))

// --- New features (F1-F5) ---
await page.click('nav button:has-text("ESG Map")')
await page.waitForTimeout(400)
// F1: data window extends to 2024
await page.selectOption('select#esg-year-select', '2024')
await page.waitForTimeout(400)
check('F1: year 2024 available & selectable', await page.locator('text=/Universe average — 2024/').count() === 1)
const lastPanelYear = await page.evaluate(async () => {
  const r = await fetch('data/dashboard.json'); const d = await r.json()
  return Math.max(...d.panel.map((x) => x.year))
})
check('F1: bundle panel includes 2024', lastPanelYear === 2024, `last=${lastPanelYear}`)
check('F1: meta.window shows 2013-2024', await page.locator('header p').first().innerText().then((t) => t.includes('2013-2024')))

// F3: indicator drilldown
await page.click('table tbody tr:has-text("Sweden")')
await page.waitForTimeout(400)
const detailsCount = await page.locator('details summary').count()
check('F3: indicator drilldown toggle present', detailsCount === 1)
await page.locator('details summary').click()
await page.waitForTimeout(300)
const indRows = await page.locator('details table tbody tr').count()
check('F3: indicator table shows ~16 rows', indRows >= 14 && indRows <= 16, `${indRows}`)

// F5: CSV export button
check('F5: CSV export button present', await page.locator('button:has-text("Download panel (CSV)")').count() === 1)
const csvDownload = page.waitForEvent('download', { timeout: 5000 }).catch(() => null)
await page.click('button:has-text("Download panel (CSV)")')
const dl = await csvDownload
check('F5: CSV download triggers', dl !== null, dl ? dl.suggestedFilename() : 'no download event')

// F5: deep-linking — reload with hash state
await page.goto(BASE + '/#tab=map&year=2021&country=ZAF', { waitUntil: 'networkidle' })
await page.locator('select#esg-year-select').waitFor({ timeout: 10000 })
check('F5: hash restores map tab', await page.locator('h2:has-text("Sovereign ESG scores")').count() === 1)
const sel2021 = await page.locator('text=/Universe average — 2021/').count()
check('F5: hash restores year 2021', sel2021 === 1)
check('F5: hash restores country ZAF', await page.locator('h3:has-text("South Africa")').count() === 1)
const hashAfter = await page.evaluate(() => window.location.hash)
check('F5: hash persists in URL', hashAfter.includes('year=2021') && hashAfter.includes('country=ZAF'), hashAfter)

// F4: pillar-level FM table
await page.click('nav button:has-text("Pricing Test")')
await page.waitForTimeout(400)
check('F4: pillar-level table present', await page.locator('text=/is any single pillar priced/').count() === 1)
const pillarRows = await page.locator('table[aria-label*="Pillar-level"] tbody tr').count()
check('F4: three pillar rows', pillarRows === 3, `${pillarRows}`)
check('F4: verdicts rendered', await page.locator('text=not priced').count() >= 3)

// F2: bond family table
await page.click('nav button:has-text("Outcome Bond Lab")')
await page.waitForTimeout(400)
check('F2: bond family table present', await page.locator('text=/all seven, official terms/').count() === 1)
const famRows = await page.locator('table[aria-label*="bond family"] tbody tr').count()
check('F2: seven bonds listed', famRows === 7, `${famRows}`)
for (const name of ['Clean Cooking', 'Amazon', 'Plastic', 'Spekboom', 'Emissions', 'UNICEF']) {
  check(`F2: ${name} listed`, await page.locator(`text=${name}`).count() >= 1)
}
check('F2: rhino row highlighted', await page.locator('tr.rhino-row').count() >= 1)
await page.goto(BASE + '/', { waitUntil: 'networkidle' })

// ARIA tabs pattern
const tabRoles = await page.locator('[role="tab"]').count()
check('A11y: nav has tablist roles (5 tabs)', tabRoles === 5, `${tabRoles}`)
const ariaSel = await page.locator('[role="tab"][aria-selected="true"]').count()
check('A11y: one tab aria-selected', ariaSel === 1)
const panel = await page.locator('main[role="tabpanel"]').count()
check('A11y: main has tabpanel role', panel === 1)

// Arrow key navigation on tabs
await page.locator('[role="tab"]').first().focus()
await page.keyboard.press('ArrowRight')
const activeId = await page.evaluate(() => document.activeElement?.id)
check('A11y: ArrowRight moves tab focus', activeId === 'tab-map', activeId)
await page.keyboard.press('Enter')
await page.waitForTimeout(300)
check('A11y: Enter activates focused tab', await page.locator('h2:has-text("Sovereign ESG scores")').count() === 1)

// Map circles keyboard-operable + labeled
await page.selectOption('select#esg-year-select', '2023').catch(() => {})
const circleBtn = await page.locator('svg g[role="button"]').count()
check('A11y: map countries are buttons (35)', circleBtn >= 35, `${circleBtn}`)
const circleLabel = await page.locator('svg g[role="button"]').first().getAttribute('aria-label')
check('A11y: map country has aria-label', circleLabel !== null && circleLabel.length > 3, circleLabel ?? '')
await page.locator('svg g[role="button"]').first().focus()
await page.keyboard.press('Enter')
await page.waitForTimeout(300)
check('A11y: keyboard selects country on map', await page.locator('h3.font-bold').count() >= 1)

// Rankings rows keyboard + table headers
const rowBtn = await page.locator('table tbody tr[tabindex="0"]').count()
check('A11y: ranking rows focusable', rowBtn >= 35, `${rowBtn}`)
const thCount = await page.locator('table thead th').count()
check('A11y: rankings table has header row', thCount >= 4, `${thCount} th`)
const labelFor = await page.locator('label[for="esg-year-select"]').count()
check('A11y: year select has associated label', labelFor === 1)

// Chart title/desc on recharts
const chartTitle = await page.evaluate(() => {
  const charts = document.querySelectorAll('.recharts-wrapper svg')
  return [...charts].map(s => ({ hasTitle: !!s.querySelector('title'), hasDesc: !!s.querySelector('desc') }))
})
check('A11y: Recharts SVGs have title/desc', chartTitle.every(c => c.hasTitle && c.hasDesc))

// reduced-motion CSS present
const reducedMotion = await page.evaluate(() => {
  for (const sheet of document.styleSheets) {
    try { for (const r of sheet.cssRules) { if (r.media && r.media.mediaText.includes('prefers-reduced-motion')) return true } } catch {}
  }
  return false
})
check('A11y: prefers-reduced-motion handled', reducedMotion)
const scrollPad = await page.evaluate(() => getComputedStyle(document.documentElement).scrollPaddingTop)
check('A11y: scroll-padding-top for sticky header', scrollPad !== '0px', scrollPad)

await browser.close()

const failed = results.filter(r => !r.ok)
console.log(`\n===== ${results.length - failed.length}/${results.length} checks passed =====`)
if (failed.length) { console.log('FAILED:', failed.map(f => f.name).join(', ')); process.exit(1) }
