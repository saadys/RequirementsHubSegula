"""
Dashboard API Routes (AI Engineering Team)

Provides endpoints for AI engineers to monitor pending AI requests
and manually override Go/No-Go decisions.
"""

from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.services.storage import get_submission, list_submissions, save_submission

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class DecisionOverrideInput(BaseModel):
    decision: Literal["GO", "NO_GO", "NEEDS_CLARIFICATION"] = Field(
        ..., description="New decision status override by AI engineer"
    )
    reviewer_notes: Optional[str] = Field(
        None, description="Optional feedback or rationale from the AI engineer"
    )
    reviewer_name: Optional[str] = Field(
        "AI Engineer", description="Name or ID of the reviewing AI engineer"
    )


class DecisionOverrideResponse(BaseModel):
    request_id: str
    decision: str
    status: str
    score: Optional[int] = None
    reviewer_notes: Optional[str] = None
    reviewer_name: Optional[str] = None
    manual_override: bool = True
    updated_at: Optional[str] = None


class PendingSubmissionItem(BaseModel):
    request_id: str
    project_name: Optional[str] = "Untitled Project"
    department: Optional[str] = "corporate_support"
    team_contact_name: Optional[str] = "N/A"
    team_contact_email: Optional[str] = "N/A"
    status: str
    decision: Optional[str] = None
    score: Optional[int] = None
    clarification_round: int = 0
    created_at: Optional[str] = None
    missing_fields: List[str] = []


@router.get(
    "/pending",
    response_model=List[PendingSubmissionItem],
    summary="List all requests awaiting review or clarification",
)
async def list_pending_requests(status_filter: Optional[str] = None):
    """Retrieves all submissions that are pending review or clarification (e.g. NEEDS_CLARIFICATION, INCOMPLETE, REJECTED)."""
    all_subs = list_submissions()
    pending_items = []

    for sub in all_subs:
        dec = sub.get("decision")
        stat = sub.get("status", "PROCESSED")

        # By default, pending includes requests needing clarification, incomplete, or rejected/review
        is_pending = (
            stat in ["NEEDS_CLARIFICATION", "INCOMPLETE", "REJECTED"]
            or dec in ["NEEDS_CLARIFICATION", "NO_GO"]
            or bool(sub.get("missing_fields"))
        )

        if status_filter:
            is_pending = is_pending and (stat == status_filter or dec == status_filter)

        if is_pending:
            form_data = sub.get("form_data", {}) or {}
            pending_items.append(
                PendingSubmissionItem(
                    request_id=sub["request_id"],
                    project_name=form_data.get("project_name") or "Untitled Project",
                    department=sub.get("department") or form_data.get("department") or "corporate_support",
                    team_contact_name=form_data.get("team_contact_name") or "N/A",
                    team_contact_email=form_data.get("team_contact_email") or "N/A",
                    status=stat,
                    decision=dec,
                    score=sub.get("score"),
                    clarification_round=sub.get("clarification_round", 0),
                    created_at=sub.get("created_at"),
                    missing_fields=sub.get("missing_fields", []),
                )
            )

    return pending_items


@router.post(
    "/{request_id}/decision",
    response_model=DecisionOverrideResponse,
    summary="Manual decision override by AI Engineer",
)
async def override_submission_decision(
    request_id: str, payload: DecisionOverrideInput
):
    """Allows an AI engineer to manually override or finalize the decision (e.g. approve a NO_GO or partial request)."""
    state = get_submission(request_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{request_id}' not found",
        )

    state["decision"] = payload.decision
    if payload.decision == "GO":
        state["status"] = "COMPLETED"
    elif payload.decision == "NO_GO":
        state["status"] = "REJECTED"
    elif payload.decision == "NEEDS_CLARIFICATION":
        state["status"] = "NEEDS_CLARIFICATION"

    state["reviewer_notes"] = payload.reviewer_notes
    state["reviewer_name"] = payload.reviewer_name
    state["manual_override"] = True

    saved_state = save_submission(request_id, state)

    return DecisionOverrideResponse(
        request_id=request_id,
        decision=saved_state["decision"],
        status=saved_state["status"],
        score=saved_state.get("score"),
        reviewer_notes=saved_state.get("reviewer_notes"),
        reviewer_name=saved_state.get("reviewer_name"),
        manual_override=True,
        updated_at=saved_state.get("updated_at"),
    )
