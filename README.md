# HUBIplan-Produktwebseite

**Die Webseite, die [HUBIplan](https://github.com/hubiplan/hubiplan) vorstellt: Funktionen,
Bildschirmfotos und Verweise auf die Repositories.**

> **English:** This repository holds the product website of HUBIplan, a free membership
> management system for clubs. It is a set of static pages (German and English) built with a
> small Python script; the result runs on any web server without Docker or server-side code.

Nicht zu verwechseln mit [hubiplan-website](https://github.com/hubiplan/hubiplan-website): Das
baut die Webseiten der Vereine aus deren HUBIplan-Daten. Diese Seite hier ist fest und liest
keine Daten aus HUBIplan.

## Aufbau

| Ordner | Inhalt |
| --- | --- |
| `inhalt/` | Seitenliste (`seiten.yaml`), Texte je Sprache (`de.yaml`, `en.yaml`), feste Links (`links.yaml`) |
| `vorlagen/` | Jinja2-Vorlagen der Seiten |
| `statisch/` | Stil, Logo, Schrift Outfit (OFL), Bildschirmfotos unter `fotos/<sprache>/` |
| `scripts/` | Bauen, Prüfen, Testen, Ausrollen |

Deutsch liegt im Wurzelordner, Englisch unter `en/`. Jede Seite wird zu `<pfad>/index.html`,
alle Links sind relativ. Die Seite setzt keine Cookies und lädt nichts von fremden Servern.

## Bauen und ansehen

Voraussetzung: Python 3.11 oder neuer.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/bauen.py              # Ergebnis in _site/
python -m http.server -d _site 8000  # dann http://localhost:8000 öffnen
```

## Prüfen

```bash
python scripts/pruefen.py            # baut und prüft Links, Bilder, Sprachen, verbotene Inhalte
scripts/test.sh HEAD                 # vollständiger Test eines Commits, vermerkt ihn als getestet
```

Texte stehen immer in allen Sprachen: `pruefen.py` schlägt fehl, wenn `en.yaml` nicht
dieselben Schlüssel hat wie `de.yaml`.

## Bildschirmfotos

Bildschirmfotos zeigen nur den erfundenen Demoverein „Schützenverein Musterstadt“. Welche
Seiten fotografiert werden, steht in `fotos.json`. Neu erzeugen (Linux/WSL mit Docker, Klone von
`hubiplan` und `hubiplan-website` daneben, am besten auf dem Release-Stand):

```bash
scripts/fotos.sh                     # alle Bilder; oder: scripts/fotos.sh mitglieder
```

Das Skript startet HUBIplan, Oberfläche und Vereinswebseite in Wegwerf-Containern, legt den
Demoverein an und speichert die Bilder unter `statisch/fotos/<sprache>/<name>.png`. Bilder vor
dem Einchecken ansehen. Fehlt ein Bild, zeigt die Seite einen Platzhalter. Docker braucht nur
dieses Skript, nicht die fertige Seite.

## Ausrollen

Das Ergebnis ist ein Ordner mit fertigen Dateien. Er läuft auf jedem Webspace und Webserver
(Apache, nginx, Caddy, GitHub Pages …), ohne Docker, PHP oder Datenbank.

```bash
scripts/ausrollen.sh <ziel> [commit]   # per SSH und rsync; Ziele nur in ~/.config/hubiplan/produktseite-ziele
scripts/ausrollen.sh --zip [commit]    # ZIP zum Hochladen per FTP
```

Ausgerollt werden nur lokal getestete Stände ohne Platzhalter, nie ein Rückschritt.

## Mitwirken und Sicherheit

Siehe [CONTRIBUTING.md](CONTRIBUTING.md) und [SECURITY.md](SECURITY.md).

## Lizenz

Copyright © 2026 Ralf Philipsen (Philipsen EDV)

Dieses Programm ist freie Software unter der GNU Affero General Public License, Version 3
oder (nach Wahl) jeder späteren Version ([LICENSE](LICENSE)). Die Schrift Outfit steht unter
der SIL Open Font License 1.1 ([statisch/schrift/OFL.txt](statisch/schrift/OFL.txt)).
