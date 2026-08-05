# ── base ──────────────────────────────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS base

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ── dev ───────────────────────────────────────────────────────────────────────
# Used by docker-compose for local development with hot-reload.
# Does NOT require uv.lock — run `uv lock` locally first, then commit it
# before building the prod image (which uses --frozen for reproducibility).
FROM base AS dev

COPY pyproject.toml uv.lock* ./
RUN uv sync --no-install-project

COPY . .
RUN uv sync

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "ideaforge.main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── builder ───────────────────────────────────────────────────────────────────
# Installs only production dependencies into an isolated venv.
FROM base AS builder

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ ./src/
RUN uv sync --frozen --no-dev

# ── prod ──────────────────────────────────────────────────────────────────────
# Minimal runtime image — only the venv and source, no build tooling.
FROM python:3.12-slim AS prod

WORKDIR /app

COPY --from=builder /app/.venv ./.venv
COPY --from=builder /app/src ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONUNBUFFERED=1

EXPOSE 8000
# PORT is injected by Railway/Render; default to 8000 locally
CMD ["sh", "-c", "uvicorn ideaforge.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
