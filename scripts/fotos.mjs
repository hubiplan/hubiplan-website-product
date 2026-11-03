// Bildschirmfotos der Produktwebseite (fotos.json) mit Playwright.
// Aufruf nur über scripts/fotos.sh (startet HUBIplan und die Vereinswebseite mit dem Demoverein).
//
//   HUBIPLAN_URL=… WEBSITE_URL=… DEMO_PASSWORD=… DEMO_DOMAIN=… OUT=/out node fotos.mjs [name …]
import { copyFileSync, mkdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { chromium } from 'playwright'

const hubiplan = process.env.HUBIPLAN_URL
const website = process.env.WEBSITE_URL
const password = process.env.DEMO_PASSWORD
const domain = process.env.DEMO_DOMAIN
const out = process.env.OUT
if (!hubiplan || !website || !password || !domain || !out) throw new Error('Umgebung unvollständig')
const spec = JSON.parse(readFileSync(process.env.FOTOS_JSON, 'utf8'))
const only = new Set(process.argv.slice(2))
const images = spec.bilder.filter((b) => !only.size || only.has(b.name))

const browser = await chromium.launch()
let failed = 0

async function ruhig(page) {
  await page.waitForLoadState('networkidle')
  await page
    .locator('[role="status"]', { hasText: /Lädt|Loading/ })
    .waitFor({ state: 'detached' })
    .catch(() => {})
  // Hinweise mit Datum veralten im Bild; Animationen anhalten
  await page.addStyleTag({
    content: 'main.content > .alert[role="status"] { display: none !important; } *, *::before, *::after { animation: none !important; transition: none !important; caret-color: transparent !important; }',
  })
  await page.waitForTimeout(400)
}

for (const language of ['de', 'en']) {
  mkdirSync(join(out, language), { recursive: true })
}

// Vereinswebseite: Inhalte des Vereins sind deutsch, ein Bild für beide Sprachen
for (const b of images.filter((i) => i.quelle === 'website')) {
  const context = await browser.newContext({ viewport: { width: b.breite, height: b.hoehe }, deviceScaleFactor: 2, reducedMotion: 'reduce' })
  const page = await context.newPage()
  try {
    await page.goto(`${website}${b.seite}`)
    await ruhig(page)
    const file = join(out, 'de', `${b.name}.png`)
    await page.screenshot({ path: file })
    copyFileSync(file, join(out, 'en', `${b.name}.png`))
    console.log(`ok   ${b.name}`)
  } catch (e) {
    failed++
    console.error(`FEHLER ${b.name}: ${e.message}`)
  }
  await context.close()
}

// HUBIplan: je Sprache und Zugang anmelden, Sprache am Konto setzen
for (const language of ['de', 'en']) {
  const byUser = Map.groupBy(images.filter((i) => i.quelle === 'hubiplan'), (b) => b.zugang)
  for (const [user, list] of byUser) {
    for (const b of list) {
      const context = await browser.newContext({
        viewport: { width: b.breite, height: b.hoehe },
        deviceScaleFactor: 2,
        colorScheme: 'light',
        reducedMotion: 'reduce',
        locale: language === 'en' ? 'en-GB' : 'de-DE',
      })
      const page = await context.newPage()
      try {
        await page.goto(`${hubiplan}/anmelden`)
        await page.locator('input[autocomplete="username"]').fill(`${user}@${domain}`)
        await page.locator('input[autocomplete="current-password"]').fill(password)
        await page.locator('button[type="submit"]').first().click()
        await page.waitForURL((u) => !u.pathname.startsWith('/anmelden'))
        const status = await page.evaluate(async (code) => {
          const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? ''
          const r = await fetch('/api/me/language/', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
            body: JSON.stringify({ language: code }),
          })
          return r.status
        }, language)
        if (status !== 200) throw new Error(`Sprache ${language} nicht wählbar (HTTP ${status})`)
        await page.goto(`${hubiplan}${b.seite}`)
        await ruhig(page)
        await page.screenshot({ path: join(out, language, `${b.name}.png`) })
        console.log(`ok   ${language}/${b.name}`)
      } catch (e) {
        failed++
        console.error(`FEHLER ${language}/${b.name}: ${e.message}`)
      }
      await context.close()
    }
  }
}
await browser.close()
if (failed) {
  console.error(`${failed} Bild(er) fehlgeschlagen`)
  process.exit(1)
}
