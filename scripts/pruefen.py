#!/usr/bin/env python3
"""Prüft Texte und gebaute Seiten der Produktwebseite.

    python3 scripts/pruefen.py [Ordner]                 (Standard: _site, vorher bauen)
    python3 scripts/pruefen.py [Ordner] --veroeffentlichen

Prüft:
- jede Sprache hat dieselben Texte (gleiche Schlüssel und Listenlängen wie de.yaml),
- alle relativen Links und Bilder zeigen auf vorhandene Dateien, Sprungmarken gibt es,
- keine Dateien von fremden Servern (Stile, Skripte, Bilder, Schriften nur relativ),
- jedes Bild hat einen Alternativtext, jede Seite eine Sprache und einen Titel,
- keine Serveradressen, IP-Adressen, Mailadressen oder Namen echter Vereine.
Mit --veroeffentlichen zusätzlich: keine Platzhalter „[Angaben folgen]“ mehr.
"""

from __future__ import annotations

import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL / "scripts"))
from bauen import SPRACHEN, baue  # noqa: E402

# Kleingeschrieben; Treffer in Texten, Vorlagen, Stilen und gebauten Seiten sind Fehler.
# Namen echter Server und Vereine stehen nicht im Repo, sondern lokal, eine Zeile je Wort
# (Datei fehlt: nur die allgemeinen Muster):
#   ~/.config/hubiplan/produktseite-verboten   (oder HUBIPLAN_PRODUKTSEITE_VERBOTEN=…)
VERBOTEN = ["localhost", "/opt/"]
_LOKAL = Path(os.environ.get("HUBIPLAN_PRODUKTSEITE_VERBOTEN", Path.home() / ".config/hubiplan/produktseite-verboten"))
if _LOKAL.is_file():
    for _zeile in _LOKAL.read_text(encoding="utf-8").splitlines():
        if _zeile.strip() and not _zeile.startswith("#"):
            VERBOTEN.append(_zeile.strip().lower())
IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
MAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Erfundene Adressen und die Kontaktadresse aus dem Impressum
MAIL_ERLAUBT = re.compile(r"(?:@(?:[\w-]+\.)*example\.(?:org|com|net)|^kontakt@philipsen-edv\.de)$")
PLATZHALTER = "[Angaben folgen]"
# Einzige erlaubte Nennung eines echten Vereins: die Widmung (Ralf 03.11.2026), nur wörtlich so
WIDMUNG = "Hubertus-Schützenverein Neuss-Grimlinghausen von 1920"


def struktur(wert, pfad="") -> set[str]:
    """Schlüsselpfade eines YAML-Baums, Listen mit Länge."""
    if isinstance(wert, dict):
        aus = set()
        for k, v in wert.items():
            aus |= {f"{pfad}.{k}"} | struktur(v, f"{pfad}.{k}")
        return aus
    if isinstance(wert, list):
        aus = {f"{pfad}[{len(wert)}]"}
        for i, v in enumerate(wert):
            aus |= struktur(v, f"{pfad}[{i}]")
        return aus
    return set()


class Leser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.verweise: list[tuple[str, str, str]] = []  # (Tag, Attribut, Wert)
        self.ids: set[str] = set()
        self.bilder_ohne_alt = 0
        self.lang = None
        self.titel = ""
        self._im_titel = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "title":
            self._im_titel = True
        if tag == "img" and a.get("alt") is None:
            self.bilder_ohne_alt += 1
        for attr in ("href", "src"):
            if a.get(attr):
                self.verweise.append((tag, attr, a[attr]))

    def handle_endtag(self, tag):
        if tag == "title":
            self._im_titel = False

    def handle_data(self, data):
        if self._im_titel:
            self.titel += data


def lies(datei: Path) -> Leser:
    leser = Leser()
    leser.feed(datei.read_text(encoding="utf-8"))
    return leser


def pruefe_texte(fehler: list[str]) -> None:
    basis = struktur(yaml.safe_load((WURZEL / "inhalt" / f"{SPRACHEN[0]}.yaml").read_text(encoding="utf-8")))
    for sprache in SPRACHEN[1:]:
        andere = struktur(yaml.safe_load((WURZEL / "inhalt" / f"{sprache}.yaml").read_text(encoding="utf-8")))
        for k in sorted(basis - andere):
            fehler.append(f"inhalt/{sprache}.yaml: fehlt {k}")
        for k in sorted(andere - basis):
            fehler.append(f"inhalt/{sprache}.yaml: zu viel {k} (nicht in {SPRACHEN[0]}.yaml)")


