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

    sub_scores = {}
    veto_triggered = False
    veto_reasons = []
    score_val = None
    if sub.scoring_result:
        score_val = sub.scoring_result.score
        if sub.scoring_result.breakdown:
            sub_scores = sub.scoring_result.breakdown.get("sub_scores") or sub.scoring_result.breakdown.get("pillar_scores") or {}
            veto_triggered = bool(sub.scoring_result.breakdown.get("veto_triggered", False))
            veto_reasons = sub.scoring_result.breakdown.get("veto_reasons") or []

    return ReportResponse(
        request_id=str(sub.id),
        report_type=report_type,
        report=report_text,
        decision=decision,
        score=score_val,
        sub_scores=sub_scores,
        veto_triggered=veto_triggered,
        veto_reasons=veto_reasons,
        is_available=is_avail,
    )


@router.get(
    "/{request_id}/score",
    response_model=ScoreResponse,
    summary="Get 0-100 feasibility score and 5-pillar breakdown",
)
async def get_submission_score(request_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves the numerical score (0-100), decision, and full breakdown across all 5 feasibility pillars."""
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

    sub_scores = {}
    veto_triggered = False
    veto_reasons = []
    if breakdown_dict:
        sub_scores = breakdown_dict.get("sub_scores") or breakdown_dict.get("pillar_scores") or {}
        veto_triggered = bool(breakdown_dict.get("veto_triggered", False))
        veto_reasons = breakdown_dict.get("veto_reasons") or []

    pillars_dict = {}
    fact = sub.fact_extraction
    if fact:
        if fact.ai_viability_category:
            pillars_dict["ai_viability"] = {"category": fact.ai_viability_category, "reason": fact.ai_viability_reason}
        if fact.data_readiness_category:
            pillars_dict["data_readiness"] = {"category": fact.data_readiness_category, "reason": fact.data_readiness_reason}
        if fact.problem_clarity_category:
            pillars_dict["problem_clarity"] = {"category": fact.problem_clarity_category, "reason": fact.problem_clarity_reason}
        if fact.integration_category:
            pillars_dict["integration_feasibility"] = {"category": fact.integration_category, "reason": fact.integration_reason}
        if fact.governance_category:
            pillars_dict["governance_and_safety"] = {"category": fact.governance_category, "reason": fact.governance_reason}

    overrides = sub.reviewer_overrides or []
    decision = overrides[0].new_decision if overrides else (scoring.decision if scoring else None)

    return ScoreResponse(
        request_id=str(sub.id),
        score=score_val,
        percentage=score_val,
        decision=decision,
        sub_scores=sub_scores,
        veto_triggered=veto_triggered,
        veto_reasons=veto_reasons,
        breakdown=breakdown_dict,
        pillars=pillars_dict,
    )

