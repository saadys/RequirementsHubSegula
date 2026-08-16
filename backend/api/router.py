"""
Main API Router

Aggregates all sub-routers (health, departments, submissions, clarification, reports, dashboard)
under the central /api prefix.
"""

from fastapi import APIRouter

from backend.api.routes_clarification import router as clarification_router
from backend.api.routes_dashboard import router as dashboard_router
from backend.api.routes_departments import router as departments_router
from backend.api.routes_health import router as health_router
from backend.api.routes_reports import router as reports_router
from backend.api.routes_stream import router as stream_router
from backend.api.routes_submissions import router as submissions_router

api_router = APIRouter(prefix="/api")

# Register sub-routers
api_router.include_router(health_router)
api_router.include_router(departments_router)
api_router.include_router(submissions_router)
api_router.include_router(stream_router)
api_router.include_router(clarification_router)
api_router.include_router(reports_router)
api_router.include_router(dashboard_router)
