// Bildschirmfotos öffnen beim Anklicken größer in einem schließbaren Fenster.
// Ohne Skript (oder ohne <dialog>) bleibt es beim Link auf die Bilddatei.
(() => {
  const fenster = document.querySelector('dialog.bildansicht')
  if (!fenster || typeof fenster.showModal !== 'function') return
  const bild = fenster.querySelector('img')
  const text = fenster.querySelector('.bildansicht-text')

  document.addEventListener('click', (e) => {
    const link = e.target.closest('.rahmen a[href]')
    if (!link || e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0) return
    const klein = link.querySelector('img')
    if (!klein) return
    e.preventDefault()
    bild.src = link.href
    bild.alt = klein.alt
    const unterschrift = link.closest('figure')?.querySelector('figcaption')
    text.textContent = unterschrift ? unterschrift.textContent : klein.alt
    fenster.showModal()
  })
  fenster.querySelector('.bildansicht-zu').addEventListener('click', () => fenster.close())
  // Klick neben das Bild (auf den abgedunkelten Hintergrund) schließt ebenfalls
  fenster.addEventListener('click', (e) => { if (e.target === fenster) fenster.close() })
  fenster.addEventListener('close', () => bild.removeAttribute('src'))
})()
