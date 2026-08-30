"""
Submissions SSE Streaming API Routes

Provides real-time Server-Sent Events (SSE) for pipeline execution progress,
fact analysis, scoring decisions, and token-by-token report streaming.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend import config
from backend.contracts.state import PipelineState
from backend.domain.status_policy import resolve_submission_status
from backend.models.BaseDataModel import AsyncSessionLocal, get_db
from backend.models.ClarificationModel import ClarificationModel
from backend.models.FactExtractionModel import FactExtractionModel
from backend.models.ReportModel import ReportModel
from backend.models.ScoringModel import ScoringModel
from backend.models.SubmissionModel import SubmissionModel
from backend.models.db_schemes.requirementshub.schemes.submission import Submission
from backend.nodes.deterministic_score import deterministic_score
from backend.nodes.fast_track import fast_track
from backend.nodes.generate_questions import generate_questions, stream_generate_questions
from backend.nodes.generate_report import (
    build_static_report_markdown,
    generate_report,
    get_feedback_prompts,
)
from backend.nodes.llm_analyze import llm_analyze, stream_llm_analyze
from backend.nodes.parse_input import parse_input
from backend.nodes.rag_search import rag_search
from backend.nodes.validate_completeness import validate_completeness
from backend.schemas import ClarificationAnswerInput, Decision, FormSubmission, SubmissionStatus
from backend.services.llm import get_streaming_llm
from backend.services.queue_manager import queue_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/submissions", tags=["Streaming"])


def _sse_pack(event_name: str, payload: dict) -> str:
    """Formats payload as standard Server-Sent Event (SSE)."""
    return f"event: {event_name}\ndata: {json.dumps(payload)}\n\n"


async def _save_pipeline_state_to_db(request_id: str, state: PipelineState, final_status: str):
    """Persists pipeline state, facts, scores, report, and clarifications to PostgreSQL atomically."""
    async with AsyncSessionLocal() as db:
        async with db.begin():
            sub_model = SubmissionModel(db)
            fact_model = FactExtractionModel(db)
            scoring_model = ScoringModel(db)
            report_model = ReportModel(db)
            clar_model = ClarificationModel(db)

            if state.get("parsed_files_text"):
                await sub_model.update_fields(
                    request_id, {"parsed_files_text": state.get("parsed_files_text") or []}, auto_commit=False
                )

            if state.get("extracted_facts"):
                facts_payload = dict(state.get("extracted_facts") or {})
                if state.get("extracted_facts_model_used"):
                    facts_payload["llm_model_used"] = state.get("extracted_facts_model_used")
                await fact_model.create_or_update(
                    request_id,
                    facts_payload,
                    auto_commit=False,
                )

            if state.get("score") is not None or state.get("decision"):
                sub_scores_val = state.get("sub_scores") or {}
                veto_trig = state.get("veto_triggered", False)
                veto_reasons_val = state.get("veto_reasons") or []

                breakdown_payload = {
                    "sub_scores": sub_scores_val,
                    "veto_triggered": veto_trig,
                    "veto_reasons": veto_reasons_val,
                }
                if state.get("score_breakdown"):
                    breakdown_payload["legacy_breakdown"] = state["score_breakdown"]

                await scoring_model.create_or_update(
                    request_id,
                    {
                        "score": state.get("score"),
                        "percentage": state.get("score"),
                        "decision": state.get("decision"),
                        "breakdown": breakdown_payload,
                    },
                    auto_commit=False,
                )

            if state.get("report"):
                report_type_val = state.get("report_type") or (
                    "fast_track"
                    if state.get("is_exact_match")
                    else ("go" if state.get("decision") in ("GO", "FAST_TRACK") else "no_go")
                )
                await report_model.create_or_update(
                    request_id,
                    report_type=report_type_val,
                    content=state.get("report") or "",
                    auto_commit=False,
                )

            if state.get("clarification_questions") and final_status == SubmissionStatus.NEEDS_CLARIFICATION.value:
                round_num = state.get("clarification_round", 1)
                await clar_model.create_or_update(
                    request_id,
                    round_number=round_num,
                    questions=state.get("clarification_questions") or [],
                    answers=[],
                    llm_model_used=state.get("clarification_model_used"),
                    auto_commit=False,
                )

            await sub_model.update_status(request_id, final_status, auto_commit=False)


async def _stream_pipeline_execution(
    request_id: str, form_dict: Dict[str, Any]
) -> AsyncGenerator[str, None]:
    """
    Step-by-step pipeline generator that yields SSE events for node progress,
    scoring, thinking processes, and streamed report tokens.
    """
    state: PipelineState = {
        "request_id": request_id,
        "form_data": form_dict,
        "department": form_dict.get("department", "corporate_support"),
        "uploaded_files": [],
        "clarification_round": 0,
        "clarification_answers": [],
    }

    try:
        # ── 0. Concurrency Queue Slot Acquisition ───────────────────
        async for queue_event in queue_manager.acquire_slot(request_id):
            yield _sse_pack("queue_status", queue_event)
            if queue_event.get("status") == "QUEUE_FULL":
                yield _sse_pack("error", {"message": queue_event.get("message", "Server queue is full")})
                return
            if queue_event.get("status") == "PROCESSING":
                break

        # ── 1. parse_input ──────────────────────────────────────────
        yield _sse_pack("node", {"node": "parse_input", "status": "running"})
        t0 = time.perf_counter()
        parse_res = parse_input(state)
        state.update(parse_res)
        d_ms = round((time.perf_counter() - t0) * 1000, 1)
        yield _sse_pack(
            "node",
            {
                "node": "parse_input",
                "status": "complete",
                "duration_ms": d_ms,
                "project_name": form_dict.get("project_name", ""),
            },
        )

        # ── 2. validate_completeness ────────────────────────────────
        yield _sse_pack("node", {"node": "validate_completeness", "status": "running"})
        t0 = time.perf_counter()
        val_res = validate_completeness(state)
        state.update(val_res)
        d_ms = round((time.perf_counter() - t0) * 1000, 1)
        missing = state.get("missing_fields", [])
        yield _sse_pack(
            "node",
            {
                "node": "validate_completeness",
                "status": "complete",
                "duration_ms": d_ms,
                "missing_fields": missing,
                "is_complete": len(missing) == 0,
            },
        )

        if missing:
            final_status = SubmissionStatus.INCOMPLETE.value
            await _save_pipeline_state_to_db(request_id, state, final_status)
            yield _sse_pack(
                "complete",
                {
                    "request_id": request_id,
                    "status": final_status,
                    "missing_fields": missing,
                },
            )
            return

        # ── 3. rag_search ───────────────────────────────────────────
        yield _sse_pack("node", {"node": "rag_search", "status": "running"})
        t0 = time.perf_counter()
        rag_res = await rag_search(state)
        state.update(rag_res)
        d_ms = round((time.perf_counter() - t0) * 1000, 1)

        similar_projs = state.get("similar_projects", []) or []
        rag_scores = state.get("rag_scores", []) or []
        max_rag = round(max(rag_scores), 3) if rag_scores else 0.0
        is_exact = bool(state.get("is_exact_match", False))

        yield _sse_pack(
            "node",
            {
                "node": "rag_search",
                "status": "complete",
                "duration_ms": d_ms,
                "matches_found": len(similar_projs),
                "top_similarity": max_rag,
                "is_exact_match": is_exact,
            },
        )

        # Fast Track Path
        if is_exact:
            yield _sse_pack("node", {"node": "fast_track", "status": "running"})
            ft_res = fast_track(state)
            state.update(ft_res)
            yield _sse_pack("node", {"node": "fast_track", "status": "complete"})
            yield _sse_pack(
                "score",
                {
                    "score": state.get("score", 95),
                    "decision": state.get("decision", "FAST_TRACK"),
                    "sub_scores": state.get("sub_scores", {}),
                    "veto_triggered": False,
                    "veto_reasons": [],
                },
            )
            yield _sse_pack("token", {"content": state.get("report", "")})
            final_status = SubmissionStatus.FAST_TRACK.value
            await _save_pipeline_state_to_db(request_id, state, final_status)
            yield _sse_pack(
                "complete",
                {
                    "request_id": request_id,
                    "status": final_status,
                    "decision": "FAST_TRACK",
                    "score": 95,
                },
            )
            return

        # ── 4. llm_analyze (5-Pillar Fact Extraction) ───────────────
        yield _sse_pack("node", {"node": "llm_analyze", "status": "running"})
        t0 = time.perf_counter()
        try:
            async for item in stream_llm_analyze(state):
                if item.get("type") == "thinking":
                    yield _sse_pack("thinking", {"content": item.get("content", "")})
                elif item.get("type") == "result":
                    state.update(item.get("data", {}))
        except Exception as e:
            logger.error("Error during stream_llm_analyze: %s", e)
            analyze_res = await llm_analyze(state)
            state.update(analyze_res)

        d_ms = round((time.perf_counter() - t0) * 1000, 1)

        extracted = state.get("extracted_facts", {}) or {}
        summary_txt = extracted.get("project_summary", "")
        yield _sse_pack(
            "node",
            {
                "node": "llm_analyze",
                "status": "complete",
                "duration_ms": d_ms,
                "summary": summary_txt,
            },
        )

        # ── 5. deterministic_score ──────────────────────────────────
        yield _sse_pack("node", {"node": "deterministic_score", "status": "running"})
        t0 = time.perf_counter()
        score_res = deterministic_score(state)
        state.update(score_res)
        d_ms = round((time.perf_counter() - t0) * 1000, 1)

        decision = str(state.get("decision", "NO_GO")).upper()
        score_val = state.get("score", 0)
        sub_scores = state.get("sub_scores", {})
        veto_trig = state.get("veto_triggered", False)
        veto_reasons = state.get("veto_reasons", [])

        yield _sse_pack(
            "node",
            {"node": "deterministic_score", "status": "complete", "duration_ms": d_ms},
        )
        yield _sse_pack(
            "score",
            {
                "score": score_val,
                "decision": decision,
                "sub_scores": sub_scores,
                "veto_triggered": veto_trig,
                "veto_reasons": veto_reasons,
            },
        )

        # ── 6. Branch: Clarification or Report Generation ───────────
        max_clarification_rounds = getattr(config, "MAX_CLARIFICATION_ROUNDS", 2)
        clarification_round = state.get("clarification_round", 0)

        if decision == Decision.NEEDS_CLARIFICATION.value and clarification_round < max_clarification_rounds:
            yield _sse_pack("node", {"node": "generate_questions", "status": "running"})
            t0 = time.perf_counter()
            try:
                async for item in stream_generate_questions(state):
                    if item.get("type") == "thinking":
                        yield _sse_pack("thinking", {"content": item.get("content", "")})
                    elif item.get("type") == "result":
                        state.update(item.get("data", {}))
            except Exception as e:
                logger.error("Error during stream_generate_questions: %s", e)
                q_fallback = await generate_questions(state)
                state.update(q_fallback)

            d_ms = round((time.perf_counter() - t0) * 1000, 1)

            questions = state.get("clarification_questions", [])
            yield _sse_pack(
                "node",
                {"node": "generate_questions", "status": "complete", "duration_ms": d_ms},
            )
            yield _sse_pack(
                "clarification",
                {
                    "questions": questions,
                    "round": state.get("clarification_round", 1),
                    "max_rounds": max_clarification_rounds,
                },
            )
            final_status = SubmissionStatus.NEEDS_CLARIFICATION.value
            await _save_pipeline_state_to_db(request_id, state, final_status)
            yield _sse_pack(
                "complete",
                {
                    "request_id": request_id,
                    "status": final_status,
                    "decision": decision,
                    "score": score_val,
                    "sub_scores": sub_scores,
                    "veto_triggered": veto_trig,
                    "veto_reasons": veto_reasons,
                    "clarification_questions": questions,
                    "clarification_round": state.get("clarification_round", 1),
                    "max_rounds": max_clarification_rounds,
                },
            )
            return

        # Report Generation with live token streaming
        yield _sse_pack("node", {"node": "generate_report", "status": "running"})
        static_report = build_static_report_markdown(state)
        # Yield the structured 5-pillar dossier header
        yield _sse_pack("token", {"content": static_report})

        full_report = static_report
        report_type = "go" if decision in ["GO", "FAST_TRACK"] else ("no_go" if decision == "NO_GO" else "partial")

        # Stream AI Architect Feedback for NO_GO or stalled evaluations
        if decision in ["NO_GO", "NEEDS_CLARIFICATION"]:
            section_header = "\n---\n\n### 🧠 AI Architect Feedback & Actionable Next Steps:\n\n"
            yield _sse_pack("token", {"content": section_header})
            full_report += section_header

            system_prompt, user_content = get_feedback_prompts(state)
            streaming_llm = get_streaming_llm(temperature=0.7)

            feedback_accumulated = ""
            try:
                # Stream feedback tokens one by one
                async for chunk_event in streaming_llm.generate_text_stream(
                    prompt=user_content,
                    system_prompt=system_prompt,
                    temperature=0.7,
                ):
                    event_type = chunk_event.get("type", "token")
                    content = chunk_event.get("content", "")
                    if event_type == "thinking":
                        yield _sse_pack("thinking", {"content": content})
                    else:
                        yield _sse_pack("token", {"content": content})
                        feedback_accumulated += content
                    # Allow event loop yield to flush SSE chunks
                    await asyncio.sleep(0)
            except Exception as stream_err:
                logger.error("Streaming feedback failed (%s); using fallback notice", stream_err)
                fallback_msg = "Please review the 5-pillar breakdown and veto alerts above to address the bottlenecks in your project data or scope."
                yield _sse_pack("token", {"content": fallback_msg})
                feedback_accumulated += fallback_msg

            full_report += feedback_accumulated

        state["report"] = full_report
        state["report_type"] = report_type

        yield _sse_pack("node", {"node": "generate_report", "status": "complete"})

        final_status = resolve_submission_status(state)
        await _save_pipeline_state_to_db(request_id, state, final_status)

        yield _sse_pack(
            "complete",
            {
                "request_id": request_id,
                "status": final_status,
                "decision": decision,
                "score": score_val,
            },
        )

    except Exception as e:
        logger.exception("Error during SSE streaming pipeline execution: %s", e)
        yield _sse_pack("error", {"message": f"Pipeline execution failed: {str(e)}"})
        async with AsyncSessionLocal() as db:
            sub_model = SubmissionModel(db)
            await sub_model.update_status(request_id, "FAILED")
    finally:
        await queue_manager.release_slot(request_id)


@router.post(
    "/stream",
    summary="Submit AI project request with real-time SSE streaming",
)
async def submit_request_stream(
    submission: FormSubmission,
    db: AsyncSession = Depends(get_db),
):
    """
    Submits a new AI project requirement and initiates an SSE (Server-Sent Events)
    stream that outputs pipeline node events, scores, thinking steps, and live tokens.
    """
    form_dict = submission.model_dump()
    req_uuid = uuid.uuid4()
    request_id = str(req_uuid)

    sub_model = SubmissionModel(db)
    sub_entity = Submission(
        id=req_uuid,
        project_name=submission.project_name,
        department_id=submission.department or "corporate_support",
        team_contact_name=submission.team_contact_name,
        team_contact_email=submission.team_contact_email,
        problem_description=submission.problem_description,
        current_process=submission.current_process,
        expected_outcome=submission.expected_outcome,
        data_description=submission.data_description,
        deadline_urgency=submission.deadline_urgency or "low",
        department_specific=submission.department_specific or {},
        status=SubmissionStatus.PENDING.value,
    )
    await sub_model.create_submission(sub_entity)

    return StreamingResponse(
        _stream_pipeline_execution(request_id, form_dict),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/submit-async",
    summary="Fast non-blocking submission with instant queue assignment (avoids browser connection limits)",
)
async def submit_request_async(
    submission: FormSubmission,
    db: AsyncSession = Depends(get_db),
):
    """Instantly registers a submission in database and queue without holding open HTTP connections."""
    form_dict = submission.model_dump()
    req_uuid = uuid.uuid4()
    request_id = str(req_uuid)

    sub_model = SubmissionModel(db)
    sub_entity = Submission(
        id=req_uuid,
        project_name=submission.project_name,
        department_id=submission.department or "corporate_support",
        team_contact_name=submission.team_contact_name,
        team_contact_email=submission.team_contact_email,
        problem_description=submission.problem_description,
        current_process=submission.current_process,
        expected_outcome=submission.expected_outcome,
        data_description=submission.data_description,
        deadline_urgency=submission.deadline_urgency or "low",
        department_specific=submission.department_specific or {},
        status=SubmissionStatus.PENDING.value,
    )
    await sub_model.create_submission(sub_entity)

    queue_info = await queue_manager.register_submission(request_id)
    return {
        "request_id": request_id,
        "status": queue_info.get("status"),
        "queue": queue_info,
    }


@router.get(
    "/{request_id}/queue-status",
    summary="Check real-time queue position for a submitted requirement",
)
async def get_queue_status(request_id: str):
    """Returns current position and estimated remaining seconds in queue."""
    return await queue_manager.get_request_status(request_id)


@router.get(
    "/{request_id}/stream",
    summary="Stream pipeline execution for an already registered submission",
)
async def stream_registered_submission(
    request_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Initiates live SSE streaming pipeline for a registered request whose slot is ready."""
    sub_model = SubmissionModel(db)
    sub = await sub_model.get_by_id(request_id)
    if not sub:
        raise HTTPException(status_code=404, detail=f"Submission '{request_id}' not found")

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

    return StreamingResponse(
        _stream_pipeline_execution(request_id, form_dict),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _stream_clarification_execution(
    request_id: str, payload_answers: List[str]
) -> AsyncGenerator[str, None]:
    """
    Step-by-step pipeline generator that yields SSE events for clarification
    re-evaluation, fact re-extraction, score recalculation, and report streaming.
    """
    loop = asyncio.get_running_loop()
    try:
        # ── 0. Concurrency Queue Slot Acquisition ───────────────────
        async for queue_event in queue_manager.acquire_slot(request_id):
            yield _sse_pack("queue_status", queue_event)
            if queue_event.get("status") == "QUEUE_FULL":
                yield _sse_pack("error", {"message": queue_event.get("message", "Server queue is full")})
                return
            if queue_event.get("status") == "PROCESSING":
                break

        async with AsyncSessionLocal() as db:
            sub_model = SubmissionModel(db)
            sub = await sub_model.get_by_id_with_relations(request_id)
            if not sub:
                yield _sse_pack("error", {"message": f"Submission '{request_id}' not found"})
                return

            clar_model = ClarificationModel(db)
            rounds = sorted(sub.clarification_rounds or [], key=lambda r: r.round_number)
            latest_round = rounds[-1] if rounds else None
            curr_round_num = latest_round.round_number if latest_round else 1

            if latest_round:
                await clar_model.update_answers(request_id, curr_round_num, payload_answers)
            else:
                await clar_model.create_round(request_id, round_number=1, questions=[], answers=payload_answers)

            # Build aggregated historical Q&A context across all rounds for LLM prompt
            all_questions = []
            all_answers = []
            for r in rounds:
                r_q = r.questions or []
                r_a = payload_answers if r.round_number == curr_round_num else (r.answers or [])
                all_questions.extend(r_q)
                all_answers.extend(r_a)

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

            state: PipelineState = {
                "request_id": request_id,
                "form_data": form_dict,
                "department": sub.department_id or "corporate_support",
                "uploaded_files": [],
                "parsed_files_text": sub.parsed_files_text or [],
                "clarification_round": curr_round_num,
                "clarification_answers": all_answers,
                "clarification_questions": all_questions,
            }

        # ── 1. Ingestion of Clarification Responses ───
        yield _sse_pack("node", {"node": "parse_input", "status": "running"})
        t0 = time.perf_counter()
        parsed_res = parse_input(state)
        state.update(parsed_res)
        d_ms = round((time.perf_counter() - t0) * 1000, 1)
        yield _sse_pack("node", {"node": "parse_input", "status": "complete", "duration_ms": d_ms})

        # ── 2. Department Schema Check ───────────────
        yield _sse_pack("node", {"node": "validate_completeness", "status": "running"})
        t0 = time.perf_counter()
        val_res = validate_completeness(state)
        state.update(val_res)
        d_ms = round((time.perf_counter() - t0) * 1000, 1)
        yield _sse_pack("node", {"node": "validate_completeness", "status": "complete", "duration_ms": d_ms})

        # ── 3. RAG Search ────────────────────────────
        yield _sse_pack("node", {"node": "rag_search", "status": "running"})
        t0 = time.perf_counter()
        rag_res = await rag_search(state)
        state.update(rag_res)
        d_ms = round((time.perf_counter() - t0) * 1000, 1)
        yield _sse_pack(
            "node",
            {
                "node": "rag_search",
                "status": "complete",
                "duration_ms": d_ms,
                "matches_found": len(state.get("similar_projects", [])),
                "top_similarity": state.get("top_similarity_score", 0.0),
            },
        )

        # ── 4. 5-Pillar Fact Extraction with Clarification Context ───
        yield _sse_pack("node", {"node": "llm_analyze", "status": "running"})
        t0 = time.perf_counter()
        try:
            async for item in stream_llm_analyze(state):
                if item.get("type") == "thinking":
                    yield _sse_pack("thinking", {"content": item.get("content", "")})
                elif item.get("type") == "result":
                    state.update(item.get("data", {}))
        except Exception as e:
            logger.error("Error during clarification stream_llm_analyze: %s", e)
            llm_res = await llm_analyze(state)
            state.update(llm_res)

        d_ms = round((time.perf_counter() - t0) * 1000, 1)
        yield _sse_pack("node", {"node": "llm_analyze", "status": "complete", "duration_ms": d_ms})

        # ── 5. Deterministic Scoring ─────────────────
        yield _sse_pack("node", {"node": "deterministic_score", "status": "running"})
        t0 = time.perf_counter()
        score_res = deterministic_score(state)
        state.update(score_res)
        d_ms = round((time.perf_counter() - t0) * 1000, 1)
        yield _sse_pack("node", {"node": "deterministic_score", "status": "complete", "duration_ms": d_ms})

        score_val = state.get("score")
        decision = state.get("decision")
        sub_scores = state.get("sub_scores", {})
        veto_trig = state.get("veto_triggered", False)
        veto_reasons = state.get("veto_reasons", [])

        yield _sse_pack(
            "score",
            {
                "score": score_val,
                "decision": decision,
                "sub_scores": sub_scores,
                "veto_triggered": veto_trig,
                "veto_reasons": veto_reasons,
            },
        )

        # ── 6. Branch: Second Clarification or Report Generation ─────
        max_clarification_rounds = getattr(config, "MAX_CLARIFICATION_ROUNDS", 2)
        clarification_round = curr_round_num

        if decision == Decision.NEEDS_CLARIFICATION.value and clarification_round < max_clarification_rounds:
            yield _sse_pack("node", {"node": "generate_questions", "status": "running"})
            t0 = time.perf_counter()
            try:
                async for item in stream_generate_questions(state):
                    if item.get("type") == "thinking":
                        yield _sse_pack("thinking", {"content": item.get("content", "")})
                    elif item.get("type") == "result":
                        state.update(item.get("data", {}))
            except Exception as e:
                logger.error("Error during stream_generate_questions (round 2): %s", e)
                q_fallback = await generate_questions(state)
                state.update(q_fallback)

            d_ms = round((time.perf_counter() - t0) * 1000, 1)

            questions = state.get("clarification_questions", [])
            new_round_num = clarification_round + 1
            state["clarification_round"] = new_round_num

            yield _sse_pack(
                "node",
                {"node": "generate_questions", "status": "complete", "duration_ms": d_ms},
            )
            yield _sse_pack(
                "clarification",
                {
                    "questions": questions,
                    "round": new_round_num,
                    "max_rounds": max_clarification_rounds,
                },
            )
            final_status = SubmissionStatus.NEEDS_CLARIFICATION.value
            await _save_pipeline_state_to_db(request_id, state, final_status)
            yield _sse_pack(
                "complete",
                {
                    "request_id": request_id,
                    "status": final_status,
                    "decision": decision,
                    "score": score_val,
                    "sub_scores": sub_scores,
                    "veto_triggered": veto_trig,
                    "veto_reasons": veto_reasons,
                    "clarification_questions": questions,
                    "clarification_round": new_round_num,
                    "max_rounds": max_clarification_rounds,
                },
            )
            return

        # ── 7. Generate Feasibility Dossier & Advice ──────────
        yield _sse_pack("node", {"node": "generate_report", "status": "running"})
        static_report = build_static_report_markdown(state)
        yield _sse_pack("token", {"content": static_report})

        full_report = static_report
        report_type = "go" if decision in ["GO", "FAST_TRACK"] else ("no_go" if decision == "NO_GO" else "partial")

        if decision in ["NO_GO", "NEEDS_CLARIFICATION"]:
            section_header = "\n---\n\n### 🧠 AI Architect Feedback & Actionable Next Steps:\n\n"
            yield _sse_pack("token", {"content": section_header})
            full_report += section_header

            system_prompt, user_content = get_feedback_prompts(state)
            streaming_llm = get_streaming_llm(temperature=0.7)

            feedback_accumulated = ""
            try:
                async for chunk_event in streaming_llm.generate_text_stream(
                    prompt=user_content,
                    system_prompt=system_prompt,
                    temperature=0.7,
                ):
                    event_type = chunk_event.get("type", "token")
                    content = chunk_event.get("content", "")
                    if event_type == "thinking":
                        yield _sse_pack("thinking", {"content": content})
                    else:
                        yield _sse_pack("token", {"content": content})
                        feedback_accumulated += content
                    await asyncio.sleep(0)
            except Exception as stream_err:
                logger.error("Streaming feedback failed (%s); using fallback notice", stream_err)
                fallback_msg = "Please review the 5-pillar breakdown and veto alerts above to address the bottlenecks in your project data or scope."
                yield _sse_pack("token", {"content": fallback_msg})
                feedback_accumulated += fallback_msg

            full_report += feedback_accumulated

        state["report"] = full_report
        state["report_type"] = report_type

        yield _sse_pack("node", {"node": "generate_report", "status": "complete"})

        final_status = resolve_submission_status(state)
        await _save_pipeline_state_to_db(request_id, state, final_status)

        yield _sse_pack(
            "complete",
            {
                "request_id": request_id,
                "status": final_status,
                "decision": decision,
                "score": score_val,
                "sub_scores": sub_scores,
                "veto_triggered": veto_trig,
                "veto_reasons": veto_reasons,
                "report": full_report,
            },
        )

    except Exception as e:
        logger.exception("Error during SSE streaming clarification re-evaluation: %s", e)
        yield _sse_pack("error", {"message": f"Clarification re-evaluation failed: {str(e)}"})
        async with AsyncSessionLocal() as db:
            sub_model = SubmissionModel(db)
            await sub_model.update_status(request_id, "FAILED")
    finally:
        await queue_manager.release_slot(request_id)


@router.post(
    "/{request_id}/clarification/stream",
    summary="Submit clarification answers with real-time SSE streaming re-evaluation",
)
async def submit_clarification_stream(
    request_id: str,
    payload: ClarificationAnswerInput,
    db: AsyncSession = Depends(get_db),
):
    """
    Submits answers to clarification questions and initiates a real-time SSE stream
    for pipeline re-evaluation (fact re-extraction, score recalculation, report streaming).
    """
    sub_model = SubmissionModel(db)
    sub = await sub_model.get_by_id_with_relations(request_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{request_id}' not found",
        )

    return StreamingResponse(
        _stream_clarification_execution(request_id, payload.answers),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

