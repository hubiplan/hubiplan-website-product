#!/usr/bin/env python3
"""Baut die Produktwebseite als Ordner mit fertigen Dateien.

    python3 scripts/bauen.py [Zielordner]      (Standard: _site)

Liest die Seitenliste aus inhalt/seiten.yaml, die Texte je Sprache aus inhalt/<sprache>.yaml
und inhalt/<sprache>/*.yaml (je Datei ein Teil, Dateiname = Schlüssel, z. B. bereiche.yaml → t.bereiche)
und die Vorlagen aus vorlagen/. Jede Seite wird zu <pfad>/index.html, alle Links sind relativ.
Das Ergebnis läuft auf jedem Webserver und jedem Webspace, ohne Programme auf dem Server.

Bildschirmfotos (statisch/fotos/<sprache>/<name>.png) gehen nicht als PNG hinaus: Das Skript
schneidet den in fotos.json genannten Ausschnitt aus (lesbar auch am Handy) und legt ihn sowie
das ganze Bild für die Bildansicht als WebP in passenden Breiten ab, mit Prüfsumme im Namen.
"""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
import shutil
import sys
from io import BytesIO
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markupsafe import Markup
from PIL import Image

WURZEL = Path(__file__).resolve().parent.parent
INHALT = WURZEL / "inhalt"
STATISCH = WURZEL / "statisch"

# Erste Sprache liegt im Wurzelordner, weitere unter /<sprache>/
SPRACHEN = ["de", "en"]

# Breiten der WebP-Dateien in Pixeln: Ausschnitt in der Seite, ganzes Bild in der Bildansicht
BREITEN_AUSSCHNITT = (560, 1120)
BREITEN_GANZ = (1600,)
BREITEN_HANDY = (420, 1080)
WEBP_QUALITAET = 80

# Inhaltsrichtlinie: nur eigene Dateien, nichts Eingebettetes. Steht als <meta> in jeder Seite und
# für Apache zusätzlich in der .htaccess (frame-ancestors wirkt nur als Kopfzeile).
RICHTLINIE = (
    "default-src 'none'; img-src 'self'; style-src 'self'; script-src 'self'; font-src 'self'; "
    "base-uri 'none'; form-action 'none'"
)

# Kopfzeilen für Apache-Webspaces (mod_headers). nginx, Caddy und andere: siehe README.
HTACCESS = f"""ErrorDocument 404 /404.html
<IfModule mod_headers.c>
Header always set Content-Security-Policy "{RICHTLINIE}; frame-ancestors 'none'"
Header always set X-Content-Type-Options "nosniff"
Header always set X-Frame-Options "DENY"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
Header always set Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
Header always set Strict-Transport-Security "max-age=31536000" "expr=%{{HTTPS}} == 'on'"
</IfModule>
"""


def lade_yaml(pfad: Path):
    with pfad.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def lade_texte(sprache: str) -> dict:
    """Texte einer Sprache: inhalt/<sprache>.yaml und je Datei in inhalt/<sprache>/ ein Teil."""
    texte = lade_yaml(INHALT / f"{sprache}.yaml")
    ordner = INHALT / sprache
    for datei in sorted(ordner.glob("*.yaml")) if ordner.is_dir() else []:
        if datei.stem in texte:
            raise SystemExit(f"inhalt/{sprache}/{datei.name}: Schlüssel {datei.stem} steht schon in {sprache}.yaml.")
        texte[datei.stem] = lade_yaml(datei)
    return texte


# Sortierschlüssel für deutsche Wörter (Umlaute wie Grundbuchstaben, ß wie ss)
_SORT = str.maketrans({"ä": "a", "ö": "o", "ü": "u", "ß": "ss", "Ä": "a", "Ö": "o", "Ü": "u"})


def alphabetisch(eintraege, schluessel: str = "titel") -> list:
    return sorted(eintraege, key=lambda e: e[schluessel].translate(_SORT).casefold())


def anfangsbuchstabe(wort: str) -> str:
    return wort[:1].translate(_SORT).upper()


def seiten_pfad(sprache: str, seite: str) -> str:
    """Ordner einer Seite relativ zur Wurzel, z. B. "", "funktionen/", "en/funktionen/"."""
    teile = [] if sprache == SPRACHEN[0] else [sprache]
    if seite:
        teile.append(seite)
    return "".join(t + "/" for t in teile)


