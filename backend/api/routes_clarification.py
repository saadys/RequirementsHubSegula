"""
Clarification API Routes

Handles multi-turn clarification loops for submissions requiring additional context via PostgreSQL / SQLAlchemy.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import MAX_CLARIFICATION_ROUNDS
from backend.graph.builder import get_compiled_graph
from backend.models.BaseDataModel import get_db
from backend.models.ClarificationModel import ClarificationModel
from backend.models.FactExtractionModel import FactExtractionModel
from backend.models.ReportModel import ReportModel
from backend.models.ScoringModel import ScoringModel
from backend.models.SubmissionModel import SubmissionModel
from backend.schemas import ClarificationAnswerInput, ClarificationResponse, Decision, SubmissionStatus

router = APIRouter(prefix="/submissions", tags=["Clarification"])


def _determine_status(result_state: Dict[str, Any]) -> str:
    """Derives overall user-facing status from pipeline result state."""
    if result_state.get("missing_fields"):
        return SubmissionStatus.INCOMPLETE.value
    if result_state.get("is_exact_match"):
        return SubmissionStatus.FAST_TRACK.value
    decision = result_state.get("decision")
    if decision == Decision.GO.value:
        return SubmissionStatus.COMPLETED.value
    elif decision == Decision.NO_GO.value:
        return SubmissionStatus.REJECTED.value
    elif decision == Decision.NEEDS_CLARIFICATION.value:
        return SubmissionStatus.NEEDS_CLARIFICATION.value
    return SubmissionStatus.PROCESSED.value


@router.get(
    "/{request_id}/clarification",
    response_model=ClarificationResponse,
    summary="Get current clarification questions for a submission",
)
async def get_clarification_questions(request_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves current clarification questions and round history for a submission."""
    sub_model = SubmissionModel(db)
    sub = await sub_model.get_by_id_with_relations(request_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{request_id}' not found",
        )

    rounds = sub.clarification_rounds or []
    latest_round = rounds[-1] if rounds else None
    overrides = sub.reviewer_overrides or []
    scoring = sub.scoring_result
    decision = overrides[0].new_decision if overrides else (scoring.decision if scoring else None)

    sub_scores = {}
    veto_triggered = False
    veto_reasons = []
    if scoring and scoring.breakdown:
        sub_scores = scoring.breakdown.get("sub_scores") or scoring.breakdown.get("pillar_scores") or {}
        veto_triggered = bool(scoring.breakdown.get("veto_triggered", False))
        veto_reasons = scoring.breakdown.get("veto_reasons") or []

    return ClarificationResponse(
        request_id=str(sub.id),
        status=sub.status,
        clarification_round=latest_round.round_number if latest_round else 0,
        max_rounds=MAX_CLARIFICATION_ROUNDS,
        questions=latest_round.questions if latest_round else [],
        answers=latest_round.answers if latest_round else [],
        score=scoring.score if scoring else None,
        decision=decision,
        sub_scores=sub_scores,
        veto_triggered=veto_triggered,
        veto_reasons=veto_reasons,
        report_type=sub.report.report_type if sub.report else None,
        report=sub.report.content if sub.report else None,
    )


