#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

cd "$SERVER_DIR"

mkdir -p data

rm -f ../data/lan_control_plane.db
docker compose build --no-cache
docker compose --profile tools run --rm migrate
