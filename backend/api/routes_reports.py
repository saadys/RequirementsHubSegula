"""
Reports & Scores API Routes

Provides endpoints for retrieving generated Markdown reports (Cahier des Charges / Fast-Track)
and detailed 7-criterion feasibility scores for submissions.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status

from backend.schemas import ReportResponse, ScoreResponse
from backend.services.storage import get_submission

router = APIRouter(prefix="/submissions", tags=["Reports & Scores"])


@router.get(
    "/{request_id}/report",
    response_model=ReportResponse,
    summary="Get final generated Markdown report",
)
async def get_submission_report(request_id: str):
    """Retrieves the generated Markdown Cahier des Charges or Fast-Track solution report."""
    state = get_submission(request_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{request_id}' not found",
        )

    report_text = state.get("report")
    report_type = state.get("report_type")
    is_avail = bool(report_text and report_text.strip())

    return ReportResponse(
        request_id=request_id,
        report_type=report_type,
        report=report_text,
        decision=state.get("decision"),
        is_available=is_avail,
    )


@router.get(
    "/{request_id}/score",
    response_model=ScoreResponse,
    summary="Get 0-100 feasibility score and 7-criterion breakdown",
)
async def get_submission_score(request_id: str):
    """Retrieves the numerical score (0-100), decision, and full breakdown across all 7 criteria."""
    state = get_submission(request_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{request_id}' not found",
        )

    score_val = state.get("score")
    breakdown_dict = state.get("score_breakdown", {})

    return ScoreResponse(
        request_id=request_id,
        score=score_val,
        percentage=score_val,
        decision=state.get("decision"),
        breakdown=breakdown_dict,
    )
