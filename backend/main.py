"""
FastAPI Application Entry Point

Owner: TOGETHER (Phase 3 — Integration)
"""

from fastapi import FastAPI

app = FastAPI(
    title="AI Requirement Hub",
    description="AI-powered intermediary tool between business teams and the AI team at Segula Technologies",
    version="0.1.0",
)


from backend.api.routes_departments import router as departments_router
from backend.api.routes_submissions import router as submissions_router
from backend.api.routes_clarification import router as clarification_router
from backend.api.routes_reports import router as reports_router
from backend.api.routes_dashboard import router as dashboard_router

app.include_router(departments_router, prefix="/api")
app.include_router(submissions_router, prefix="/api")
app.include_router(clarification_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


