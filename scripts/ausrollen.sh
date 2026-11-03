#!/usr/bin/env bash
# Rollt einen lokal getesteten Stand der Produktwebseite auf einen Webspace aus.
#
#   scripts/ausrollen.sh <ziel> [Git-Referenz]     per SSH (Standard: HEAD)
#   scripts/ausrollen.sh --zip [Git-Referenz]      nur ZIP bauen, zum Hochladen per FTP
#
# Ziele stehen nur auf dem eigenen Rechner, nie im Repository, in
#   ~/.config/hubiplan/produktseite-ziele
# eine Zeile je Ziel: <name> <benutzer@host>:<ordner> [<eigner-dateien> <eigner-ordner>]
#   live benutzer@host:/pfad/zum/webordner
#   live admin@host:/home/web/public_html web:web web:www-data
# Mit Eignern meldet sich das Skript als Verwaltungsbenutzer an und schreibt per sudo
# (wie DEPLOY_SUDO=1 der anderen Skripte): Dateien gehören dann <eigner-dateien>, Ordner
# <eigner-ordner>. Ohne Eigner schreibt der angemeldete Benutzer selbst.
# SSH-Programm über SSH=… (Standard ssh), z. B. das Windows-ssh.exe aus WSL heraus.
# Braucht auf dem Server nur tar (rsync, falls vorhanden); lokal kein rsync.
#
# Schutz: nur Stände, die scripts/test.sh als getestet vermerkt hat; keine Platzhalter
# („[Angaben folgen]“) mehr; nie ein Rückschritt (der neue Stand muss den live laufenden
# enthalten, laut Datei .fassung im Webordner).
set -euo pipefail

STATE="${HUBIPLAN_PRODUKTSEITE_TESTED_FILE:-$HOME/.local/state/hubiplan-website-product/tested-trees}"
ZIELE="${HUBIPLAN_PRODUKTSEITE_ZIELE:-$HOME/.config/hubiplan/produktseite-ziele}"
SSH="${SSH:-ssh}"

