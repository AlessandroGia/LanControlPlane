#!/usr/bin/env bash
set -euo pipefail

docker compose --profile tools run --rm lint
docker compose --profile tools run --rm format
docker compose --profile tools run --rm tests