def relativ(von_ordner: str, ziel: str) -> str:
    """Relativer Link vom Ordner einer Seite zu einem Ziel ab der Wurzel."""
    rel = posixpath.relpath("/" + ziel, "/" + von_ordner) if ziel else posixpath.relpath("/", "/" + von_ordner)
    if ziel.endswith("/") or ziel == "":
        rel = rel.rstrip("/") + "/"
    if rel.startswith("./"):
        rel = rel[2:]
    return rel or "./"


def md(text: str) -> Markup:
    """Kurzer Markdown-Text (Fett, Links, Code) ohne umschließenden Absatz."""
    html = markdown.markdown(text or "", extensions=["smarty"])
    if html.startswith("<p>") and html.endswith("</p>") and html.count("<p>") == 1:
        html = html[3:-4]
    return Markup(html)


_SEITENLINK = re.compile(r"\]\(@([a-z_]+)(#[\w-]+)?\)")


def seitenlinks(text: str, url) -> str:
    """Links auf eigene Seiten in Markdown-Texten: [Technik](@technik#betreiben) → relativer Link."""
    return _SEITENLINK.sub(lambda m: f"]({url(m.group(1))}{m.group(2) or ''})", text or "")


def webp(bild: Image.Image, breite: int, ziel: Path, stamm: str) -> tuple[str, int, int]:
    """Speichert das Bild in höchstens dieser Breite als WebP; Name mit Prüfsumme des Inhalts."""
    if bild.width > breite:
        bild = bild.resize((breite, round(bild.height * breite / bild.width)), Image.Resampling.LANCZOS)
    puffer = BytesIO()
    bild.save(puffer, "WEBP", quality=WEBP_QUALITAET, method=6)
    daten = puffer.getvalue()
    name = f"{stamm}-{bild.width}-{hashlib.sha256(daten).hexdigest()[:8]}.webp"
    (ziel / name).write_bytes(daten)
    return name, bild.width, bild.height


def baue_fotos(ziel: Path) -> dict[tuple[str, str], dict]:
    """WebP-Fassungen aller Bildschirmfotos; Schlüssel (Sprache, Name)."""
    angaben = {b["name"]: b for b in json.loads((WURZEL / "fotos.json").read_text(encoding="utf-8"))["bilder"]}
    fotos: dict[tuple[str, str], dict] = {}
    for sprache in SPRACHEN:
        ordner = STATISCH / "fotos" / sprache
        aus = ziel / "statisch" / "fotos" / sprache
        aus.mkdir(parents=True, exist_ok=True)
        for png in sorted(ordner.glob("*.png")):
            name = png.stem
            with Image.open(png) as roh:
                bild = roh.convert("RGB")
            eintrag = angaben.get(name, {})
            handy = name.endswith("-android")
            ausschnitt = eintrag.get("ausschnitt")
            if ausschnitt:
                # Angaben in Fensterpixeln (fotos.json breite/hoehe), Datei hat deviceScaleFactor 2
                faktor = bild.width / eintrag["breite"]
                x, y, b, h = (round(v * faktor) for v in ausschnitt)
                if x < 0 or y < 0 or x + b > bild.width or y + h > bild.height:
                    raise SystemExit(f"fotos.json: Ausschnitt von {name} reicht über das Bild hinaus.")
                teil = bild.crop((x, y, x + b, y + h))
            else:
                teil = bild
            fassungen = [webp(teil, w, aus, name) for w in (BREITEN_HANDY if handy else BREITEN_AUSSCHNITT)]
            # Handy-Bilder sind schon ganz, die größte Fassung dient zugleich der Bildansicht
            ganz = fassungen[-1] if handy else webp(bild, BREITEN_GANZ[-1], aus, name + "-ganz")
            klein = fassungen[0]
            fotos[(sprache, name)] = {
                "datei": f"statisch/fotos/{sprache}/{klein[0]}",
                "srcset": [(f"statisch/fotos/{sprache}/{f[0]}", f[1]) for f in fassungen],
                "breite": klein[1],
                "hoehe": klein[2],
                "ganz": f"statisch/fotos/{sprache}/{ganz[0]}",
            }
    return fotos


