#!/usr/bin/env bash
# Bildschirmfotos der Produktwebseite neu erzeugen (fotos.json).
#
#   scripts/fotos.sh [Bildname …]
#
# Startet in Wegwerf-Containern PostgreSQL, Redis, das HUBIplan-Backend mit dem erfundenen
# Demoverein „Schützenverein Musterstadt“ (seed_demoverein) und dem zweiten Demoverein
# „Musikkapelle Musterdorf“ (seed_demokapelle), die Oberfläche und die Vereinswebseiten
# beider Vereine, fotografiert jede Stelle aus fotos.json mit Playwright auf Deutsch und
# Englisch und legt die Bilder unter statisch/fotos/<sprache>/ ab. Danach die Bilder ansehen
# (keine echten Namen, Adressen, Serveradressen) und einchecken.
#
# Nimmt den eingecheckten Stand der Klone (git archive HEAD):
#   HUBIPLAN_REPO  (Standard ~/hubiplan)          am besten auf dem Release-Tag
#   WEBSITE_REPO   (Standard ~/hubiplan-website)
#
# Braucht Docker. Läuft nur auf dem lokalen Entwicklungsrechner (nie auf einem Server) und belegt einen
# Testplatz (höchstens zwei gleichzeitig, je höchstens 8 Kerne; testplatz).
# Docker braucht nur dieses Skript; die fertige Seite läuft ohne.
set -euo pipefail

if [ -z "${TESTPLATZ:-}" ]; then
    command -v testplatz > /dev/null || { echo "Abbruch: testplatz fehlt (hubiplan/docs/testserver.md)." >&2; exit 2; }
    exec testplatz "$0" "$@"
fi

ROOT=$(cd "$(dirname "$0")/.." && pwd)
HUBIPLAN_REPO="${HUBIPLAN_REPO:-$HOME/hubiplan}"
WEBSITE_REPO="${WEBSITE_REPO:-$HOME/hubiplan-website}"
CPUS="--cpuset-cpus=$TESTPLATZ_CPUS"
PLAYWRIGHT_VERSION="${PLAYWRIGHT_VERSION:-1.55.0}"
PW_IMAGE="mcr.microsoft.com/playwright:v$PLAYWRIGHT_VERSION-noble"
PG_IMAGE=$(grep -m1 -oE 'image: postgres:[0-9][^ ]*' "$HUBIPLAN_REPO/docker-compose.server.yml" | cut -d' ' -f2)
REDIS_IMAGE=$(grep -m1 -oE 'image: redis:[0-9][^ ]*' "$HUBIPLAN_REPO/docker-compose.yml" | cut -d' ' -f2)
# Nur für diesen Lauf; die Demozugänge verschwinden mit den Containern
PASSWORD="Fotos-$(head -c 12 /dev/urandom | od -An -tx1 | tr -d ' \n')"
DEMO_DOMAIN="sv-musterstadt.test"
KAPELLE_DOMAIN="mk-musterdorf.test"

ID="hubiplan-fotos-$(date +%s)-$$"
if [ -d /mnt/e/tmp ]; then mkdir -p /mnt/e/tmp/hubiplan-produktseite; WORK=$(mktemp -d -p /mnt/e/tmp/hubiplan-produktseite)
else WORK=$(mktemp -d); fi
cleanup() {
    for c in pw kapelle site web backend redis db; do docker rm -f "$ID-$c" > /dev/null 2>&1 || true; done
    docker network rm "$ID" > /dev/null 2>&1 || true
    docker image rm "$ID-backend:bild" "$ID-site:bild" > /dev/null 2>&1 || true
    rm -rf "$WORK" 2> /dev/null || docker run --rm -v "$WORK:/w" node:24-alpine rm -rf /w/hubiplan
    rm -rf "$WORK"
}
trap cleanup EXIT

mkdir -p "$WORK/hubiplan" "$WORK/website"
git -C "$HUBIPLAN_REPO" archive HEAD | tar -x -C "$WORK/hubiplan"
git -C "$WEBSITE_REPO" archive HEAD | tar -x -C "$WORK/website"
echo "Fotos mit HUBIplan $(git -C "$HUBIPLAN_REPO" rev-parse --short HEAD) und Webseite $(git -C "$WEBSITE_REPO" rev-parse --short HEAD), $TEST_KERNE Kerne …"

docker build -q -t "$ID-backend:bild" "$WORK/hubiplan/backend" > /dev/null
docker build -q -t "$ID-site:bild" "$WORK/website" > /dev/null
docker network create "$ID" > /dev/null
docker run -d --name "$ID-db" --network "$ID" --network-alias db "$CPUS" --tmpfs /var/lib/postgresql \
    -e POSTGRES_USER=hubiplan -e POSTGRES_PASSWORD=hubiplan -e POSTGRES_DB=hubiplan "$PG_IMAGE" > /dev/null
docker run -d --name "$ID-redis" --network "$ID" --network-alias redis "$CPUS" "$REDIS_IMAGE" > /dev/null
until docker exec "$ID-db" pg_isready -U hubiplan > /dev/null 2>&1; do sleep 1; done

