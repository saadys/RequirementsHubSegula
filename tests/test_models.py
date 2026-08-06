"""
tests/test_models.py
Production Unit Tests for all 7 ORM Models & Data Access Layer (`backend/models`).
"""

import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.DepartmentModel import DepartmentModel
from backend.models.SubmissionModel import SubmissionModel
from backend.models.FactExtractionModel import FactExtractionModel
from backend.models.ScoringModel import ScoringModel
from backend.models.ClarificationModel import ClarificationModel
from backend.models.ReportModel import ReportModel
from backend.models.ReviewerModel import ReviewerModel

from backend.models.db_schemes.requirementshub.schemes import (
    Department,
    Submission,
    FactExtraction,
    ScoringResult,
    ClarificationRound,
    Report,
    ReviewerOverride,
)


@pytest.mark.asyncio
async def test_department_model_crud(db_session: AsyncSession):
    """Test DepartmentModel CRUD operations."""
    model = DepartmentModel(db_client=db_session)

    # 1. Create department
    dept = Department(
        id="automotive",
        display_name="Automotive Engineering",
        description="ADAS and Powertrain systems",
        enabled=True,
        specific_fields=[{"name": "vehicle_type", "type": "string"}],
    )
    saved = await model.save_department(dept)
    assert saved.id == "automotive"

    # 2. Get department by ID
    fetched = await model.get_department_by_id("automotive")
    assert fetched is not None
    assert fetched.display_name == "Automotive Engineering"

    # 3. List enabled departments
    all_enabled = await model.get_all_departments(enabled_only=True)
    assert len(all_enabled) == 1
    assert all_enabled[0].id == "automotive"


@pytest.mark.asyncio
async def test_submission_model_crud(db_session: AsyncSession, seeded_department: Department):
    """Test SubmissionModel creation, state updates, and filtering."""
    model = SubmissionModel(db_client=db_session)

    sub = Submission(
        project_name="Autonomous Braking AI",
        department_id=seeded_department.id,
        team_contact_name="Sara Connor",
        team_contact_email="sara@segula.fr",
        problem_description="Identify obstacle detection latency in LIDAR streams.",
        deadline_urgency="high",
        status="PENDING",
    )
    saved = await model.create_submission(sub)
    assert saved.id is not None
    assert saved.status == "PENDING"

    # Fetch by ID
    fetched = await model.get_submission_by_id(saved.id)
    assert fetched is not None
    assert fetched.project_name == "Autonomous Braking AI"

    # Update status
    updated = await model.update_status(saved.id, "PROCESSED")
    assert updated.status == "PROCESSED"

    # List submissions with status filter
    filtered = await model.list_submissions(status_filter="PROCESSED")
    assert len(filtered) == 1
    assert filtered[0].id == saved.id


@pytest.mark.asyncio
async def test_fact_extraction_model_1to1_relationship(db_session: AsyncSession, seeded_department: Department):
    """Test FactExtractionModel 1:1 relationship with Submission."""
    sub_model = SubmissionModel(db_client=db_session)
    sub = await sub_model.create_submission(
        Submission(
            project_name="RAG Document Search",
            department_id=seeded_department.id,
            status="PENDING",
        )
    )

    fact_model = FactExtractionModel(db_client=db_session)
    fact = FactExtraction(
        submission_id=sub.id,
        has_clear_problem_statement=True,
        problem_is_ai_solvable=True,
        problem_category="nlp",
        summary="Extracted requirement facts.",
    )
    saved_fact = await fact_model.save_fact_extraction(fact)
    assert saved_fact.submission_id == sub.id

    fetched_fact = await fact_model.get_by_submission_id(sub.id)
    assert fetched_fact is not None
    assert fetched_fact.problem_category == "nlp"


@pytest.mark.asyncio
async def test_scoring_model_and_breakdown(db_session: AsyncSession, seeded_department: Department):
    """Test ScoringModel creation and feasibility breakdown dict storage."""
    sub_model = SubmissionModel(db_client=db_session)
    sub = await sub_model.create_submission(
        Submission(project_name="Feasibility Test", department_id=seeded_department.id)
    )

    scoring_model = ScoringModel(db_client=db_session)
    breakdown_data = {
        "problem_clarity": {"points": 20, "max": 20},
        "data_readiness": {"points": 15, "max": 20},
    }
    score_res = ScoringResult(
        submission_id=sub.id,
        score=85,
        percentage=85,
        decision="GO",
        breakdown=breakdown_data,
    )
    saved_score = await scoring_model.save_scoring_result(score_res)
    assert saved_score.score == 85
    assert saved_score.decision == "GO"
    assert saved_score.breakdown["problem_clarity"]["points"] == 20