def baue(ziel: Path) -> list[Path]:
    seiten = lade_yaml(INHALT / "seiten.yaml")
    links = lade_yaml(INHALT / "links.yaml")
    env = Environment(
        loader=FileSystemLoader(WURZEL / "vorlagen"),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["md"] = md
    env.filters["alphabetisch"] = alphabetisch
    env.filters["seitenlinks"] = seitenlinks
    env.filters["anfangsbuchstabe"] = anfangsbuchstabe
    env.globals["richtlinie"] = RICHTLINIE

    if ziel.exists():
        shutil.rmtree(ziel)
    # Bildschirmfotos nicht als PNG kopieren, sondern als WebP bauen
    shutil.copytree(STATISCH, ziel / "statisch", ignore=shutil.ignore_patterns("*.png", ".gitkeep"))
    shutil.copytree(STATISCH / "bilder", ziel / "statisch" / "bilder", dirs_exist_ok=True)
    fotos = baue_fotos(ziel)
    geschrieben: list[Path] = []

    def links_fuer(sprache: str) -> dict[str, str]:
        return {k: v[sprache] if isinstance(v, dict) else v for k, v in links.items()}

    for sprache in SPRACHEN:
        texte = lade_texte(sprache)
        for seite in seiten:
            ordner = seiten_pfad(sprache, seite["pfad"])

            def url(name: str, sprache_ziel: str | None = None, _ordner=ordner, _sprache=sprache) -> str:
                eintrag = next(s for s in seiten if s["name"] == name)
                return relativ(_ordner, seiten_pfad(sprache_ziel or _sprache, eintrag["pfad"]))

            def datei(pfad: str, _ordner=ordner) -> str:
                link = relativ(_ordner, pfad)
                if pfad.endswith((".css", ".js")):
                    # Fassung im Link, damit Browser nach dem Ausrollen nicht die alte Datei behalten
                    link += "?v=" + hashlib.sha256((WURZEL / pfad).read_bytes()).hexdigest()[:10]
                return link

            def foto(name: str, _ordner=ordner, _sprache=sprache) -> dict | None:
                """Bildschirmfoto als WebP mit srcset, Maßen und ganzem Bild, sonst None (Platzhalter)."""
                f = fotos.get((_sprache, name))
                if not f:
                    return None
                return {
                    "src": relativ(_ordner, f["datei"]),
                    "srcset": ", ".join(f"{relativ(_ordner, p)} {w}w" for p, w in f["srcset"]),
                    "breite": f["breite"],
                    "hoehe": f["hoehe"],
                    "ganz": relativ(_ordner, f["ganz"]),
                }

            vorlage = env.get_template(seite["vorlage"])
            html = vorlage.render(
                t=texte,
                seite=seite,
                seiten=seiten,
                sprache=sprache,
                sprachen=SPRACHEN,
                url=url,
                datei=datei,
                links=links_fuer(sprache),
                foto=foto,
            )
            aus = ziel / ordner / "index.html"
            aus.parent.mkdir(parents=True, exist_ok=True)
            aus.write_text(html, encoding="utf-8")
            geschrieben.append(aus)

    # Fehlerseite für Webserver, die eine 404.html ausliefern, in allen Sprachen auf einer Seite.
    # Links ab Wurzel, weil sie unter jeder fehlenden Adresse erscheint.
    alle = {s: lade_texte(s) for s in SPRACHEN}

    def wurzel_url(name: str, sprache_ziel: str | None = None) -> str:
        eintrag = next(s for s in seiten if s["name"] == name)
        return "/" + seiten_pfad(sprache_ziel or SPRACHEN[0], eintrag["pfad"])

    def wurzel_datei(pfad: str) -> str:
        link = "/" + pfad
        if pfad.endswith((".css", ".js")):
            link += "?v=" + hashlib.sha256((WURZEL / pfad).read_bytes()).hexdigest()[:10]
        return link

    html = env.get_template("404.html").render(
        t=alle[SPRACHEN[0]],
        alle=alle,
        sprache=SPRACHEN[0],
        sprachen=SPRACHEN,
        links=links_fuer(SPRACHEN[0]),
        datei=wurzel_datei,
        url=wurzel_url,
    )
    (ziel / "404.html").write_text(html, encoding="utf-8")
    geschrieben.append(ziel / "404.html")
    # Apache-Webspaces: eigene Fehlerseite statt der des Hosters und Sicherheitskopfzeilen
    # (nginx und andere: siehe README)
    (ziel / ".htaccess").write_text(HTACCESS, encoding="utf-8")
    return geschrieben


def main() -> int:
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else WURZEL / "_site"
    dateien = baue(ziel.resolve())
    print(f"{len(dateien)} Seiten nach {ziel} gebaut.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