docker run -d --name "$ID-backend" --network "$ID" --network-alias backend "$CPUS" \
    -e DJANGO_DEBUG=true -e DJANGO_SECRET_KEY=nur-fuer-fotos \
    -e DJANGO_ALLOWED_HOSTS=localhost,backend,web \
    -e DJANGO_CSRF_TRUSTED_ORIGINS=http://web:5173 -e FRONTEND_URL=http://web:5173 \
    -e DATABASE_URL=postgres://hubiplan:hubiplan@db:5432/hubiplan -e DATABASE_APP_ROLE=hubiplan_app \
    -e REDIS_URL=redis://redis:6379/0 -e CACHE_URL=redis://redis:6379/1 \
    -e HUBIPLAN_LANGUAGES=de,en -e RUN_MIGRATIONS=1 -e MIGRATE_VERBOSITY=0 \
    "$ID-backend:bild" python manage.py runserver 0.0.0.0:8000 > /dev/null
until docker exec "$ID-backend" python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/public/languages/')" > /dev/null 2>&1; do
    docker inspect -f '{{.State.Running}}' "$ID-backend" | grep -q true || { docker logs "$ID-backend" | tail -30; exit 1; }
    sleep 2
done
docker exec "$ID-backend" python manage.py seed_demoverein --password "$PASSWORD" > /dev/null
# Zweiter Demoverein für Musikvereine (Webseite der „Musikkapelle Musterdorf“)
docker exec "$ID-backend" python manage.py seed_demokapelle --password "$PASSWORD" > /dev/null
# Webseiten der Demovereine öffentlich (nur in diesem Wegwerf-Stand)
docker exec -e DATABASE_APP_ROLE= "$ID-backend" python manage.py shell -c "
from website.models import Website
for name in ('Schützenverein Musterstadt', 'Musikkapelle Musterdorf'):
    Website.objects.filter(organization__name__startswith=name).update(state='public')
" > /dev/null
echo "Backend mit Demovereinen bereit"

docker run -d --name "$ID-web" --network "$ID" --network-alias web "$CPUS" \
    -v "$WORK/hubiplan/frontend:/app" -v hubiplan-npm-cache:/root/.npm -w /app \
    -e BACKEND_URL=http://backend:8000 -e __VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS=web \
    node:24-alpine sh -c "npm ci --no-audit --no-fund --loglevel=error > /dev/null && npx vite --host 0.0.0.0 --port 5173" > /dev/null
docker run -d --name "$ID-site" --network "$ID" --network-alias site "$CPUS" \
    -e DJANGO_SECRET_KEY=nur-fuer-fotos -e HUBIPLAN_API_URL=http://backend:8000 -e HUBIPLAN_PUBLIC_URL=http://backend:8000 \
    -e SITE_HOST_OVERRIDE="www.$DEMO_DOMAIN" -e CACHE_SECONDS=0 \
    "$ID-site:bild" > /dev/null
docker run -d --name "$ID-kapelle" --network "$ID" --network-alias kapelle "$CPUS" \
    -e DJANGO_SECRET_KEY=nur-fuer-fotos -e HUBIPLAN_API_URL=http://backend:8000 -e HUBIPLAN_PUBLIC_URL=http://backend:8000 \
    -e SITE_HOST_OVERRIDE="www.$KAPELLE_DOMAIN" -e CACHE_SECONDS=0 \
    "$ID-site:bild" > /dev/null
until docker run --rm --network "$ID" node:24-alpine sh -c "wget -q -O /dev/null http://web:5173/ && wget -q -O /dev/null http://site:8000/ && wget -q -O /dev/null http://kapelle:8000/" 2> /dev/null; do
    for c in web site kapelle; do
        docker inspect -f '{{.State.Running}}' "$ID-$c" | grep -q true || { docker logs "$ID-$c" | tail -30; exit 1; }
    done
    sleep 3
done
echo "Oberfläche und Vereinswebseite bereit"

mkdir -p "$ROOT/statisch/fotos" "$WORK/pw"
cp "$ROOT/scripts/fotos.mjs" "$ROOT/fotos.json" "$WORK/pw/"
docker run --rm --name "$ID-pw" --network "$ID" "$CPUS" --ipc=host \
    -v "$WORK/pw:/pw" -v "$ROOT/statisch/fotos:/out" \
    -e HUBIPLAN_URL=http://web:5173 -e WEBSITE_URL=http://site:8000 -e KAPELLE_URL=http://kapelle:8000 -e DEMO_PASSWORD="$PASSWORD" \
    -e DEMO_DOMAIN="$DEMO_DOMAIN" -e OUT=/out -e FOTOS_JSON=/pw/fotos.json -w /pw \
    --user "$(id -u):$(id -g)" -e HOME=/tmp -e npm_config_cache=/tmp/.npm \
    "$PW_IMAGE" sh -c "npm i --no-save --no-audit --no-fund --loglevel=error --prefix /pw playwright@$PLAYWRIGHT_VERSION > /dev/null && node fotos.mjs $*"
echo "Fertig: statisch/fotos/ (Bilder ansehen, dann einchecken)"
