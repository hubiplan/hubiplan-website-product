# Sicherheit

Die Produktwebseite von HUBIplan besteht nur aus statischen Seiten ohne Formulare, Cookies
oder Programme auf dem Server. Hinweise auf Sicherheitslücken nehmen wir trotzdem ernst und
sind für jede Meldung dankbar.

*Reports in English are welcome; see the [English summary](#english-summary) at the end.*

## Lücke melden

Bitte **kein öffentliches Issue**, sondern vertraulich über GitHub:
[Report a vulnerability](https://github.com/hubiplan/hubiplan-website-product/security/advisories/new)
(im Repository unter **Security › Report a vulnerability**).

Lücken in HUBIplan selbst bitte [dort melden](https://github.com/hubiplan/hubiplan/security/advisories/new).

## Was dann passiert

- Wir bestätigen den Eingang in der Regel innerhalb von 7 Tagen.
- Wir prüfen die Meldung, halten dich auf dem Laufenden und stimmen eine Korrektur mit dir ab.
- Bitte gib uns bis zur Korrektur, höchstens 90 Tage ab Meldung, Zeit, bevor du Einzelheiten
  veröffentlichst.

## Unterstützte Fassungen

Die Seite wird fortlaufend aus `main` gebaut; es gibt keine Release-Zweige. Korrekturen gibt es
für den aktuellen Stand von `main`.

## Umfang

Gemeint sind die Vorlagen, Texte und Skripte in diesem Repository, etwa eingeschleuste
Inhalte über Vorlagen oder ein Skript, das beim Ausrollen mehr als den Webordner verändert.
Besonders interessant sind auch Inhalte von fremden Servern, Cookies oder Skripte, die
Besucher verfolgen könnten, sowie Daten echter Personen in Bildschirmfotos.
Nicht gemeint sind Einstellungen des Webservers, auf dem eine Kopie der Seite liegt.

## Regeln fürs Prüfen

Prüfe nur gegen eine eigene, lokal gebaute Kopie (`python scripts/bauen.py`), keine
Überlastungsangriffe auf die veröffentlichte Seite. Wer sich daran hält und in gutem Glauben
handelt, hat von uns keine rechtlichen Schritte zu erwarten.

## English summary

Please do **not** open a public issue. Report vulnerabilities privately via
[GitHub private vulnerability reporting](https://github.com/hubiplan/hubiplan-website-product/security/advisories/new);
issues in HUBIplan itself belong in [HUBIplan](https://github.com/hubiplan/hubiplan/security/advisories/new).
We usually acknowledge reports within 7 days and ask you to keep details private until a fix
is available, for at most 90 days. Test only against a locally built copy. Good-faith
research that follows these rules will not face legal action from us. The German text above
is binding.
