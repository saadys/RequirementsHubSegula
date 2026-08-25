"""
Submissions API Routes

Handles submitting new AI project requests, running the LangGraph pipeline,
retrieving submission state, and listing submissions via PostgreSQL / SQLAlchemy.
"""

import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import DATA_DIR, MAX_CLARIFICATION_ROUNDS
from backend.graph.builder import get_compiled_graph, get_checkpointer
from backend.models.BaseDataModel import AsyncSessionLocal, get_db
from backend.models.ClarificationModel import ClarificationModel
from backend.models.FactExtractionModel import FactExtractionModel
from backend.models.ReportModel import ReportModel
from backend.models.ScoringModel import ScoringModel
from backend.models.SubmissionModel import SubmissionModel
from backend.models.db_schemes.requirementshub.schemes.submission import Submission
from backend.schemas import Decision, FormSubmission, SubmissionResponse, SubmissionStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/submissions", tags=["Submissions"])


def entity_to_submission_response(sub: Submission) -> SubmissionResponse:
    """Converts a Submission ORM instance and its loaded relations into a SubmissionResponse Pydantic model."""
    scoring = sub.scoring_result
    rep = sub.report
    clar_rounds = sorted(sub.clarification_rounds or [], key=lambda r: r.round_number)
    overrides = sub.reviewer_overrides or []
    fact = sub.fact_extraction

    latest_round = clar_rounds[-1] if clar_rounds else None
    round_num = latest_round.round_number if latest_round else 0
    decision = overrides[0].new_decision if overrides else (scoring.decision if scoring else None)

    # Check if latest clarification round is already answered or completed
    has_answered_latest = bool(latest_round and latest_round.answers and len(latest_round.answers) > 0)
    is_clarification_done = False
    if has_answered_latest and round_num >= MAX_CLARIFICATION_ROUNDS:
        is_clarification_done = True
    elif rep is not None and sub.status in ("COMPLETED", "REJECTED", "FAST_TRACK"):
        is_clarification_done = True

    active_questions = [] if (is_clarification_done or has_answered_latest) else (latest_round.questions if latest_round else [])

    sub_scores = {}
    veto_triggered = False
    veto_reasons = []
    if scoring and scoring.breakdown:
        sub_scores = scoring.breakdown.get("sub_scores") or scoring.breakdown.get("pillar_scores") or {}
        veto_triggered = bool(scoring.breakdown.get("veto_triggered", False))
        veto_reasons = scoring.breakdown.get("veto_reasons") or []

    form_data = {
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

    created_at_str = (
        sub.created_at.isoformat()
        if sub.created_at and hasattr(sub.created_at, "isoformat")
        else (str(sub.created_at) if sub.created_at else None)
    )

    return SubmissionResponse(
        request_id=str(sub.id),
        status=sub.status,
        decision=decision,
        score=scoring.score if scoring else None,
        sub_scores=sub_scores,
        veto_triggered=veto_triggered,
        veto_reasons=veto_reasons,
        report_type=rep.report_type if rep else None,
        missing_fields=(fact.extracted_requirements if (fact and fact.extracted_requirements) else []),
        clarification_questions=active_questions,
        clarification_round=round_num,
        max_rounds=MAX_CLARIFICATION_ROUNDS,
        parsed_files_text=sub.parsed_files_text or [],
        report=rep.content if rep else None,
        created_at=created_at_str,
        form_data=form_data,
    )


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
        if result_state.get("report"):
            return SubmissionStatus.COMPLETED.value
        return SubmissionStatus.NEEDS_CLARIFICATION.value
    return SubmissionStatus.PROCESSED.value


async def _execute_pipeline_in_background(
    request_id: str, form_dict: Dict[str, Any], uploaded_file_paths: List[str], checkpointer
):
    """Executes the compiled LangGraph pipeline asynchronously in a background task.

    thread_id is set to request_id so a later clarification resume (see
    routes_clarification.py) can reach this exact run's paused checkpoint."""
    try:
        initial_state = {
            "request_id": request_id,
            "form_data": form_dict,
            "department": form_dict.get("department", "corporate_support"),
            "uploaded_files": uploaded_file_paths,
            "clarification_round": 0,
            "clarification_answers": [],
        }

        graph = get_compiled_graph(checkpointer)
        result_state = await graph.ainvoke(
            initial_state, config={"configurable": {"thread_id": request_id}}
        )

        status_str = _determine_status(result_state)

        async with AsyncSessionLocal() as db:
            async with db.begin():
                sub_model = SubmissionModel(db)
                fact_model = FactExtractionModel(db)
                scoring_model = ScoringModel(db)
                report_model = ReportModel(db)
                clar_model = ClarificationModel(db)

                if result_state.get("missing_fields"):
                    await sub_model.update_fields(
                        request_id, {"missing_fields": result_state.get("missing_fields") or []}, auto_commit=False
                    )

                if result_state.get("parsed_files_text"):
                    await sub_model.update_fields(
                        request_id, {"parsed_files_text": result_state.get("parsed_files_text") or []}, auto_commit=False
                    )

                if result_state.get("extracted_facts"):
                    facts_payload = dict(result_state.get("extracted_facts") or {})
                    if result_state.get("extracted_facts_model_used"):
                        facts_payload["llm_model_used"] = result_state.get("extracted_facts_model_used")
                    await fact_model.create_or_update(
                        request_id,
                        facts_payload,
                        auto_commit=False,
                    )

                if result_state.get("score") is not None or result_state.get("decision"):
                    sub_scores_val = result_state.get("sub_scores") or {}
                    veto_trig = result_state.get("veto_triggered", False)
                    veto_reasons_val = result_state.get("veto_reasons") or []

                    breakdown_payload = {
                        "sub_scores": sub_scores_val,
                        "veto_triggered": veto_trig,
                        "veto_reasons": veto_reasons_val,
                    }
                    if result_state.get("score_breakdown"):
                        breakdown_payload["legacy_breakdown"] = result_state.get("score_breakdown")

                    await scoring_model.create_or_update(
                        request_id,
                        {
                            "score": result_state.get("score"),
                            "percentage": result_state.get("score"),
                            "decision": result_state.get("decision"),
                            "breakdown": breakdown_payload,
                        },
                        auto_commit=False,
                    )

                if result_state.get("report"):
                    await report_model.create_or_update(
                        request_id,
                        report_type=result_state.get("report_type", "FULL_CAHIER_DES_CHARGES"),
                        content=result_state.get("report"),
                        auto_commit=False,
                    )

                if result_state.get("clarification_questions"):
                    await clar_model.create_round(
                        submission_id=request_id,
                        round_number=result_state.get("clarification_round", 1),
                        questions=result_state.get("clarification_questions", []),
                        answers=result_state.get("clarification_answers", []),
                        llm_model_used=result_state.get("clarification_model_used"),
                        auto_commit=False,
                    )

                # Update status to completed/needs_clarification at the very end after all child records are staged
                await sub_model.update_status(request_id, status_str, auto_commit=False)

        logger.info(f"Background task finished for request {request_id}. Status: {status_str}")
    except Exception as e:
        logger.error(f"Error in background pipeline execution for request {request_id}: {e}")
        try:
            async with AsyncSessionLocal() as db:
                sub_model = SubmissionModel(db)
                await sub_model.update_status(request_id, "FAILED")
        except Exception as db_err:
            logger.error(f"Failed to update status to FAILED in DB for {request_id}: {db_err}")


@router.post(
    "/",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new AI project request (JSON)",
)
async def submit_request(
    submission: FormSubmission,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    checkpointer=Depends(get_checkpointer),
):
    """Submits a new AI project request as JSON, returns PENDING immediately, and executes pipeline in background."""
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

    # Launch pipeline in background task
    background_tasks.add_task(_execute_pipeline_in_background, request_id, form_dict, [], checkpointer)

    sub = await sub_model.get_by_id_with_relations(req_uuid)
    return entity_to_submission_response(sub or sub_entity)


@router.post(
    "/upload",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit request with uploaded PDF files (Multipart Form Data)",
)
async def submit_request_with_files(
    background_tasks: BackgroundTasks,
    form_data_json: str = Form(
        ..., description="JSON string matching FormSubmission schema"
    ),
    files: List[UploadFile] = File(
        None, description="Uploaded PDF files (Choose Files)"
    ),
    file: UploadFile = File(
        None, description="Single PDF file upload (Choose File)"
    ),
    db: AsyncSession = Depends(get_db),
    checkpointer=Depends(get_checkpointer),
):
    """Submits form data along with uploaded files, returns PENDING immediately, and parses in background."""
    try:
        raw_dict = json.loads(form_data_json)
        submission = FormSubmission(**raw_dict)
        form_dict = submission.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid form_data_json format: {str(e)}",
        )

    file_list: List[UploadFile] = []
    if file is not None:
        file_list.append(file)
    if files:
        file_list.extend(files)

    req_uuid = uuid.uuid4()
    request_id = str(req_uuid)
    upload_dir = os.path.join(DATA_DIR, "uploads", request_id)
    try:
        os.makedirs(upload_dir, exist_ok=True)
    except PermissionError:
        upload_dir = os.path.join("/tmp", "uploads", request_id)
        os.makedirs(upload_dir, exist_ok=True)

    saved_paths = []
    for upload in file_list:
        if upload and upload.filename:
            file_path = os.path.join(upload_dir, upload.filename)
            content = await upload.read()
            with open(file_path, "wb") as f:
                f.write(content)
            saved_paths.append(file_path)

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

    # Launch pipeline in background task
    background_tasks.add_task(_execute_pipeline_in_background, request_id, form_dict, saved_paths, checkpointer)

    sub = await sub_model.get_by_id_with_relations(req_uuid)
    return entity_to_submission_response(sub or sub_entity)


@router.get(
    "/",
    response_model=List[SubmissionResponse],
    summary="List all submissions with optional filters",
)
async def get_all_submissions(
    department: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Lists all submissions. Filter by department or status (e.g. GO, NEEDS_CLARIFICATION, REJECTED, FAST_TRACK)."""
    sub_model = SubmissionModel(db)
    items = await sub_model.get_all_with_relations(status_filter=status)
    if department:
        items = [s for s in items if s.department_id == department]

    responses = [entity_to_submission_response(item) for item in items]
    return responses


@router.get(
    "/{request_id}",
    response_model=SubmissionResponse,
    summary="Get submission details by request_id",
)
async def get_submission_by_id(request_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves full details and status of a submission by request_id."""
    sub_model = SubmissionModel(db)
    sub = await sub_model.get_by_id_with_relations(request_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{request_id}' not found",
        )

    return entity_to_submission_response(sub)
