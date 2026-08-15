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


@pytest.mark.asyncio
async def test_get_report_and_score_5_pillars(async_client: AsyncClient, db_session: AsyncSession, seeded_department):
    """Test fetching report and 5-pillar categorical score breakdown with circuit-breaker veto fields."""
    from backend.models.FactExtractionModel import FactExtractionModel

    req_uuid = uuid.uuid4()
    req_id = str(req_uuid)

    sub_model = SubmissionModel(db_session)
    sub = Submission(
        id=req_uuid,
        project_name="Predictive Maintenance AI",
        department_id="corporate_support",
        status="COMPLETED",
    )
    await sub_model.create_submission(sub)

    # Seed FactExtraction with 5 pillars
    fact_model = FactExtractionModel(db_session)
    await fact_model.create_or_update(
        req_id,
        {
            "ai_viability": {"category": "HIGHLY_VIABLE", "reason": "Standard supervised ML"},
            "data_readiness": {"category": "READY", "reason": "50,000 labeled sensor records"},
            "problem_clarity": {"category": "CLEAR", "reason": "Predict component failure 48h prior"},
            "integration_feasibility": {"category": "SEAMLESS", "reason": "REST API into existing MES"},
            "governance_and_safety": {"category": "LOW_RISK", "reason": "Advisory internal tool"},
        },
    )

    scoring_model = ScoringModel(db_session)
    await scoring_model.create_or_update(
        req_id,
        {
            "score": 95,
            "percentage": 95,
            "decision": "GO",
            "breakdown": {
                "sub_scores": {
                    "ai_viability": 30,
                    "data_readiness": 25,
                    "problem_clarity": 20,
                    "integration": 10,
                    "governance": 10,
                },
                "veto_triggered": False,
                "veto_reasons": [],
            },
        },
    )

    report_model = ReportModel(db_session)
    await report_model.create_or_update(
        req_id,
        report_type="FULL_CAHIER_DES_CHARGES",
        content="# Predictive Maintenance Dossier\nScore: 95/100",
    )

    # Fetch Score
    score_res = await async_client.get(f"/api/submissions/{req_id}/score")
    assert score_res.status_code == 200
    score_data = score_res.json()

    assert score_data["score"] == 95
    assert score_data["decision"] == "GO"
    assert score_data["veto_triggered"] is False
    assert score_data["veto_reasons"] == []
    assert score_data["sub_scores"]["ai_viability"] == 30
    assert score_data["sub_scores"]["data_readiness"] == 25
    assert score_data["sub_scores"]["problem_clarity"] == 20
    assert score_data["sub_scores"]["integration"] == 10
    assert score_data["sub_scores"]["governance"] == 10

    assert score_data["pillars"]["ai_viability"]["category"] == "HIGHLY_VIABLE"
    assert score_data["pillars"]["data_readiness"]["category"] == "READY"
    assert score_data["pillars"]["problem_clarity"]["category"] == "CLEAR"
    assert score_data["pillars"]["integration_feasibility"]["category"] == "SEAMLESS"
    assert score_data["pillars"]["governance_and_safety"]["category"] == "LOW_RISK"

    # Fetch Report
    report_res = await async_client.get(f"/api/submissions/{req_id}/report")
    assert report_res.status_code == 200
    report_data = report_res.json()
    assert report_data["sub_scores"]["ai_viability"] == 30
    assert report_data["veto_triggered"] is False

