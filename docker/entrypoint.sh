#!/bin/sh
# =============================================================================
# docker/entrypoint.sh — Role dispatcher for Segula AI Requirement Hub
#
# Automatically executes Alembic schema migrations and loads seed data
# (departments + RAG vector knowledge) before booting the FastAPI ASGI server.
# =============================================================================

case "${1:-api}" in
    migrate)
        echo "[entrypoint] Applying Alembic database migrations..."
        alembic upgrade head
        echo "[entrypoint] Seeding initial departments and historic vector knowledge base..."
        python -m backend.cli.seed
        echo "[entrypoint] ✅ Migration and database seeding completed."
        ;;
    api)
        echo "[entrypoint] Applying Alembic database migrations..."
        alembic upgrade head || echo "[entrypoint] ⚠️ Alembic migration failed or was skipped. Proceeding..."
        echo "[entrypoint] Seeding initial departments and historic vector knowledge base..."
        python -m backend.cli.seed || echo "[entrypoint] ⚠️ Seeding failed or was skipped. Proceeding..."
        echo "[entrypoint] Starting Segula AI Requirement Hub on port ${PORT:-8080}..."
        exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8080}"
        ;;
    *)
        exec "$@"
        ;;
esac
