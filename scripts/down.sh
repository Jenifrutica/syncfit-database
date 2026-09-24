#!/usr/bin/env bash
# Stop the SyncFit PostgreSQL container.
if docker compose version >/dev/null 2>&1; then
  docker compose down
else
  docker rm -f syncfit-postgres
fi
