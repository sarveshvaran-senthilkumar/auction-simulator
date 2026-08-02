/**
 * Headless walk through the real mobile flow against a running backend.
 *
 *   uvicorn app.main:app --port 8000   # backend, in another terminal
 *   npm run build && node render_test.mjs
 *
 * Loads the production bundle in jsdom, proxies fetch/WebSocket to the live
 * server, and clicks: Home -> Create -> Lobby -> claim franchise -> Retention.
 *
 * Needs jsdom:  npm install --no-save jsdom
 */
import fs from 'fs'
import path from 'path'
import { JSDOM, VirtualConsole } from 'jsdom'

const API = 'http://127.0.0.1:8000'
const DIST = 'dist'

const errors = []
const vc = new VirtualConsole()
vc.on('jsdomError', (e) => errors.push('jsdomError: ' + (e.stack || e.message)))
vc.on('error', (...a) => errors.push('console.error: ' + a.join(' ')))

const html = fs.readFileSync(path.join(DIST, 'index.html'), 'utf8')
const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  url: 'http://localhost:5173/',
  pretendToBeVisual: true,
  virtualConsole: vc,
})
const { window } = dom
const { document } = window

window.matchMedia = () => ({
  matches: false, addListener() {}, removeListener() {},
  addEventListener() {}, removeEventListener() {},
})
window.navigator.vibrate = () => true
window.scrollTo = () => {}
Object.defineProperty(window.navigator, 'clipboard', { value: { writeText: async () => {} } })

// Relative URLs from the bundle go to the real API, the way the Vite proxy does.
window.fetch = async (url, init) => {
  const res = await fetch(String(url).startsWith('http') ? url : API + url, init)
  const text = await res.text()
  return { ok: res.ok, status: res.status, json: async () => JSON.parse(text) }
}

// The socket only needs to exist; retention data arrives over HTTP.
const sent = []
window.WebSocket = class {
  static OPEN = 1
  constructor(url) {
    this.url = url
    this.readyState = 1
    setTimeout(() => this.onopen?.(), 10)
  }
  send(data) { sent.push(JSON.parse(data)) }
  close() { this.readyState = 3 }
}

const script = html.match(/<script type="module"[^>]*src="([^"]+)"/)[1]
window.eval(fs.readFileSync(path.join(DIST, script.replace(/^\//, '')), 'utf8'))

const wait = (ms) => new Promise((r) => setTimeout(r, ms))
const root = () => document.getElementById('root')
const text = () => root().textContent ?? ''
const findByText = (needle, tag = 'button') =>
  [...document.querySelectorAll(tag)].find((el) => el.textContent?.includes(needle))

function click(el, label) {
  if (!el) throw new Error(`could not find: ${label}`)
  el.dispatchEvent(new window.MouseEvent('click', { bubbles: true }))
}

function typeInto(el, value) {
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set
  setter.call(el, value)
  el.dispatchEvent(new window.Event('input', { bubbles: true }))
}

const steps = []
function check(name, ok, detail = '') {
  steps.push({ name, ok })
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  — ' + detail : ''}`)
}

await wait(700)
check('home renders', text().includes('Mega Auction'))
check('health probe reached backend', text().includes('Server online'), text().slice(-30))

click(findByText('Create Auction'), 'Create Auction')
await wait(250)
typeInto(document.querySelector('input'), 'Headless')
await wait(120)
check('create form shows format picker', text().includes('Quick') && text().includes('Standard'))

click(findByText('Quick'), 'Quick format')
await wait(100)
click(findByText('Create Room'), 'Create Room')
await wait(1500)

check('lobby reached', /Choose your franchise/.test(text()), text().match(/[A-Z2-9]{6}/)?.[0] ?? '')
check('all ten franchises listed',
  ['CSK', 'MI', 'RCB', 'KKR', 'DC', 'RR', 'PBKS', 'SRH', 'LSG', 'GT'].every((c) => text().includes(c)))

click(findByText('Chennai Super Kings'), 'CSK card')
await wait(1300)
check('franchise claimed', text().includes('● You'))

click(findByText('Start as'), 'Start button')
await wait(2600)

check('retention screen reached',
  text().includes('Your 2024 squad') || text().includes('Retentions locked'),
  text().slice(0, 80))
check('retention slabs priced', /₹18 Cr/.test(text()) || /Slot 1/.test(text()))
check('2024 squad listed', /Ruturaj|Jadeja|Dhoni|Conway|Pathirana/.test(text()))

// Pick two players and confirm, exercising the slab maths and the socket call.
const rows = [...document.querySelectorAll('button')].filter((b) =>
  /worth ₹/.test(b.textContent ?? ''))
if (rows.length >= 2) {
  const purseBefore = text().match(/₹(\d+(?:\.\d+)?) Cr/)?.[1]
  click(rows[0], 'first retention')
  await wait(250)
  click(rows[1], 'second retention')
  await wait(350)
  const purseAfter = text().match(/₹(\d+(?:\.\d+)?) Cr/)?.[1]
  check('purse drops as players are retained',
    Number(purseAfter) < Number(purseBefore), `${purseBefore} -> ${purseAfter}`)

  click(findByText('Confirm 2 retention'), 'Confirm retentions')
  await wait(350)
  click(findByText('Lock it in'), 'Lock it in')
  await wait(450)
  const msg = sent.find((m) => m.type === 'RETENTION_CONFIRM')
  check('RETENTION_CONFIRM sent over socket',
    !!msg && msg.payload.player_ids.length === 2, JSON.stringify(msg?.payload ?? {}))
  check('locked screen shown', text().includes('Retentions locked'))
} else {
  check('retention rows found', false, `only ${rows.length} rows`)
}

console.log('\nruntime errors:', errors.length)
errors.slice(0, 5).forEach((e) => console.log('  ' + e.slice(0, 260)))

const failed = steps.filter((s) => !s.ok).length
console.log(`\n${steps.length - failed}/${steps.length} checks passed`)
process.exit(failed === 0 && errors.length === 0 ? 0 : 1)
