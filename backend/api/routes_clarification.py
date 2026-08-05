"""
Clarification API Routes

Handles multi-turn clarification loops for submissions requiring additional context.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from backend.config import MAX_CLARIFICATION_ROUNDS
from backend.graph.builder import get_compiled_graph
from backend.schemas import ClarificationAnswerInput, ClarificationResponse, Decision, SubmissionStatus
from backend.services.storage import get_submission, save_submission

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
async def get_clarification_questions(request_id: str):
    """Retrieves current clarification questions and round history for a submission."""
    state = get_submission(request_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{request_id}' not found",
        )

    return ClarificationResponse(
        request_id=request_id,
        status=state.get("status", _determine_status(state)),
        clarification_round=state.get("clarification_round", 0),
        max_rounds=MAX_CLARIFICATION_ROUNDS,
        questions=state.get("clarification_questions", []),
        answers=state.get("clarification_answers", []),
        score=state.get("score"),
        decision=state.get("decision"),
        report_type=state.get("report_type"),
        report=state.get("report"),
    )


@router.post(
    "/{request_id}/clarification",
    response_model=ClarificationResponse,
    summary="Submit answers to clarification questions & re-trigger pipeline",
)
async def submit_clarification_answers(
    request_id: str, payload: ClarificationAnswerInput
):
    """Submits user answers to clarification questions and re-invokes the LangGraph pipeline."""
    state = get_submission(request_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{request_id}' not found",
        )

    curr_decision = state.get("decision")
    curr_status = state.get("status")
    if curr_decision != "NEEDS_CLARIFICATION" and curr_status != "NEEDS_CLARIFICATION":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Submission '{request_id}' does not currently require clarification (status: '{curr_status}', decision: '{curr_decision}')",
        )

    # Append new answers to state
    existing_answers = list(state.get("clarification_answers", []))
    existing_answers.extend(payload.answers)
    state["clarification_answers"] = existing_answers

    # Re-invoke pipeline starting from llm_analyze with updated answers
    graph = get_compiled_graph()
    updated_state = graph.invoke(state)

    status_str = _determine_status(updated_state)
    updated_state["status"] = status_str
    updated_state["request_id"] = request_id

    # Persist updated state
    saved_state = save_submission(request_id, updated_state)

    return ClarificationResponse(
        request_id=request_id,
        status=saved_state.get("status", status_str),
        clarification_round=saved_state.get("clarification_round", 0),
        max_rounds=MAX_CLARIFICATION_ROUNDS,
        questions=saved_state.get("clarification_questions", []),
        answers=saved_state.get("clarification_answers", []),
        score=saved_state.get("score"),
        decision=saved_state.get("decision"),
        report_type=saved_state.get("report_type"),
        report=saved_state.get("report"),
    )
