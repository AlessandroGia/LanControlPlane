#!/usr/bin/env sh
set -eu

alembic -c /app/server/alembic.ini upgrade head
exec "$@"
