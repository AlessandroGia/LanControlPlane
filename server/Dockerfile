FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md ./
COPY server ./server
COPY shared ./shared
COPY alembic ./alembic

RUN uv sync

EXPOSE 8000