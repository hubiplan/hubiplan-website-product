// Bilderkarussell oben auf der Startseite. Ohne Skript lässt sich die Bildreihe seitlich
// wischen; mit Skript kommen Knöpfe, Punkte und ein ruhiger Bildwechsel dazu.
(() => {
  const TAKT = 6000
  for (const k of document.querySelectorAll('.karussell')) {
    const spur = k.querySelector('.karussell-spur')
    const bilder = [...spur.children]
    const punkte = [...k.querySelectorAll('.karussell-punkte a')]
    const pause = k.querySelector('.karussell-pause')
    const ruhig = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let laeuft = !ruhig
    let uhr = null
    let haltDa = false

    const aktuell = () => Math.round(spur.scrollLeft / Math.max(spur.clientWidth, 1))
    const zeige = (i) => {
      const n = (i + bilder.length) % bilder.length
      spur.scrollTo({ left: n * spur.clientWidth, behavior: ruhig ? 'auto' : 'smooth' })
    }
    const markiere = () => {
      const i = aktuell()
      punkte.forEach((p, j) => p.toggleAttribute('aria-current', i === j))
    }
    const plane = () => {
      clearInterval(uhr)
      uhr = laeuft && !haltDa ? setInterval(() => zeige(aktuell() + 1), TAKT) : null
    }
    const setzeLauf = (an) => {
      laeuft = an
      pause.textContent = an ? '❚❚' : '▶'
      pause.setAttribute('aria-label', an ? k.dataset.anhalten : k.dataset.abspielen)
      plane()
    }

    k.classList.add('mit-skript')
    for (const b of k.querySelectorAll('[data-schritt]')) {
      b.addEventListener('click', () => { setzeLauf(false); zeige(aktuell() + Number(b.dataset.schritt)) })
    }
    punkte.forEach((p, j) => p.addEventListener('click', (e) => { e.preventDefault(); setzeLauf(false); zeige(j) }))
    pause.addEventListener('click', () => setzeLauf(!laeuft))
    spur.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        e.preventDefault(); setzeLauf(false); zeige(aktuell() + (e.key === 'ArrowRight' ? 1 : -1))
      }
    })
    // Beim Darüberfahren oder mit dem Fokus im Karussell steht der Wechsel still
    k.addEventListener('mouseenter', () => { haltDa = true; plane() })
    k.addEventListener('mouseleave', () => { haltDa = false; plane() })
    k.addEventListener('focusin', () => { haltDa = true; plane() })
    k.addEventListener('focusout', () => { haltDa = false; plane() })
    let ende = null
    spur.addEventListener('scroll', () => { clearTimeout(ende); ende = setTimeout(markiere, 80) }, { passive: true })
    markiere()
    setzeLauf(laeuft)
  }
})()
