#!/bin/sh
# =============================================================================
# docker/entrypoint.sh — Role dispatcher for Segula AI Requirement Hub
#
# Automatically executes Alembic schema migrations on startup before booting
# the FastAPI ASGI server on Cloud Run / container runtime.
# =============================================================================
set -eu

case "${1:-api}" in
    migrate)
        echo "[entrypoint] Applying Alembic database migrations..."
        exec alembic upgrade head
        ;;
    api)
        echo "[entrypoint] Applying Alembic database migrations..."
        alembic upgrade head || {
            echo "[entrypoint] ⚠️ Alembic migration failed or was skipped. Proceeding with application startup..."
        }
        echo "[entrypoint] Starting Segula AI Requirement Hub on port ${PORT:-8080}..."
        exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8080}"
        ;;
    *)
        exec "$@"
        ;;
esac
