"""
Tests for Reports & Scores API Endpoints (Module D)
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.ReportModel import ReportModel
from backend.models.ScoringModel import ScoringModel
from backend.models.SubmissionModel import SubmissionModel
from backend.models.db_schemes.requirementshub.schemes.submission import Submission


@pytest.mark.asyncio
async def test_get_report_and_score_not_found(async_client: AsyncClient):
    """Test 404 for non-existent submission IDs."""
    rep_res = await async_client.get("/api/submissions/00000000-0000-0000-0000-000000000000/report")
    assert rep_res.status_code == 404
    assert "not found" in rep_res.json()["detail"].lower()

    score_res = await async_client.get("/api/submissions/00000000-0000-0000-0000-000000000000/score")
    assert score_res.status_code == 404
    assert "not found" in score_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_report_and_score_success(async_client: AsyncClient, db_session: AsyncSession, seeded_department):
    """Test fetching report and score breakdown endpoints using SQLAlchemy ORM seeding."""
    req_uuid = uuid.uuid4()
    req_id = str(req_uuid)

    sub_model = SubmissionModel(db_session)
    sub = Submission(
        id=req_uuid,
        project_name="AI Document Classifier",
        department_id="corporate_support",
        status="COMPLETED",
    )
    await sub_model.create_submission(sub)

    scoring_model = ScoringModel(db_session)
    score_breakdown = {
        "problem_clarity": {"score": 20, "max": 20},
        "ai_solvability": {"score": 15, "max": 15},
        "data_availability": {"score": 20, "max": 20},
        "similar_projects": {"score": 10, "max": 15},
        "research_needed": {"score": 10, "max": 10},
        "technique_clarity": {"score": 10, "max": 10},
        "integration": {"score": 0, "max": 10},
    }
    await scoring_model.create_or_update(
        req_id,
        {
            "score": 85,
            "percentage": 85,
            "decision": "GO",
            "breakdown": score_breakdown,
        },
    )

    report_model = ReportModel(db_session)
    report_content = "# AI Document Classifier Feasibility Report\nStatus: GO\nScore: 85/100"
    await report_model.create_or_update(
        req_id,
        report_type="FULL_CAHIER_DES_CHARGES",
        content=report_content,
    )

    # 1. Fetch Report
    report_res = await async_client.get(f"/api/submissions/{req_id}/report")
    assert report_res.status_code == 200
    report_data = report_res.json()
    assert report_data["request_id"] == req_id
    assert report_data["is_available"] is True
    assert report_data["report_type"] == "FULL_CAHIER_DES_CHARGES"
    assert len(report_data["report"]) > 20

    # 2. Fetch Score Breakdown
    score_res = await async_client.get(f"/api/submissions/{req_id}/score")
    assert score_res.status_code == 200
    score_data = score_res.json()
    assert score_data["request_id"] == req_id
    assert score_data["score"] == 85
    assert score_data["decision"] == "GO"

    # Verify 7 criteria breakdown structure
    breakdown = score_data["breakdown"]
    expected_criteria = [
        "problem_clarity",
        "ai_solvability",
        "data_availability",
        "similar_projects",
        "research_needed",
        "technique_clarity",
        "integration",
    ]
    for criterion in expected_criteria:
        assert criterion in breakdown
        assert "score" in breakdown[criterion]
        assert "max" in breakdown[criterion]
