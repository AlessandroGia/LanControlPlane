#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"

for project in shared server agent; do
  echo "==> Checking $project"
  cd "$REPO_ROOT/$project"
  uv sync --all-groups --frozen
  uv run ruff check .
  uv run ruff format --check .
  uv run mypy src
  uv run pytest -q
done

echo "==> Checking web"
cd "$REPO_ROOT/web"
npm ci
npm run lint
npm run build
