#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

cd "$SERVER_DIR"

docker compose build --no-cache

echo "Server image built. Database migrations run automatically when the server container starts."
