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

RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    cd /app/agent && \
    uv sync --frozen --no-dev

FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY shared/src /app/shared/src
COPY agent/src /app/agent/src

CMD ["python", "-m", "lan_control_plane_agent.main"]
