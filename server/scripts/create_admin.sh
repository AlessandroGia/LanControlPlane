#!/usr/bin/env bash
set -euo pipefail

SECRET_FILE="${1:-./secrets/admin_password.txt}"

if [[ ! -f "$SECRET_FILE" ]]; then
  echo "Secret file not found: $SECRET_FILE" >&2
  exit 1
fi

docker compose -f docker-compose.yml --profile tools run --rm \
  -e LCP_ADMIN_PASSWORD_FILE=/run/secrets/admin_password.txt \
  -v "$(pwd)/${SECRET_FILE#./}:/run/secrets/admin_password.txt:ro" \
  create-admin
