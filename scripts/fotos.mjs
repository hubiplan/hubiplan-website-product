// Bildschirmfotos der Produktwebseite (fotos.json) mit Playwright.
// Aufruf nur über scripts/fotos.sh (startet HUBIplan und die Vereinswebseite mit dem Demoverein).
//
//   HUBIPLAN_URL=… WEBSITE_URL=… DEMO_PASSWORD=… DEMO_DOMAIN=… OUT=/out node fotos.mjs [name …]
import { copyFileSync, mkdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { chromium } from 'playwright'

const hubiplan = process.env.HUBIPLAN_URL
const website = process.env.WEBSITE_URL
// Webseiten je Demoverein (fotos.json: "verein"); ohne Angabe der Schützenverein
const websites = { schuetzen: website, kapelle: process.env.KAPELLE_URL }
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
    const basis = websites[b.verein || 'schuetzen']
    if (!basis) throw new Error(`keine Webseite für Verein ${b.verein}`)
    await page.goto(`${basis}${b.seite}`)
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
      // Zwei Versuche: nach der Anmeldung kann die Oberfläche noch einmal neu laden
      for (let versuch = 1; versuch <= 2; versuch++) {
        try {
          await page.goto(`${hubiplan}/anmelden`)
          if (page.url().includes('/anmelden')) {
            await page.locator('input[autocomplete="username"]').fill(`${user}@${domain}`)
            await page.locator('input[autocomplete="current-password"]').fill(password)
            await page.locator('button[type="submit"]').first().click()
            await page.waitForURL((u) => !u.pathname.startsWith('/anmelden'))
          }
          await page.waitForLoadState('networkidle')
          // Sprache über die API des Browserkontexts setzen (gleiche Cookies, unabhängig von der Seite)
          const csrf = (await context.cookies()).find((c) => c.name === 'csrftoken')?.value ?? ''
          const r = await context.request.patch(`${hubiplan}/api/me/language/`, {
            headers: { 'X-CSRFToken': csrf, Referer: `${hubiplan}/` },
            data: { language },
          })
          if (r.status() !== 200) throw new Error(`Sprache ${language} nicht wählbar (HTTP ${r.status()})`)
          await page.goto(`${hubiplan}${b.seite}`)
          await ruhig(page)
          await page.screenshot({ path: join(out, language, `${b.name}.png`) })
          console.log(`ok   ${language}/${b.name}`)
          break
        } catch (e) {
          if (versuch === 2) {
            failed++
            console.error(`FEHLER ${language}/${b.name}: ${e.message}`)
          }
        }
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
