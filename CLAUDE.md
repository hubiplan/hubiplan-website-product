# Hinweise für die Arbeit an hubiplan-website-product

Projektregeln (gelten wie im Hauptprojekt `hubiplan`):

- **Nie Tests auf einem Server ausführen.** Getestet wird auf dem lokalen Entwicklungsrechner
  mit `scripts/test.sh`, danach wird ausgerollt. `scripts/ausrollen.sh` rollt nur lokal getestete Stände aus.
- **Höchstens drei Testläufe gleichzeitig, jeder höchstens 8 Kerne**, projektübergreifend:
  `scripts/test.sh` holt sich einen Platz mit `testplatz`
  (aus `hubiplan/scripts/testplatz.sh`, siehe `hubiplan/docs/testserver.md`).
- Temporäre Dateien gehören in das lokal konfigurierte Arbeits- oder Tempverzeichnis.
- **Einfaches Hosting, überall ausrollbar, kein Docker:** nur statische Dateien,
  relative Links, nichts, was auf dem Server laufen muss.
- Keine Passwörter oder Geheimnisse ins Repo oder in Chats. Keine Serveradressen ins Repo;
  Ausrollziele nur in `~/.config/hubiplan/produktseite-ziele` auf dem lokalen Entwicklungsrechner.
- **Öffentliche Beiträge enthalten nur Projektinformationen:** keine internen Chat-Links,
  Gesprächsverläufe, Hostnamen, SSH-Zuordnungen, persönlichen Rechnerpfade oder
  kundenspezifischen Betriebs- und Freigabevermerke. Beispiele verwenden reservierte
  Beispieldomains und Demodaten.
- **Bildschirmfotos nur mit erfundenen Daten** (Demoverein „Schützenverein Musterstadt“ aus
  `seed_demoverein`), nie echte Vereine oder Personen; Pilotvereine nicht namentlich nennen.
  Einzige Ausnahme: die ausdrücklich freigegebene Widmung an den Hubertus-Schützenverein im Fuß
  (`WIDMUNG` in `scripts/pruefen.py`). Das veröffentlichte Betreiberimpressum bleibt erhalten.
- Keine Cookies, kein Tracking, keine Inhalte von fremden Servern (auch keine Google Fonts).
- **Jeder neue Text gleich auch auf Englisch** (`inhalt/de.yaml` und `inhalt/en.yaml`);
  `scripts/pruefen.py` schlägt sonst fehl.
- Links nie unterstreichen (auch nicht beim Darüberfahren); Links sind an Farbe und Schriftstärke erkennbar.
- **Jeder PR füllt „Für die Änderungshinweise“** der PR-Vorlage aus (Deutsch und Englisch).
- CI (GitHub Actions) gibt es nicht; keine automatischen Auslöser.
- Sprache in Doku und Commits: Deutsch.
