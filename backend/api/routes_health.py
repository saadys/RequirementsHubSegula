import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.BaseDataModel import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Production Health Check Probe for GCP Cloud Run.
    Verifies API availability and validates PostgreSQL DB connection.
    """
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "version": "0.1.0",
            "database": "connected",
        }
    except Exception as exc:
        logger.error("Health check database probe failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "version": "0.1.0",
                "database": "disconnected",
            },
        )

