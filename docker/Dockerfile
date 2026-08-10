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

USER appuser

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
