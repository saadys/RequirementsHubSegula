"""
Reports & Scores API Routes

Provides endpoints for retrieving generated Markdown reports (Cahier des Charges / Fast-Track)
and detailed 7-criterion feasibility scores for submissions via PostgreSQL / SQLAlchemy.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.BaseDataModel import get_db
from backend.models.SubmissionModel import SubmissionModel
from backend.schemas import ReportResponse, ScoreResponse

router = APIRouter(prefix="/submissions", tags=["Reports & Scores"])


@router.get(
    "/{request_id}/report",
    response_model=ReportResponse,
    summary="Get final generated Markdown report",
)
async def get_submission_report(request_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves the generated Markdown Cahier des Charges or Fast-Track solution report."""
    sub_model = SubmissionModel(db)
    sub = await sub_model.get_by_id_with_relations(request_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{request_id}' not found",
        )

    rep = sub.report
    report_text = rep.content if rep else None
    report_type = rep.report_type if rep else None
    is_avail = bool(report_text and report_text.strip())

    overrides = sub.reviewer_overrides or []
    decision = overrides[0].new_decision if overrides else (sub.scoring_result.decision if sub.scoring_result else None)

    return ReportResponse(
        request_id=str(sub.id),
        report_type=report_type,
        report=report_text,
        decision=decision,
        is_available=is_avail,
    )


@router.get(
    "/{request_id}/score",
    response_model=ScoreResponse,
    summary="Get 0-100 feasibility score and 7-criterion breakdown",
)
async def get_submission_score(request_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves the numerical score (0-100), decision, and full breakdown across all 7 criteria."""
    sub_model = SubmissionModel(db)
    sub = await sub_model.get_by_id_with_relations(request_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{request_id}' not found",
        )

    scoring = sub.scoring_result
    score_val = scoring.score if scoring else None
    breakdown_dict = scoring.breakdown if scoring else {}

    overrides = sub.reviewer_overrides or []
    decision = overrides[0].new_decision if overrides else (scoring.decision if scoring else None)

    return ScoreResponse(
        request_id=str(sub.id),
        score=score_val,
        percentage=score_val,
        decision=decision,
        breakdown=breakdown_dict,
    )
