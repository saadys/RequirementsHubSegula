#!/bin/sh
# =============================================================================
# docker/entrypoint.sh — Role dispatcher for the RequirementsHub backend image
#
# One image, several roles. The migration is NOT chained to the API start-up
# on purpose: with N replicas (Cloud Run, k8s), every replica would race for
# the ACCESS EXCLUSIVE lock on `alembic_version`, the losers would stall past
# their health-check deadline and crash-loop the whole rollout.
#
# Roles:
#   migrate  -> apply Alembic migrations, then exit (one-shot job)
#   api      -> serve the FastAPI app (default)
#   <other>  -> executed verbatim, so `docker run <image> sh` still works
# =============================================================================
set -eu

case "${1:-api}" in
    migrate)
        echo "[entrypoint] applying Alembic migrations..."
        exec alembic upgrade head
        ;;
    api)
        echo "[entrypoint] starting API on port ${PORT:-8000}..."
        exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"
        ;;
    *)
        exec "$@"
        ;;
esac
