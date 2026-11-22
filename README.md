# HUBIplan-Produktwebseite

**Die Webseite, die [HUBIplan](https://github.com/hubiplan/hubiplan) vorstellt: Funktionen,
Bildschirmfotos und Verweise auf die Repositories.**

> **English:** This repository holds the product website of HUBIplan, a free membership
> management system for clubs. It is a set of static pages (German and English) built with a
> small Python script; the result runs on any web server without Docker or server-side code.

Nicht zu verwechseln mit [hubiplan-website](https://github.com/hubiplan/hubiplan-website): Das
baut die Webseiten der Vereine aus deren HUBIplan-Daten. Diese Seite hier ist fest und liest
keine Daten aus HUBIplan.

Zu HUBIplan gehören fünf Repositories:

| Repository | Inhalt |
| --- | --- |
| [hubiplan](https://github.com/hubiplan/hubiplan) | die Vereinsverwaltung: Backend, Oberfläche, Betrieb |
| [hubiplan-website](https://github.com/hubiplan/hubiplan-website) | öffentliche Vereinswebseiten aus den Daten von HUBIplan |
| [hubiplan-android](https://github.com/hubiplan/hubiplan-android) | Android-App für Mitglieder, Vorstand und Kasse |
| [hubiplan-ios](https://github.com/hubiplan/hubiplan-ios) | App für iPhone und iPad (im Aufbau) |
| **hubiplan-website-product** (dieses) | Produktwebseite, die HUBIplan vorstellt |

## Seiten

Die Startseite richtet sich zuerst an Vereinsvorstände und folgt ihren Fragen: Nutzen und
Bilder, Funktionen in vier Gruppen (je Kachel ein Satz, Einzelheiten aufklappbar), Vereine und
Verbände, Webseite und App, „So fangen Sie an“ (ohne Technikwörter), häufige Fragen, „Wer steckt
dahinter“ und Mitmachen. Alles für Technikkundige (Ausprobieren mit Docker, Selbst betreiben,
Repositories) steht auf der Seite `technik/`. Dazu kommen Impressum, Datenschutzhinweise, die
Anleitung zum Löschen des App-Kontos, die Nutzungsbedingungen der App, die Erklärung zur
Barrierefreiheit und eine zweisprachige Fehlerseite `404.html`. Am Handy bleibt die Startseite
kurz (Kacheln klappen über ihre Überschrift auf); beim Teilen zeigt sie eine Vorschau (Open
Graph, ohne Bild). Alle Seiten gibt es auf Deutsch und Englisch; die Liste steht in
`inhalt/seiten.yaml`.

Bei jedem Release von HUBIplan die Fassung unter `start.wer.fassung` in beiden Sprachen anpassen.

## Aufbau

| Ordner | Inhalt |
| --- | --- |
| `inhalt/` | Seitenliste (`seiten.yaml`), Texte je Sprache (`de.yaml`, `en.yaml`), feste Links (`links.yaml`, auch je Sprache) |
| `vorlagen/` | Jinja2-Vorlagen der Seiten |
| `statisch/` | Stil, Logo, Schrift Outfit (OFL), Bildschirmfotos unter `fotos/<sprache>/` |
| `scripts/` | Bauen, Prüfen, Testen, Ausrollen |
| `inhalt/openapi.json` | Kopie der API-Beschreibung aus `hubiplan/backend/partnerapi/openapi.json` für die Seite `technik/api/` |

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

Bildschirmfotos zeigen nur erfundene Demovereine aus HUBIplan („Schützenverein Musterstadt“,
„Musikkapelle Musterdorf“, künftig weitere Vereinsarten). Welche Seiten fotografiert werden,
steht in `fotos.json`. Neu erzeugen (Linux/WSL mit Docker, Klone von
`hubiplan` und `hubiplan-website` daneben, am besten auf dem Release-Stand):

```bash
scripts/fotos.sh                     # alle Bilder; oder: scripts/fotos.sh mitglieder
```

Das Skript startet HUBIplan, Oberfläche und Vereinswebseite in Wegwerf-Containern, legt den
Demoverein an und speichert die Bilder unter `statisch/fotos/<sprache>/<name>.png`. Bilder vor
dem Einchecken ansehen. Fehlt ein Bild, zeigt die Seite einen Platzhalter. Docker braucht nur
dieses Skript, nicht die fertige Seite.

Die PNG-Dateien gehen nicht hinaus: `scripts/bauen.py` macht daraus WebP-Dateien (mit Pillow,
Prüfsumme im Dateinamen). Die Seite zeigt den Ausschnitt `ausschnitt: [x, y, Breite, Höhe]` aus
`fotos.json` (in Fensterpixeln), in der Regel den ganzen Inhaltsbereich ohne Seitenleiste
(Seitenverhältnis 10:7), in 560 und 1120 Pixel Breite; die Bildansicht öffnet das ganze Bild
(1600 Pixel). Neue Ausschnitte nach dem Bauen bei 390 Pixel Breite ansehen.

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


## API-Seite

Die Seite `technik/api/` zeigt die API für andere Programme zur Information, gebaut aus
`inhalt/openapi.json`. Ändert sich die API in `hubiplan`, die Datei von dort übernehmen:

```bash
cp ../hubiplan/backend/partnerapi/openapi.json inhalt/openapi.json
```

Maßgeblich bleibt die Beschreibung jeder Instanz unter `/api/partner/v1/docs/`.

## Ausrollen

Das Ergebnis ist ein Ordner mit fertigen Dateien. Er läuft auf jedem Webspace und Webserver
(Apache, nginx, Caddy, GitHub Pages …), ohne Docker, PHP oder Datenbank.

```bash
scripts/ausrollen.sh <ziel> [commit]   # per SSH und rsync; Ziele nur in ~/.config/hubiplan/produktseite-ziele
scripts/ausrollen.sh --zip [commit]    # ZIP zum Hochladen per FTP
```

Ausgerollt werden nur lokal getestete Stände ohne Platzhalter, nie ein Rückschritt.

Fehlerseite: Der Bau legt `404.html` (Deutsch und Englisch) und für Apache eine `.htaccess` mit
`ErrorDocument 404 /404.html` in den Webordner. Webspaces mit eigener Fehlerseite neben dem
Webordner (z. B. HestiaCP mit nginx: `<domain>/document_errors/404.html`) bekommen sie mit
`fehlerseite=<datei>` in der Zielzeile (siehe Kopf von `scripts/ausrollen.sh`).

Sicherheitskopfzeilen: Jede Seite trägt ihre Inhaltsrichtlinie (Content-Security-Policy) selbst als
`<meta>`: nur eigene Dateien, keine eingebetteten Skripte oder Stile, keine Formulare
(`scripts/pruefen.py` prüft das). Was nur als Kopfzeile wirkt (Schutz gegen Einbetten in fremde
Seiten, `nosniff`, HTTPS erzwingen), setzt auf Apache die mitgelieferte `.htaccess` (braucht
`mod_headers`). Andere Webserver bekommen es in ihrer Konfiguration, für nginx zum Beispiel im
`server`-Block der Domain (bei HestiaCP in einer Datei `nginx.ssl.conf_<name>` im Konfigurationsordner
der Domain):

```nginx
add_header Content-Security-Policy "default-src 'none'; img-src 'self'; style-src 'self'; script-src 'self'; font-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=(), usb=()" always;
add_header Strict-Transport-Security "max-age=31536000" always;
```

Achtung bei nginx: Setzt ein `location`-Block selbst `add_header` (etwa für Cache-Zeiten), gelten
dort die Kopfzeilen des `server`-Blocks nicht mehr; sie müssen dann auch in diesen Block.

Zwischenspeicher: Stil, Skripte und Bildschirmfotos tragen eine Prüfsumme im Namen bzw. in der
Adresse. Für `statisch/` darf der Webserver deshalb lange Cache-Zeiten setzen (z. B. 30 Tage),
für die HTML-Seiten nicht.

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
