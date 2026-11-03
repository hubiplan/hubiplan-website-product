#!/usr/bin/env bash
# Testet einen Commit lokal (WSL oder Git Bash), bevor er ausgerollt wird.
#
#   scripts/test.sh [Git-Referenz]
#
# Nimmt nur, was eingecheckt ist (git archive), baut die Seite in einer eigenen
# Python-Umgebung und prüft sie (ruff, scripts/pruefen.py). Kein Docker nötig.
# Nach Erfolg wird der Stand (Git-Tree) als getestet vermerkt; scripts/ausrollen.sh rollt
# nur solche Stände aus.
#
# Regeln wie in hubiplan: Tests laufen nie auf einem Server. Höchstens zwei Testläufe
# gleichzeitig (alle Projekte), jeder höchstens 8 Kerne: das Skript holt sich einen Platz
# mit testplatz (aus hubiplan/scripts/testplatz.sh, in WSL nach ~/.local/bin installiert).
set -euo pipefail

STATE="${HUBIPLAN_PRODUKTSEITE_TESTED_FILE:-$HOME/.local/state/hubiplan-website-product/tested-trees}"

if [ -z "${TESTPLATZ:-}" ]; then
    if ! command -v testplatz > /dev/null; then
        echo "Abbruch: testplatz fehlt (siehe hubiplan/docs/testserver.md, „Testplätze“)." >&2
        exit 2
    fi
    exec testplatz --kerne 1 "$0" "$@"
fi

REF="${1:-HEAD}"
COMMIT=$(git rev-parse --verify --quiet "$REF^{commit}" || true)
if [ -z "$COMMIT" ]; then
    git fetch --all --quiet || echo "Warnung: git fetch ist fehlgeschlagen." >&2
    COMMIT=$(git rev-parse --verify --quiet "$REF^{commit}" || true)
fi
[ -n "$COMMIT" ] || { echo "Abbruch: $REF ist nicht im Klon $(pwd)." >&2; exit 2; }
SHA=$(git rev-parse --short "$COMMIT")
TREE=$(git rev-parse "$COMMIT^{tree}")

# Temporäres auf E:, wenn vorhanden
if [ -d /mnt/e/tmp ]; then mkdir -p /mnt/e/tmp/hubiplan-produktseite; WORK=$(mktemp -d -p /mnt/e/tmp/hubiplan-produktseite)
else WORK=$(mktemp -d); fi
trap 'rm -rf "$WORK"' EXIT

echo "Teste $SHA ($(git log -1 --format=%s "$COMMIT")) lokal …"
mkdir -p "$WORK/quelle"
git archive --format=tar "$COMMIT" | tar -x -C "$WORK/quelle"

# Python-Umgebung je Stand der Abhängigkeiten, wird wiederverwendet
HASH=$(cat "$WORK/quelle/requirements.txt" "$WORK/quelle/requirements-dev.txt" | sha256sum | cut -c1-12)
VENV="$HOME/.cache/hubiplan-website-product/venv-$HASH"
if [ ! -x "$VENV/bin/python" ] && [ ! -x "$VENV/Scripts/python.exe" ]; then
    echo "Lege Python-Umgebung an ($VENV) …"
    python3 -m venv "$VENV"
    PY="$VENV/bin/python"; [ -x "$PY" ] || PY="$VENV/Scripts/python.exe"
    "$PY" -m pip install -q -r "$WORK/quelle/requirements-dev.txt"
fi
PY="$VENV/bin/python"; [ -x "$PY" ] || PY="$VENV/Scripts/python.exe"

cd "$WORK/quelle"
"$PY" -m ruff check .
"$PY" -m ruff format --check . > /dev/null
"$PY" scripts/bauen.py "$WORK/site"
"$PY" scripts/pruefen.py "$WORK/site"
cd - > /dev/null

mkdir -p "$(dirname "$STATE")"
echo "$TREE $SHA $(date -Iseconds)" >> "$STATE"
echo "Alles grün: $SHA ist als getestet vermerkt."
