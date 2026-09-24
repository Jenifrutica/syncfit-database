#!/usr/bin/env bash
# Start PostgreSQL for SyncFit (works with or without the compose plugin).
set -e
if docker compose version >/dev/null 2>&1; then
  docker compose up -d
else
  docker rm -f syncfit-postgres >/dev/null 2>&1 || true
  docker run -d --name syncfit-postgres \
    -e POSTGRES_USER=syncfit -e POSTGRES_PASSWORD=syncfit -e POSTGRES_DB=syncfit \
    -p 5432:5432 -v syncfit_pgdata:/var/lib/postgresql/data postgres:16-alpine >/dev/null
fi
printf 'waiting for PostgreSQL'
until docker exec syncfit-postgres pg_isready -U syncfit >/dev/null 2>&1; do printf '.'; sleep 1; done
echo
echo "PostgreSQL ready on localhost:5432 (user/pass/db: syncfit)"
