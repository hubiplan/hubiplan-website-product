# HUBIplan-Produktwebseite

**Die Webseite, die [HUBIplan](https://github.com/hubiplan/hubiplan) vorstellt: Funktionen,
Bildschirmfotos und Verweise auf die Repositories.**

> **English:** This repository holds the product website of HUBIplan, a free membership
> management system for clubs. It is a set of static pages (German and English) built with a
> small Python script; the result runs on any web server without Docker or server-side code.

Nicht zu verwechseln mit [hubiplan-website](https://github.com/hubiplan/hubiplan-website): Das
baut die Webseiten der Vereine aus deren HUBIplan-Daten. Diese Seite hier ist fest und liest
keine Daten aus HUBIplan.

Zu HUBIplan gehören vier Repositories:

| Repository | Inhalt |
| --- | --- |
| [hubiplan](https://github.com/hubiplan/hubiplan) | die Vereinsverwaltung: Backend, Oberfläche, Betrieb |
| [hubiplan-website](https://github.com/hubiplan/hubiplan-website) | öffentliche Vereinswebseiten aus den Daten von HUBIplan |
| [hubiplan-android](https://github.com/hubiplan/hubiplan-android) | Android-App für Mitglieder, Vorstand und Kasse |
| **hubiplan-website-product** (dieses) | Produktwebseite, die HUBIplan vorstellt |

## Seiten

Die Startseite stellt HUBIplan in Kacheln vor (Funktionen mit Bildschirmfotos, Android-App mit
Link zum Eintrag bei Google Play, eigene Instanz, häufige Fragen, Verweise auf die
Repositories). Dazu kommen Impressum, Datenschutzhinweise, die
Anleitung zum Löschen des App-Kontos und die Nutzungsbedingungen der App. Alle
Seiten gibt es auf Deutsch und Englisch; die Liste steht in `inhalt/seiten.yaml`.

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

Das Bild der Android-App (`baustein-android.png`, Terminliste, 1080 × 2400) entsteht von Hand
im Android-Emulator, weil die App nur HTTPS mit System-Zertifikaten zulässt:

1. Demoverein-Backend wie in `scripts/fotos.sh` starten (Wegwerf-Container, `seed_demoverein`),
   davor einen HTTPS-Proxy (z. B. Caddy) mit einem Wegwerf-Zertifikat für `10.0.2.2`, Port 8443.
2. Die Variante `foss` von `hubiplan-android` (main) als Debug bauen, mit einer nur lokal
   abgelegten `app/src/debug/res/xml/network_security_config.xml`, die zusätzlich der
   Wegwerf-CA vertraut (nie einchecken).
3. Emulator mit `-read-only` starten, App installieren, als `mitglied@sv-musterstadt.test`
   an `https://10.0.2.2:8443` anmelden, Statusleiste im Demo-Modus (9:30, voller Akku, keine
   Benachrichtigungen), Sprache mit `adb shell cmd locale set-app-locales de.hubiplan.app
   --locales de-DE` bzw. `en-US`, dann `adb exec-out screencap -p > baustein-android.png`.
4. Danach Emulator, Container, Zertifikat und Debug-Build wegwerfen.

## Ausrollen

Das Ergebnis ist ein Ordner mit fertigen Dateien. Er läuft auf jedem Webspace und Webserver
(Apache, nginx, Caddy, GitHub Pages …), ohne Docker, PHP oder Datenbank.

```bash
scripts/ausrollen.sh <ziel> [commit]   # per SSH und rsync; Ziele nur in ~/.config/hubiplan/produktseite-ziele
scripts/ausrollen.sh --zip [commit]    # ZIP zum Hochladen per FTP
```

Ausgerollt werden nur lokal getestete Stände ohne Platzhalter, nie ein Rückschritt.

## Mitwirken

Fehlermeldungen, Ideen und Pull Requests sind willkommen: [CONTRIBUTING.md](CONTRIBUTING.md).
Neue Texte immer in beiden Sprachen, Bildschirmfotos nur mit dem erfundenen Demoverein, keine
Inhalte von fremden Servern, keine Cookies.

## Sicherheit

Sicherheitslücken bitte **nicht** als öffentliches Issue melden, sondern vertraulich über
[GitHub](https://github.com/hubiplan/hubiplan-website-product/security/advisories/new).
Einzelheiten: [SECURITY.md](SECURITY.md).

## Lizenz

Copyright © 2026 Ralf Philipsen (Philipsen EDV)

Die Produktwebseite ist freie Software: Sie dürfen sie unter den Bedingungen der **GNU Affero
General Public License**, wie von der Free Software Foundation veröffentlicht, weitergeben
und/oder ändern, entweder gemäß Version 3 der Lizenz oder (nach Ihrer Wahl) jeder späteren
Version (`AGPL-3.0-or-later`), wie HUBIplan selbst.

Sie wird in der Hoffnung verbreitet, dass sie nützlich ist, aber **ohne jede Gewährleistung**,
sogar ohne die implizite Gewährleistung der Marktreife oder der Eignung für einen bestimmten
Zweck. Den vollständigen Lizenztext (englisch, maßgeblich) enthält die Datei
[LICENSE](LICENSE).

Die Schrift Outfit steht unter der SIL Open Font License 1.1
([statisch/schrift/OFL.txt](statisch/schrift/OFL.txt)).
