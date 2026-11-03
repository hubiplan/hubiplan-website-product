#!/usr/bin/env python3
"""Baut die Produktwebseite als Ordner mit fertigen Dateien.

    python3 scripts/bauen.py [Zielordner]      (Standard: _site)

Liest die Seitenliste aus inhalt/seiten.yaml, die Texte je Sprache aus inhalt/<sprache>.yaml
und die Vorlagen aus vorlagen/. Jede Seite wird zu <pfad>/index.html, alle Links sind relativ.
Das Ergebnis läuft auf jedem Webserver und jedem Webspace, ohne Programme auf dem Server.
"""

from __future__ import annotations

import posixpath
import shutil
import sys
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markupsafe import Markup

WURZEL = Path(__file__).resolve().parent.parent
INHALT = WURZEL / "inhalt"
STATISCH = WURZEL / "statisch"

# Erste Sprache liegt im Wurzelordner, weitere unter /<sprache>/
SPRACHEN = ["de", "en"]


def lade_yaml(pfad: Path):
    with pfad.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


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

    if ziel.exists():
        shutil.rmtree(ziel)
    shutil.copytree(STATISCH, ziel / "statisch")
    geschrieben: list[Path] = []

    for sprache in SPRACHEN:
        texte = lade_yaml(INHALT / f"{sprache}.yaml")
        for seite in seiten:
            ordner = seiten_pfad(sprache, seite["pfad"])

            def url(name: str, sprache_ziel: str | None = None, _ordner=ordner, _sprache=sprache) -> str:
                eintrag = next(s for s in seiten if s["name"] == name)
                return relativ(_ordner, seiten_pfad(sprache_ziel or _sprache, eintrag["pfad"]))

            def datei(pfad: str, _ordner=ordner) -> str:
                return relativ(_ordner, pfad)

            def foto(name: str, _ordner=ordner, _sprache=sprache) -> str | None:
                """Bildschirmfoto statisch/fotos/<sprache>/<name>.png, sonst None (Platzhalter)."""
                pfad = f"statisch/fotos/{_sprache}/{name}.png"
                return relativ(_ordner, pfad) if (WURZEL / pfad).is_file() else None

            vorlage = env.get_template(seite["vorlage"])
            html = vorlage.render(
                t=texte,
                seite=seite,
                seiten=seiten,
                sprache=sprache,
                sprachen=SPRACHEN,
                url=url,
                datei=datei,
                links=links,
                foto=foto,
            )
            aus = ziel / ordner / "index.html"
            aus.parent.mkdir(parents=True, exist_ok=True)
            aus.write_text(html, encoding="utf-8")
            geschrieben.append(aus)

    # Fehlerseite für Webserver, die eine 404.html im Wurzelordner ausliefern (Links ab Wurzel)
    texte = lade_yaml(INHALT / f"{SPRACHEN[0]}.yaml")
    html = env.get_template("404.html").render(
        t=texte,
        sprache=SPRACHEN[0],
        links=links,
        datei=lambda p: "/" + p,
        url=lambda n, s=None: "/" if n == "start" else f"/{n}/",
    )
    (ziel / "404.html").write_text(html, encoding="utf-8")
    geschrieben.append(ziel / "404.html")
    return geschrieben


def main() -> int:
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else WURZEL / "_site"
    dateien = baue(ziel.resolve())
    print(f"{len(dateien)} Seiten nach {ziel} gebaut.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
