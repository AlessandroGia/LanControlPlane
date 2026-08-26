FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY shared/pyproject.toml /app/shared/pyproject.toml
COPY shared/src /app/shared/src

COPY server/pyproject.toml /app/server/pyproject.toml
COPY server/uv.lock /app/server/uv.lock
COPY server/src /app/server/src
COPY server/alembic /app/server/alembic
COPY server/alembic.ini /app/server/alembic.ini
COPY server/scripts/docker-entrypoint.sh /app/server/docker-entrypoint.sh

WORKDIR /app/server

RUN uv sync --frozen --no-dev

FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/server/.venv/bin:$PATH"

WORKDIR /app/server

COPY --from=builder /app/server/.venv /app/server/.venv
COPY --from=builder /app/server/src /app/server/src
COPY --from=builder /app/server/alembic /app/server/alembic
COPY --from=builder /app/server/alembic.ini /app/server/alembic.ini
COPY --from=builder /app/server/docker-entrypoint.sh /app/server/docker-entrypoint.sh
COPY --from=builder /app/shared/src /app/shared/src

RUN chmod +x /app/server/docker-entrypoint.sh

ENTRYPOINT ["/app/server/docker-entrypoint.sh"]
CMD ["uvicorn", "lan_control_plane_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
