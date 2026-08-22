import uuid
import pytest
from unittest.mock import patch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.routes_stream import _save_pipeline_state_to_db
from backend.models.db_schemes.requirementshub.schemes import (
    Submission,
    FactExtraction,
    ScoringResult,
    Report,
)
from backend.models.SubmissionModel import SubmissionModel
from backend.schemas import SubmissionStatus


@pytest.mark.asyncio
async def test_save_pipeline_state_to_db_success(db_session: AsyncSession, seeded_department):
    """Verify that all state components are atomically persisted in one go."""
    req_uuid = uuid.uuid4()
    req_id = str(req_uuid)

    sub = Submission(
        id=req_uuid,
        project_name="Atomic Pipeline Test",
        department_id="corporate_support",
        team_contact_name="Alice Martin",
        team_contact_email="alice.martin@segula.fr",
        problem_description="Testing atomic persistence",
        status="PENDING",
    )
    db_session.add(sub)
    await db_session.commit()

    state = {
        "request_id": req_id,
        "parsed_files_text": ["Extracted text from doc 1"],
        "extracted_facts": {
            "identified_technique": "RAG",
            "project_summary": "Atomic pipeline summary",
        },
        "score": 85.0,
        "decision": "GO",
        "sub_scores": {"ai_viability": 30, "data_readiness": 25},
        "veto_triggered": False,
        "veto_reasons": [],
        "report": "# Feasibility Report\nAll checks passed.",
        "report_type": "go",
    }

    await _save_pipeline_state_to_db(req_id, state, SubmissionStatus.COMPLETED.value)

    # Verify all records exist in DB (expire identity map cache first)
    db_session.expire_all()
    sub_model = SubmissionModel(db_session)
    reloaded = await sub_model.get_by_id_with_relations(req_uuid)

    assert reloaded is not None
    assert reloaded.status == "COMPLETED"
    assert reloaded.parsed_files_text == ["Extracted text from doc 1"]
    assert reloaded.fact_extraction is not None
    assert reloaded.fact_extraction.identified_technique == "RAG"
    assert reloaded.scoring_result is not None
    assert reloaded.scoring_result.score == 85.0
    assert reloaded.scoring_result.decision == "GO"
    assert reloaded.report is not None
    assert reloaded.report.content == "# Feasibility Report\nAll checks passed."


@pytest.mark.asyncio
async def test_save_pipeline_state_to_db_rollback_on_failure(db_session: AsyncSession, seeded_department):
    """Verify that if an error occurs mid-way (e.g. during report creation), all changes roll back."""
    req_uuid = uuid.uuid4()
    req_id = str(req_uuid)

    sub = Submission(
        id=req_uuid,
        project_name="Atomic Rollback Test",
        department_id="corporate_support",
        team_contact_name="Bob Test",
        team_contact_email="bob.test@segula.fr",
        problem_description="Testing rollback",
        status="PENDING",
    )
    db_session.add(sub)
    await db_session.commit()

    state = {
        "request_id": req_id,
        "parsed_files_text": ["New parsed text"],
        "extracted_facts": {
            "identified_technique": "CV",
        },
        "score": 40.0,
        "decision": "NO_GO",
        "report": "Failing report creation",
    }

    # Simulate an unhandled database error during report creation
    with patch(
        "backend.models.ReportModel.ReportModel.create_or_update",
        side_effect=RuntimeError("Simulated DB connection drop"),
    ):
        with pytest.raises(RuntimeError, match="Simulated DB connection drop"):
            await _save_pipeline_state_to_db(req_id, state, SubmissionStatus.REJECTED.value)

    # Clean local session cache and reload directly from database
    db_session.expire_all()
    sub_model = SubmissionModel(db_session)
    reloaded = await sub_model.get_by_id_with_relations(req_uuid)

    # Since transaction was rolled back, status remains PENDING and child records were NOT persisted
    assert reloaded.status == "PENDING"
    assert reloaded.fact_extraction is None
    assert reloaded.scoring_result is None
    assert reloaded.report is None
