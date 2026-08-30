# ==============================================================================
# Multi-stage Unified Production Dockerfile for Segula AI Requirement Hub
# Target: GCP Cloud Run / Production Container Runtime
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Frontend Build (Node.js)
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Copy dependencies manifest first to leverage Docker layer caching
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy frontend source code and compile production assets
COPY frontend/ ./
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Python Backend Dependency Builder (uv)
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS python-builder

# Install astral-sh uv binary for lightning-fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

ENV UV_PROJECT_ENVIRONMENT="/app/.venv"
RUN uv sync --frozen --no-dev --no-install-project

# ------------------------------------------------------------------------------
# Stage 3: Production Runtime (Unified FastAPI + Static SPA Server)
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS runner

# Security: Create unprivileged system user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser

WORKDIR /app

# Standard production Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PORT=8080 \
    STATIC_DIR=/app/frontend_dist

# Copy Python virtual environment from builder with ownership
COPY --chown=appuser:appgroup --from=python-builder /app/.venv /app/.venv

# Copy compiled frontend production assets from frontend-builder
COPY --chown=appuser:appgroup --from=frontend-builder /frontend/dist /app/frontend_dist

# Copy backend source code and alembic configuration
COPY --chown=appuser:appgroup backend /app/backend
COPY --chown=appuser:appgroup alembic.ini /app/alembic.ini

# Copy entrypoint script with execute permissions
COPY --chmod=0755 docker/entrypoint.sh /usr/local/bin/entrypoint.sh

USER appuser

# Cloud Run default listening port
EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["api"]