@pytest.mark.asyncio
async def test_clarification_model_1toN_rounds(db_session: AsyncSession, seeded_department: Department):
    """Test ClarificationModel 1:N Q&A round tracking."""
    sub_model = SubmissionModel(db_client=db_session)
    sub = await sub_model.create_submission(
        Submission(project_name="Clarification Test", department_id=seeded_department.id)
    )

    clar_model = ClarificationModel(db_client=db_session)

    # Round 1
    r1 = ClarificationRound(
        submission_id=sub.id,
        round_number=1,
        questions=["What format is the data?"],
        answers=["CSV files on S3"],
    )
    await clar_model.save_clarification_round(r1)

    # Round 2
    r2 = ClarificationRound(
        submission_id=sub.id,
        round_number=2,
        questions=["How many rows are expected?"],
        answers=["Around 1,000,000 rows"],
    )
    await clar_model.save_clarification_round(r2)

    rounds = await clar_model.get_rounds_by_submission_id(sub.id)
    assert len(rounds) == 2
    assert rounds[0].round_number == 1
    assert rounds[1].round_number == 2


@pytest.mark.asyncio
async def test_report_model(db_session: AsyncSession, seeded_department: Department):
    """Test ReportModel storing final Markdown content."""
    sub_model = SubmissionModel(db_client=db_session)
    sub = await sub_model.create_submission(
        Submission(project_name="Report Generation Test", department_id=seeded_department.id)
    )

    report_model = ReportModel(db_client=db_session)
    rep = Report(
        submission_id=sub.id,
        report_type="FULL_CAHIER_DES_CHARGES",
        content="# Cahier des Charges\n\n## 1. Executive Summary\nAI project approved.",
    )
    saved_rep = await report_model.save_report(rep)
    assert saved_rep.report_type == "FULL_CAHIER_DES_CHARGES"

    fetched = await report_model.get_by_submission_id(sub.id)
    assert fetched is not None
    assert "# Cahier des Charges" in fetched.content


@pytest.mark.asyncio
async def test_reviewer_override_append_only_audit(db_session: AsyncSession, seeded_department: Department):
    """Test ReviewerModel append-only audit trail logging for decision overrides."""
    sub_model = SubmissionModel(db_client=db_session)
    sub = await sub_model.create_submission(
        Submission(project_name="Audit Override Test", department_id=seeded_department.id)
    )

    rev_model = ReviewerModel(db_client=db_session)

    # Override 1: NEEDS_CLARIFICATION -> GO
    o1 = ReviewerOverride(
        submission_id=sub.id,
        previous_decision="NEEDS_CLARIFICATION",
        new_decision="GO",
        reviewer_name="Alex Engineer",
        reviewer_notes="Additional dataset provided manually.",
    )
    await rev_model.save_override(o1)

    # Override 2: GO -> NO_GO (Strategic shift)
    o2 = ReviewerOverride(
        submission_id=sub.id,
        previous_decision="GO",
        new_decision="NO_GO",
        reviewer_name="Senior Architect",
        reviewer_notes="Duplicate internal project found.",
    )
    await rev_model.save_override(o2)

    overrides = await rev_model.get_overrides_by_submission_id(sub.id)
    assert len(overrides) == 2
    assert overrides[0].new_decision == "GO"
    assert overrides[1].new_decision == "NO_GO"


@pytest.mark.asyncio
async def test_cascade_deletion(db_session: AsyncSession, seeded_department: Department):
    """Test that deleting a Submission cascade-deletes all associated child records."""
    sub_model = SubmissionModel(db_client=db_session)
    sub = await sub_model.create_submission(
        Submission(project_name="Cascade Deletion Test", department_id=seeded_department.id)
    )

    # Attach child records
    await FactExtractionModel(db_session).save_fact_extraction(
        FactExtraction(submission_id=sub.id, summary="Fact to be deleted")
    )
    await ScoringModel(db_session).save_scoring_result(
        ScoringResult(submission_id=sub.id, score=90, decision="GO")
    )
    await ReportModel(db_session).save_report(
        Report(submission_id=sub.id, content="Report content")
    )

    # Delete parent submission
    await sub_model.delete_submission(sub.id)

    # Verify children are deleted
    assert await FactExtractionModel(db_session).get_by_submission_id(sub.id) is None
    assert await ScoringModel(db_session).get_by_submission_id(sub.id) is None
    assert await ReportModel(db_session).get_by_submission_id(sub.id) is None
