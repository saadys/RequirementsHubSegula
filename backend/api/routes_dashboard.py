from typing import List, Optional
from fastapi import APIRouter, HTTPException, status

from backend.schemas import (
    Decision,
    DecisionOverrideInput,
    DecisionOverrideResponse,
    PendingSubmissionItem,
    SubmissionStatus,
)
from backend.services.storage import get_submission, list_submissions, save_submission

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/pending",
    response_model=List[PendingSubmissionItem],
    summary="List all requests for AI Engineering review",
)
async def list_pending_requests(status_filter: Optional[str] = None):
    """Retrieves submissions for AI engineering review (optionally filtered by status)."""
    all_subs = list_submissions()
    pending_items = []

    for sub in all_subs:
        dec = sub.get("decision")
        stat = sub.get("status", SubmissionStatus.PROCESSED.value)

        # Determine matching based on status filter
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
                matches = stat == SubmissionStatus.INCOMPLETE.value or bool(sub.get("missing_fields"))
            else:
                matches = stat == sf or dec == sf
            if not matches:
                continue

        form_data = sub.get("form_data", {}) or {}
        has_rep = bool(sub.get("report"))
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
                has_report=has_rep,
                report_type=sub.get("report_type"),
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
    if payload.decision == Decision.GO.value:
        state["status"] = SubmissionStatus.COMPLETED.value
    elif payload.decision == Decision.NO_GO.value:
        state["status"] = SubmissionStatus.REJECTED.value
    elif payload.decision == Decision.NEEDS_CLARIFICATION.value:
        state["status"] = SubmissionStatus.NEEDS_CLARIFICATION.value

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
