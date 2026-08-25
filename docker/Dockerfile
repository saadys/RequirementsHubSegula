FROM python:3.12-slim AS builder

# Install uv(Extraction du binaire uv depuis son conteneur officiel vers le dossier /bin/uv)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv


WORKDIR /app

COPY pyproject.toml uv.lock ./

# Copy dependency files first (cache layer)
ENV UV_PROJECT_ENVIRONMENT="/app/.venv"
RUN uv sync --frozen --no-dev --no-install-project

#############################


FROM python:3.12-slim AS runner

# Copy application code
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser

WORKDIR /app

# Variables d'environnement standard Python de production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder /app/.venv /app/.venv

COPY backend /app/backend

# Alembic config lives at the project root; env.py resolves the script_location
# and imports `backend.config` for DATABASE_URL, so both must ship in the image.
COPY alembic.ini /app/alembic.ini

# --chmod is required: the build host may be Windows, which carries no exec bit.
COPY --chmod=0755 docker/entrypoint.sh /usr/local/bin/entrypoint.sh

USER appuser

EXPOSE 8000

# Roles: `migrate` (one-shot job) or `api` (default). See docker/entrypoint.sh.
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["api"]