@router.post(
    "/{request_id}/clarification",
    response_model=ClarificationResponse,
    summary="Submit answers to clarification questions & re-trigger pipeline",
)
async def submit_clarification_answers(
    request_id: str, payload: ClarificationAnswerInput, db: AsyncSession = Depends(get_db)
):
    """Submits user answers to clarification questions and re-invokes the LangGraph pipeline."""
    sub_model = SubmissionModel(db)
    sub = await sub_model.get_by_id_with_relations(request_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{request_id}' not found",
        )

    overrides = sub.reviewer_overrides or []
    curr_decision = overrides[0].new_decision if overrides else (sub.scoring_result.decision if sub.scoring_result else None)
    curr_status = sub.status

    if curr_decision != "NEEDS_CLARIFICATION" and curr_status != "NEEDS_CLARIFICATION":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Submission '{request_id}' does not currently require clarification (status: '{curr_status}', decision: '{curr_decision}')",
        )

    clar_model = ClarificationModel(db)
    rounds = sub.clarification_rounds or []
    latest_round = rounds[-1] if rounds else None
    curr_round_num = latest_round.round_number if latest_round else 1

    existing_answers = list(latest_round.answers) if (latest_round and latest_round.answers) else []
    existing_answers.extend(payload.answers)

    if latest_round:
        await clar_model.update_answers(request_id, curr_round_num, existing_answers)
    else:
        await clar_model.create_round(request_id, round_number=1, questions=[], answers=existing_answers)

    form_dict = {
        "project_name": sub.project_name,
        "department": sub.department_id,
        "team_contact_name": sub.team_contact_name,
        "team_contact_email": sub.team_contact_email,
        "problem_description": sub.problem_description,
        "current_process": sub.current_process,
        "expected_outcome": sub.expected_outcome,
        "data_description": sub.data_description,
        "deadline_urgency": sub.deadline_urgency,
        "department_specific": sub.department_specific or {},
    }

    state = {
        "request_id": str(sub.id),
        "form_data": form_dict,
        "department": sub.department_id or "corporate_support",
        "clarification_round": curr_round_num,
        "clarification_answers": existing_answers,
        "clarification_questions": latest_round.questions if latest_round else [],
    }

    graph = get_compiled_graph()
    updated_state = await graph.ainvoke(state)

    status_str = _determine_status(updated_state)
    await sub_model.update_status(request_id, status_str)

    if updated_state.get("extracted_facts"):
        fact_model = FactExtractionModel(db)
        await fact_model.create_or_update(
            request_id,
            updated_state.get("extracted_facts") or {},
        )

    if updated_state.get("score") is not None or updated_state.get("decision"):
        scoring_model = ScoringModel(db)
        sub_scores_val = updated_state.get("sub_scores") or {}
        veto_trig = updated_state.get("veto_triggered", False)
        veto_reasons_val = updated_state.get("veto_reasons") or []

        breakdown_payload = {
            "sub_scores": sub_scores_val,
            "veto_triggered": veto_trig,
            "veto_reasons": veto_reasons_val,
        }
        if updated_state.get("score_breakdown"):
            breakdown_payload["legacy_breakdown"] = updated_state.get("score_breakdown")

        await scoring_model.create_or_update(
            request_id,
            {
                "score": updated_state.get("score"),
                "percentage": updated_state.get("score"),
                "decision": updated_state.get("decision"),
                "breakdown": breakdown_payload,
            },
        )

    if updated_state.get("report"):
        report_model = ReportModel(db)
        await report_model.create_or_update(
            request_id,
            report_type=updated_state.get("report_type", "FULL_CAHIER_DES_CHARGES"),
            content=updated_state.get("report"),
        )

    if updated_state.get("clarification_questions") and status_str == SubmissionStatus.NEEDS_CLARIFICATION.value:
        next_round_num = curr_round_num + 1
        if next_round_num <= MAX_CLARIFICATION_ROUNDS:
            await clar_model.create_round(
                submission_id=request_id,
                round_number=next_round_num,
                questions=updated_state.get("clarification_questions", []),
                answers=[],
            )

    refreshed_sub = await sub_model.get_by_id_with_relations(request_id)
    ref_rounds = refreshed_sub.clarification_rounds or []
    ref_latest = ref_rounds[-1] if ref_rounds else None
    ref_scoring = refreshed_sub.scoring_result

    ref_sub_scores = {}
    ref_veto_trig = False
    ref_veto_reasons = []
    if ref_scoring and ref_scoring.breakdown:
        ref_sub_scores = ref_scoring.breakdown.get("sub_scores") or ref_scoring.breakdown.get("pillar_scores") or {}
        ref_veto_trig = bool(ref_scoring.breakdown.get("veto_triggered", False))
        ref_veto_reasons = ref_scoring.breakdown.get("veto_reasons") or []

    return ClarificationResponse(
        request_id=str(refreshed_sub.id),
        status=refreshed_sub.status,
        clarification_round=ref_latest.round_number if ref_latest else curr_round_num,
        max_rounds=MAX_CLARIFICATION_ROUNDS,
        questions=ref_latest.questions if ref_latest else [],
        answers=ref_latest.answers if ref_latest else existing_answers,
        score=ref_scoring.score if ref_scoring else None,
        decision=ref_scoring.decision if ref_scoring else None,
        sub_scores=ref_sub_scores,
        veto_triggered=ref_veto_trig,
        veto_reasons=ref_veto_reasons,
        report_type=refreshed_sub.report.report_type if refreshed_sub.report else None,
        report=refreshed_sub.report.content if refreshed_sub.report else None,
    )

