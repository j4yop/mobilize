// E2E runner for the dashboard.
//
//   npm run test:e2e
//
// Builds the app, boots `vite preview` on a fixed port, runs the Playwright
// check suite (e2e_full_check.mjs) against it, then tears the server down.
// Exits non-zero when any check fails, so it is safe to call from a Makefile
// target or CI. No new dependencies: Playwright is already a dev dependency.
import { spawn } from 'node:child_process'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const PORT = Number(process.env.E2E_PORT ?? 4174)
const BASE = `http://localhost:${PORT}`
const STARTUP_TIMEOUT_MS = 30_000
const VITE = resolve(HERE, 'node_modules', '.bin', 'vite')

const run = (cmd, args, opts = {}) =>
  spawn(cmd, args, { cwd: HERE, stdio: 'inherit', ...opts })

const exitOf = (child) => new Promise((res) => child.on('exit', (code) => res(code ?? 1)))

const responds = async (url) => {
  try {
    await fetch(url, { redirect: 'manual' })
    return true
  } catch {
    return false
  }
}

// Returns 'up', 'exited:<code>', or 'timeout'. Watching the child as well as the
// port matters: if the server dies we must not keep polling a socket that some
// other process happens to be holding.
async function waitForServer(url, timeoutMs, server) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    if (await responds(url)) return 'up'
    if (server.exitCode !== null) return `exited:${server.exitCode}`
    await new Promise((r) => setTimeout(r, 250))
  }
  return 'timeout'
}

let exitCode = 1
let server = null

try {
  // Pre-flight: a server already bound to this port would silently serve a
  // stale build (vite preview caches its file list at startup), so the suite
  // would report results for code that is not ours. Refuse rather than lie.
  if (await responds(BASE)) {
    throw new Error(
      `port ${PORT} is already serving something — probably a leftover preview ` +
        `server from an earlier run. Kill it, or rerun with E2E_PORT=<free port>.`,
    )
  }

  console.log('[e2e] building static bundle…')
  const buildCode = await exitOf(run('npm', ['run', 'build']))
  if (buildCode !== 0) throw new Error(`build failed (exit ${buildCode})`)

  console.log(`[e2e] starting preview on ${BASE} …`)
  // Spawn vite directly so this runner owns the port (no npm flag parsing).
  server = run(VITE, ['preview', '--port', String(PORT), '--strictPort'])

  const state = await waitForServer(BASE, STARTUP_TIMEOUT_MS, server)
  if (state !== 'up') {
    throw new Error(
      state === 'timeout'
        ? `preview server did not respond at ${BASE} within ${STARTUP_TIMEOUT_MS}ms`
        : `preview server ${state} before it was ready`,
    )
  }

  console.log('[e2e] running checks…\n')
  exitCode = await exitOf(
    run(process.execPath, ['e2e_full_check.mjs'], {
      env: { ...process.env, BASE_URL: BASE },
    }),
  )
} catch (err) {
  console.error(`[e2e] ${err instanceof Error ? err.message : String(err)}`)
} finally {
  if (server && server.exitCode === null) {
    server.kill('SIGTERM')
    await new Promise((r) => setTimeout(r, 300))
  }
}

console.log(`[e2e] ${exitCode === 0 ? 'PASSED' : 'FAILED'}`)
process.exit(exitCode)
