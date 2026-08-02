"""
Submissions API Routes

Handles submitting new AI project requests, running the LangGraph pipeline,
retrieving submission state, and listing submissions.
"""

import json
import os
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from backend.config import DATA_DIR
from backend.contracts.schemas import FormSubmission
from backend.graph.builder import get_compiled_graph
from backend.services.storage import (
    get_submission,
    list_submissions,
    save_submission,
)

router = APIRouter(prefix="/submissions", tags=["Submissions"])


class SubmissionResponse(BaseModel):
    request_id: str
    status: str
    decision: Optional[str] = None
    score: Optional[int] = None
    report_type: Optional[str] = None
    missing_fields: List[str] = []
    clarification_questions: List[str] = []
    parsed_files_text: List[str] = []
    report: Optional[str] = None
    created_at: Optional[str] = None
    form_data: Dict[str, Any] = {}


def _determine_status(result_state: Dict[str, Any]) -> str:
    """Derives overall user-facing status from pipeline result state."""
    if result_state.get("missing_fields"):
        return "INCOMPLETE"
    if result_state.get("is_exact_match"):
        return "FAST_TRACK"
    decision = result_state.get("decision")
    if decision == "GO":
        return "COMPLETED"
    elif decision == "NO_GO":
        return "REJECTED"
    elif decision == "NEEDS_CLARIFICATION":
        return "NEEDS_CLARIFICATION"
    return "PROCESSED"


def _run_pipeline(
    form_dict: Dict[str, Any], uploaded_file_paths: List[str]
) -> Dict[str, Any]:
    """Executes the compiled LangGraph pipeline for a submission."""
    request_id = str(uuid.uuid4())
    initial_state = {
        "request_id": request_id,
        "form_data": form_dict,
        "department": form_dict.get("department", "corporate_support"),
        "uploaded_files": uploaded_file_paths,
        "clarification_round": 0,
        "clarification_answers": [],
    }

    graph = get_compiled_graph()
    result_state = graph.invoke(initial_state)

    status_str = _determine_status(result_state)
    result_state["status"] = status_str
    result_state["request_id"] = request_id

    # Persist in storage
    saved_state = save_submission(request_id, result_state)
    return saved_state


@router.post(
    "/",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new AI project request (JSON)",
)
async def submit_request(submission: FormSubmission):
    """Submits a new AI project request as JSON, runs the LangGraph pipeline, and returns results."""
    form_dict = submission.model_dump()
    saved_state = _run_pipeline(form_dict, uploaded_file_paths=[])

    return SubmissionResponse(
        request_id=saved_state["request_id"],
        status=saved_state.get("status", "PROCESSED"),
        decision=saved_state.get("decision"),
        score=saved_state.get("score"),
        report_type=saved_state.get("report_type"),
        missing_fields=saved_state.get("missing_fields", []),
        clarification_questions=saved_state.get("clarification_questions", []),
        parsed_files_text=saved_state.get("parsed_files_text", []),
        report=saved_state.get("report"),
        created_at=saved_state.get("created_at"),
        form_data=saved_state.get("form_data", {}),
    )


@router.post(
    "/upload",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit request with uploaded PDF files (Multipart Form Data)",
)
async def submit_request_with_files(
    form_data_json: str = Form(
        ..., description="JSON string matching FormSubmission schema"
    ),
    files: List[UploadFile] = File(
        None, description="Uploaded PDF files (Choose Files)"
    ),
    file: UploadFile = File(
        None, description="Single PDF file upload (Choose File)"
    ),
):
    """Submits form data along with uploaded files (PDF, Excel, CSV) and parses them using the graph's parse_input node."""
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

    # Save uploaded files to disk
    request_id_temp = str(uuid.uuid4())
    upload_dir = os.path.join(DATA_DIR, "uploads", request_id_temp)
    os.makedirs(upload_dir, exist_ok=True)

    saved_paths = []
    for upload in file_list:
        if upload and upload.filename:
            file_path = os.path.join(upload_dir, upload.filename)
            content = await upload.read()
            with open(file_path, "wb") as f:
                f.write(content)
            saved_paths.append(file_path)

    saved_state = _run_pipeline(form_dict, uploaded_file_paths=saved_paths)

    return SubmissionResponse(
        request_id=saved_state["request_id"],
        status=saved_state.get("status", "PROCESSED"),
        decision=saved_state.get("decision"),
        score=saved_state.get("score"),
        report_type=saved_state.get("report_type"),
        missing_fields=saved_state.get("missing_fields", []),
        clarification_questions=saved_state.get("clarification_questions", []),
        parsed_files_text=saved_state.get("parsed_files_text", []),
        report=saved_state.get("report"),
        created_at=saved_state.get("created_at"),
        form_data=saved_state.get("form_data", {}),
    )


@router.get(
    "/",
    response_model=List[SubmissionResponse],
    summary="List all submissions with optional filters",
)
async def get_all_submissions(
    department: Optional[str] = None, status: Optional[str] = None
):
    """Lists all submissions. Filter by department or status (e.g. GO, NEEDS_CLARIFICATION, REJECTED, FAST_TRACK)."""
    items = list_submissions(department=department, status=status)
    responses = []
    for item in items:
        responses.append(
            SubmissionResponse(
                request_id=item["request_id"],
                status=item.get("status", "PROCESSED"),
                decision=item.get("decision"),
                score=item.get("score"),
                report_type=item.get("report_type"),
                missing_fields=item.get("missing_fields", []),
                clarification_questions=item.get("clarification_questions", []),
                parsed_files_text=item.get("parsed_files_text", []),
                report=item.get("report"),
                created_at=item.get("created_at"),
                form_data=item.get("form_data", {}),
            )
        )
    return responses


@router.get(
    "/{request_id}",
    response_model=SubmissionResponse,
    summary="Get submission details by request_id",
)
async def get_submission_by_id(request_id: str):
    """Retrieves full details and status of a submission by request_id."""
    sub = get_submission(request_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission '{request_id}' not found",
        )

    return SubmissionResponse(
        request_id=sub["request_id"],
        status=sub.get("status", "PROCESSED"),
        decision=sub.get("decision"),
        score=sub.get("score"),
        report_type=sub.get("report_type"),
        missing_fields=sub.get("missing_fields", []),
        clarification_questions=sub.get("clarification_questions", []),
        parsed_files_text=sub.get("parsed_files_text", []),
        report=sub.get("report"),
        created_at=sub.get("created_at"),
        form_data=sub.get("form_data", {}),
    )
