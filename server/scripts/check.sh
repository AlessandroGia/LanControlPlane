#!/usr/bin/env bash
set -euo pipefail

docker compose -f docker-compose.yml --profile tools run --rm lint
docker compose -f docker-compose.yml --profile tools run --rm format
docker compose -f docker-compose.yml --profile tools run --rm tests