[ $# -ge 1 ] || { sed -n '2,6p' "$0" >&2; exit 2; }
ZIEL_NAME="$1"
REF="${2:-HEAD}"

COMMIT=$(git rev-parse --verify --quiet "$REF^{commit}") || { echo "Abbruch: $REF unbekannt." >&2; exit 2; }
SHA=$(git rev-parse --short "$COMMIT")
TREE=$(git rev-parse "$COMMIT^{tree}")
if ! grep -q "^$TREE " "$STATE" 2> /dev/null; then
    echo "Abbruch: $SHA ist nicht lokal getestet (scripts/test.sh $SHA)." >&2
    exit 1
fi

if [ -d /mnt/e/tmp ]; then mkdir -p /mnt/e/tmp/hubiplan-produktseite; WORK=$(mktemp -d -p /mnt/e/tmp/hubiplan-produktseite)
else WORK=$(mktemp -d); fi
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/quelle"
git archive --format=tar "$COMMIT" | tar -x -C "$WORK/quelle"

PY=python3
for v in "$HOME"/.cache/hubiplan-website-product/venv-*/bin/python; do [ -x "$v" ] && PY="$v"; done
"$PY" "$WORK/quelle/scripts/bauen.py" "$WORK/site"
"$PY" "$WORK/quelle/scripts/pruefen.py" "$WORK/site" --veroeffentlichen
echo "$COMMIT" > "$WORK/site/.fassung"

if [ "$ZIEL_NAME" = "--zip" ]; then
    ZIP="$PWD/hubiplan-produktseite-$SHA.zip"
    (cd "$WORK/site" && rm -f "$ZIP" && zip -qr "$ZIP" .)
    echo "ZIP gebaut: $ZIP (Inhalt in den Webordner hochladen)."
    exit 0
fi

ZEILE=$(awk -v n="$ZIEL_NAME" '$1 == n { print $2, $3, $4 }' "$ZIELE" 2> /dev/null || true)
read -r ZIEL EIGNER_DATEIEN EIGNER_ORDNER <<< "$ZEILE"
[ -n "${ZIEL:-}" ] || { echo "Abbruch: Ziel „$ZIEL_NAME“ fehlt in $ZIELE." >&2; exit 2; }
HOST="${ZIEL%%:*}"
ORDNER="${ZIEL#*:}"
case "$ORDNER" in /*/*) ;; *) echo "Abbruch: Zielordner „$ORDNER“ ist kein absoluter Unterordner." >&2; exit 2 ;; esac
SUDO=""
if [ -n "${EIGNER_DATEIEN:-}" ]; then
    [ -n "${EIGNER_ORDNER:-}" ] || { echo "Abbruch: Eigner der Ordner fehlt in $ZIELE." >&2; exit 2; }
    SUDO="sudo "
fi

# stdin von ssh.exe immer umlenken, sonst wartet es auf die Tastatur
LIVE=$("$SSH" "$HOST" "${SUDO}cat '$ORDNER/.fassung' 2> /dev/null || true" < /dev/null | tr -d '\r')
if [ -n "$LIVE" ]; then
    git cat-file -e "$LIVE^{commit}" 2> /dev/null || git fetch --all --quiet || true
    if ! git merge-base --is-ancestor "$LIVE" "$COMMIT" 2> /dev/null; then
        echo "Abbruch: $SHA enthält den live laufenden Stand ${LIVE:0:7} nicht (Rückschritt)." >&2
        exit 1
    fi
fi

echo "Rolle $SHA nach $ZIEL_NAME aus …"
# Drei einfache SSH-Aufrufe ohne verschachtelte Anführungszeichen (Windows-ssh.exe reicht
# Befehle sonst unzuverlässig weiter): Zwischenordner anlegen, Seite als tar hochladen,
# auf dem Server per Skript über stdin entpacken, Eigner und Rechte setzen und den Inhalt
# des Webordners ersetzen (der Ordner selbst bleibt, mit seinen Eignern und Einstellungen).
T=$("$SSH" "$HOST" "mktemp -d" < /dev/null | tr -d '\r')
case "$T" in /tmp/*) ;; *) echo "Abbruch: Zwischenordner auf dem Server nicht angelegt." >&2; exit 1 ;; esac
tar -C "$WORK/site" -cf - . | "$SSH" "$HOST" "cat > $T/seite.tar"
if [ -n "$SUDO" ]; then
    EIGNER="chown -R $EIGNER_DATEIEN \"\$NEU\"
find \"\$NEU\" -mindepth 1 -type d -exec chown $EIGNER_ORDNER {} +"
else
    EIGNER=":"
fi
"$SSH" "$HOST" "${SUDO}bash -s" << SKRIPT
set -eu
T='$T'
ZIEL='$ORDNER'
NEU="\$T/neu"
trap 'rm -rf "\$T"' EXIT
test -d "\$ZIEL"
mkdir "\$NEU"
tar -x --no-same-owner -f "\$T/seite.tar" -C "\$NEU"
find "\$NEU" -type d -exec chmod 755 {} +
find "\$NEU" -type f -exec chmod 644 {} +
$EIGNER
# Der Webordner selbst behält Eigner und Rechte (rsync -pgo und cp -a übertragen sie sonst)
chown --reference="\$ZIEL" "\$NEU"
chmod --reference="\$ZIEL" "\$NEU"
if command -v rsync > /dev/null; then
    rsync -rlpgo --delete "\$NEU"/ "\$ZIEL"/
else
    find "\$ZIEL" -mindepth 1 -delete
    cp -a "\$NEU"/. "\$ZIEL"/
fi
echo "Webordner aktualisiert."
SKRIPT
echo "Fertig: $ZIEL_NAME zeigt $SHA."
