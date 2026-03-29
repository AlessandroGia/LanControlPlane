#!/usr/bin/env bash
set -euo pipefail

docker compose -f server/docker-compose.yml --profile tools run --rm format