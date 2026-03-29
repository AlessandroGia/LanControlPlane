#!/usr/bin/env bash
set -euo pipefail

rm -f ../data/lan_control_plane.db
docker compose -f docker-compose.yml --profile tools run --rm migrate
docker compose -f docker-compose.yml build --no-cache
