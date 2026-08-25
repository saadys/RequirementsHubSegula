"""
Clarification API Routes

Handles multi-turn clarification loops for submissions requiring additional context via PostgreSQL / SQLAlchemy.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from langgraph.types import Command
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import MAX_CLARIFICATION_ROUNDS
from backend.domain.status_policy import resolve_submission_status
from backend.graph.builder import get_compiled_graph, get_checkpointer
from backend.mappers.submission_mapper import build_clarification_response
from backend.models.BaseDataModel import get_db
from backend.models.ClarificationModel import ClarificationModel
from backend.models.FactExtractionModel import FactExtractionModel
from backend.models.ReportModel import ReportModel
from backend.models.ScoringModel import ScoringModel
from backend.models.SubmissionModel import SubmissionModel
from backend.schemas import ClarificationAnswerInput, ClarificationResponse, SubmissionStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/submissions", tags=["Clarification"])


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

    return build_clarification_response(sub)


@router.post(
    "/{request_id}/clarification",
    response_model=ClarificationResponse,
    summary="Submit answers to clarification questions & re-trigger pipeline",
)
async def submit_clarification_answers(
    request_id: str,
    payload: ClarificationAnswerInput,
    db: AsyncSession = Depends(get_db),
    checkpointer=Depends(get_checkpointer),
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
    rounds = sorted(sub.clarification_rounds or [], key=lambda r: r.round_number)
    latest_round = rounds[-1] if rounds else None
    curr_round_num = latest_round.round_number if latest_round else 1

    if latest_round and latest_round.round_number >= MAX_CLARIFICATION_ROUNDS and latest_round.answers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Clarification rounds ({MAX_CLARIFICATION_ROUNDS}/{MAX_CLARIFICATION_ROUNDS}) have already been completed for this submission.",
        )

    if latest_round:
        await clar_model.update_answers(request_id, curr_round_num, payload.answers)
    else:
        await clar_model.create_round(request_id, round_number=1, questions=[], answers=payload.answers)

    # Collect all historical questions and answers across rounds
    all_questions = []
    all_answers = []
    for r in rounds:
        r_q = r.questions or []
        r_a = payload.answers if r.round_number == curr_round_num else (r.answers or [])
        all_questions.extend(r_q)
        all_answers.extend(r_a)

    graph = get_compiled_graph(checkpointer)
    run_config = {"configurable": {"thread_id": request_id}}

    # Resume the paused graph in-place (no re-run of parse_input/rag_search/llm_analyze)
    # ONLY if a checkpoint actually exists for this thread_id — e.g. the submission
    # was created before this checkpointer was deployed, or (in tests) the
    # NEEDS_CLARIFICATION state was seeded directly in the DB without ever running
    # the graph. In that case there is nothing to resume, so fall back to the old
    # behavior: reconstruct the state from the DB and run the graph from START.
    # graph.aget_state() raises ValueError outright (not an empty snapshot) when the
    # graph was compiled with no checkpointer at all, so check that first.
    if checkpointer is None:
        can_resume = False
    else:
        existing_snapshot = await graph.aget_state(run_config)
        can_resume = bool(existing_snapshot.values) and bool(existing_snapshot.next)

    if can_resume:
        updated_state = await graph.ainvoke(Command(resume=payload.answers), run_config)
    else:
        logger.warning(
            "No resumable checkpoint for submission %s — falling back to full pipeline re-run.",
            request_id,
        )
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
            "uploaded_files": [],
            "parsed_files_text": sub.parsed_files_text or [],
            "clarification_round": curr_round_num,
            "clarification_answers": all_answers,
            "clarification_questions": all_questions,
        }
        updated_state = await graph.ainvoke(state, run_config)

    status_str = resolve_submission_status(updated_state)
    await sub_model.update_status(request_id, status_str)

    if updated_state.get("extracted_facts"):
        fact_model = FactExtractionModel(db)
        facts_payload = dict(updated_state.get("extracted_facts") or {})
        if updated_state.get("extracted_facts_model_used"):
            facts_payload["llm_model_used"] = updated_state.get("extracted_facts_model_used")
        await fact_model.create_or_update(
            request_id,
            facts_payload,
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
                llm_model_used=updated_state.get("clarification_model_used"),
            )

    refreshed_sub = await sub_model.get_by_id_with_relations(request_id)

    # Re-read through the shared mapper rather than re-deriving the projection
    # here. Two behaviours change on purpose versus the previous inline block:
    #   * rounds are sorted before picking the latest one (the GET handler always
    #     sorted; this one did not, so an out-of-order fetch could surface a stale
    #     round),
    #   * a reviewer override now wins over the pipeline decision, matching the
    #     GET handler. Returning the raw scoring decision here meant POST and GET
    #     could report different decisions for the same overridden submission.
    return build_clarification_response(refreshed_sub)
