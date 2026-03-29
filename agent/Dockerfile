FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY shared/pyproject.toml /app/shared/pyproject.toml
COPY shared/src /app/shared/src

COPY agent/pyproject.toml /app/agent/pyproject.toml
COPY agent/uv.lock /app/agent/uv.lock
COPY agent/src /app/agent/src

WORKDIR /app/agent

RUN uv sync --frozen --no-dev

FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/agent/.venv/bin:$PATH"

WORKDIR /app/agent

COPY --from=builder /app/agent/.venv /app/agent/.venv
COPY --from=builder /app/agent/src /app/agent/src
COPY --from=builder /app/shared/src /app/shared/src

CMD ["python", "-m", "lan_control_plane_agent.main"]
