"""
AI Team Dashboard API Routes

Provides endpoints for listing pending submissions and performing manual decision overrides
by AI Engineers using PostgreSQL / SQLAlchemy.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.BaseDataModel import get_db
from backend.models.ReviewerModel import ReviewerModel
from backend.models.SubmissionModel import SubmissionModel
from backend.schemas import (
    Decision,
    DecisionOverrideInput,
    DecisionOverrideResponse,
    PendingSubmissionItem,
    SubmissionStatus,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/pending",
    response_model=List[PendingSubmissionItem],
    summary="List all requests for AI Engineering review",
)
async def list_pending_requests(
    status_filter: Optional[str] = None, db: AsyncSession = Depends(get_db)
):
    """Retrieves submissions for AI engineering review (optionally filtered by status)."""
    sub_model = SubmissionModel(db)
    all_subs = await sub_model.get_all_with_relations()
    pending_items = []

    for sub in all_subs:
        scoring = sub.scoring_result
        overrides = sub.reviewer_overrides or []
        dec = overrides[0].new_decision if overrides else (scoring.decision if scoring else None)
        stat = sub.status or SubmissionStatus.PROCESSED.value
        fact = sub.fact_extraction
        rep = sub.report
        rounds = sub.clarification_rounds or []
        clar_round = rounds[-1].round_number if rounds else 0
        missing_fields = fact.extracted_requirements if (fact and fact.extracted_requirements) else []

        if status_filter and status_filter.upper() != "ALL":
            sf = status_filter.upper()
            if sf == Decision.GO.value:
                matches = stat in [SubmissionStatus.COMPLETED.value, Decision.GO.value] or dec == Decision.GO.value
            elif sf in [Decision.NO_GO.value, SubmissionStatus.REJECTED.value]:
                matches = stat in [SubmissionStatus.REJECTED.value, Decision.NO_GO.value] or dec == Decision.NO_GO.value
            elif sf == Decision.NEEDS_CLARIFICATION.value:
                matches = (
                    stat == SubmissionStatus.NEEDS_CLARIFICATION.value
                    or dec == Decision.NEEDS_CLARIFICATION.value
                )
            elif sf == SubmissionStatus.INCOMPLETE.value:
                matches = stat == SubmissionStatus.INCOMPLETE.value or bool(missing_fields)
            else:
                matches = stat == sf or dec == sf
            if not matches:
                continue

        has_rep = bool(rep and rep.content and rep.content.strip())
        created_at_str = (
            sub.created_at.isoformat()
            if sub.created_at and hasattr(sub.created_at, "isoformat")
            else (str(sub.created_at) if sub.created_at else None)
        )

        sub_scores = {}
        veto_triggered = False
        veto_reasons = []
        if scoring and scoring.breakdown:
            sub_scores = scoring.breakdown.get("sub_scores") or scoring.breakdown.get("pillar_scores") or {}
            veto_triggered = bool(scoring.breakdown.get("veto_triggered", False))
            veto_reasons = scoring.breakdown.get("veto_reasons") or []

        pending_items.append(
            PendingSubmissionItem(
                request_id=str(sub.id),
                project_name=sub.project_name or "Untitled Project",
                department=sub.department_id or "corporate_support",
                team_contact_name=sub.team_contact_name or "N/A",
                team_contact_email=sub.team_contact_email or "N/A",
                status=stat,
                decision=dec,
                score=scoring.score if scoring else None,
                sub_scores=sub_scores,
                veto_triggered=veto_triggered,
                veto_reasons=veto_reasons,
                ai_viability_category=fact.ai_viability_category if fact else None,
                data_readiness_category=fact.data_readiness_category if fact else None,
                problem_clarity_category=fact.problem_clarity_category if fact else None,
                integration_category=fact.integration_category if fact else None,
                governance_category=fact.governance_category if fact else None,
                clarification_round=clar_round,
                created_at=created_at_str,
                missing_fields=missing_fields,
                has_report=has_rep,
                report_type=rep.report_type if rep else None,
            )
        )

    return pending_items



@router.post(
    "/{request_id}/decision",
    response_model=DecisionOverrideResponse,
    summary="Manual decision override by AI Engineer",
)
async def override_submission_decision(
    request_id: str, payload: DecisionOverrideInput, db: AsyncSession = Depends(get_db)
):
    """Allows an AI engineer to manually override or finalize the decision (e.g. approve a NO_GO or partial request)."""
    sub_model = SubmissionModel(db)
    sub = await sub_model.get_by_id_with_relations(request_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{request_id}' not found",
        )

    overrides = sub.reviewer_overrides or []
    prev_decision = overrides[0].new_decision if overrides else (sub.scoring_result.decision if sub.scoring_result else sub.status)

    new_status = sub.status
    if payload.decision == Decision.GO.value:
        new_status = SubmissionStatus.COMPLETED.value
    elif payload.decision == Decision.NO_GO.value:
        new_status = SubmissionStatus.REJECTED.value
    elif payload.decision == Decision.NEEDS_CLARIFICATION.value:
        new_status = SubmissionStatus.NEEDS_CLARIFICATION.value

    rev_model = ReviewerModel(db)
    await rev_model.create_override(
        submission_id=request_id,
        previous_decision=prev_decision,
        new_decision=payload.decision,
        reviewer_name=payload.reviewer_name or "AI Engineer",
        reviewer_notes=payload.reviewer_notes,
    )

    await sub_model.update_status(request_id, new_status)

    return DecisionOverrideResponse(
        request_id=str(sub.id),
        decision=payload.decision,
        status=new_status,
        score=sub.scoring_result.score if sub.scoring_result else None,
        reviewer_notes=payload.reviewer_notes,
        reviewer_name=payload.reviewer_name,
        manual_override=True,
        updated_at=datetime.now().isoformat(),
    )