def pruefe_verbotenes(datei: Path, text: str, fehler: list[str], name: str) -> None:
    klein = text.replace(WIDMUNG, "").lower()
    for wort in VERBOTEN:
        if wort in klein:
            fehler.append(f"{name}: enthält „{wort}“")
    for ip in IP.findall(text):
        fehler.append(f"{name}: enthält IP-Adresse {ip}")
    for mail in MAIL.findall(text):
        if not MAIL_ERLAUBT.search(mail) and not mail.endswith((".png", ".svg", ".woff2")):
            fehler.append(f"{name}: enthält Mailadresse {mail}")


def pruefe_seiten(ordner: Path, fehler: list[str], veroeffentlichen: bool) -> int:
    seiten = sorted(ordner.rglob("*.html"))
    gelesen = {p: lies(p) for p in seiten}
    for datei, leser in gelesen.items():
        name = str(datei.relative_to(ordner))
        if not leser.lang:
            fehler.append(f"{name}: <html> ohne lang")
        if not leser.titel.strip():
            fehler.append(f"{name}: ohne Titel")
        if leser.bilder_ohne_alt:
            fehler.append(f"{name}: {leser.bilder_ohne_alt} Bild(er) ohne alt")
        text = datei.read_text(encoding="utf-8")
        if veroeffentlichen and PLATZHALTER in text:
            fehler.append(f"{name}: enthält noch „{PLATZHALTER}“")
        for tag, attr, wert in leser.verweise:
            teile = urlsplit(wert)
            if teile.scheme or wert.startswith("//"):
                if tag != "a":
                    fehler.append(f"{name}: lädt {wert} von einem fremden Server")
                elif teile.scheme not in ("https", "mailto"):
                    fehler.append(f"{name}: Link ohne https: {wert}")
                continue
            if datei.name == "404.html" or not teile.path and not teile.fragment:
                continue
            if teile.path.startswith("/"):
                fehler.append(f"{name}: Link ab Wurzel {wert} (bitte relativ)")
                continue
            ziel = (datei.parent / unquote(teile.path)).resolve() if teile.path else datei
            if ziel.is_dir():
                ziel = ziel / "index.html"
            if not ziel.is_file():
                fehler.append(f"{name}: {attr}={wert} zeigt ins Leere")
                continue
            if teile.fragment and ziel.suffix == ".html":
                ids = gelesen[ziel].ids if ziel in gelesen else lies(ziel).ids
                if teile.fragment not in ids:
                    fehler.append(f"{name}: Sprungmarke #{teile.fragment} fehlt in {ziel.relative_to(ordner)}")
    return len(seiten)


def main() -> int:
    argumente = [a for a in sys.argv[1:] if not a.startswith("--")]
    veroeffentlichen = "--veroeffentlichen" in sys.argv
    ordner = Path(argumente[0]) if argumente else WURZEL / "_site"
    if not argumente:
        baue(ordner)
    fehler: list[str] = []
    pruefe_texte(fehler)
    for teil in ("inhalt", "vorlagen", "statisch"):
        for datei in sorted((WURZEL / teil).rglob("*")):
            if datei.is_file() and datei.suffix in (".yaml", ".html", ".css", ".svg", ".js", ".txt", ".md"):
                pruefe_verbotenes(datei, datei.read_text(encoding="utf-8"), fehler, str(datei.relative_to(WURZEL)))
    anzahl = pruefe_seiten(ordner, fehler, veroeffentlichen)
    for datei in sorted(ordner.rglob("*.html")):
        pruefe_verbotenes(datei, datei.read_text(encoding="utf-8"), fehler, str(datei.relative_to(ordner)))
    if fehler:
        print("\n".join(fehler), file=sys.stderr)
        print(f"FEHLER: {len(fehler)} Befund(e).", file=sys.stderr)
        return 1
    print(f"Prüfung ok: {anzahl} Seiten, {len(SPRACHEN)} Sprachen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
