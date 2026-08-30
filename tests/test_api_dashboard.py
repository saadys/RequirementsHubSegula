"""
Tests for AI Team Dashboard API Endpoints (Module E)
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_override_decision_not_found(async_client: AsyncClient):
    """Test 404 for non-existent submission ID when performing decision override."""
    res = await async_client.post(
        "/api/dashboard/00000000-0000-0000-0000-000000000000/decision",
        json={
            "decision": "GO",
            "reviewer_notes": "Manual override test",
            "reviewer_name": "Test Engineer",
        },
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_dashboard_pending_and_override(async_client: AsyncClient, seeded_department):
    """Test listing pending requests and performing a manual decision override by an AI engineer."""
    vague_payload = {
        "project_name": "Low Feasibility Idea",
        "department": "corporate_support",
        "team_contact_name": "Alex Vance",
        "team_contact_email": "alex.vance@segula.fr",
        "problem_description": "General AI idea for productivity without data or specifics.",
        "current_process": "Unknown",
        "expected_outcome": "Automate everything",
        "deadline_urgency": "low",
        "department_specific": {
            "service_area": "hr",
            "target_users": "employees",
            "has_existing_system": False,
        },
    }

    create_res = await async_client.post("/api/submissions/", json=vague_payload)
    assert create_res.status_code == 201
    submission = create_res.json()
    req_id = submission["request_id"]

    # 1. Check Pending List
    pending_res = await async_client.get("/api/dashboard/pending")
    assert pending_res.status_code == 200
    pending_items = pending_res.json()
    assert isinstance(pending_items, list)
    matching = [p for p in pending_items if p["request_id"] == req_id]
    assert len(matching) >= 1

    # 2. Perform AI Engineer Decision Override to GO
    override_payload = {
        "decision": "GO",
        "reviewer_notes": "Approved manually after direct discussion with business team lead.",
        "reviewer_name": "Sarah Connor",
    }
    override_res = await async_client.post(f"/api/dashboard/{req_id}/decision", json=override_payload)
    assert override_res.status_code == 200
    override_data = override_res.json()

    assert override_data["request_id"] == req_id
    assert override_data["decision"] == "GO"
    assert override_data["status"] == "COMPLETED"
    assert override_data["manual_override"] is True
    assert override_data["reviewer_name"] == "Sarah Connor"

    # 3. Verify state persisted via GET /api/submissions/{request_id}
    sub_res = await async_client.get(f"/api/submissions/{req_id}")
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert sub_data["decision"] == "GO"
    assert sub_data["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_dashboard_5_pillar_metadata(async_client: AsyncClient, db_session, seeded_department):
    """Test dashboard pending items serialization of 5-pillar categorizations and veto flags."""
    import uuid
    from backend.models.SubmissionModel import SubmissionModel
    from backend.models.FactExtractionModel import FactExtractionModel
    from backend.models.ScoringModel import ScoringModel
    from backend.models.db_schemes.requirementshub.schemes.submission import Submission

    req_uuid = uuid.uuid4()
    req_id = str(req_uuid)

    sub_model = SubmissionModel(db_session)
    sub = Submission(
        id=req_uuid,
        project_name="Dashboard 5 Pillar Test",
        department_id="corporate_support",
        status="NEEDS_CLARIFICATION",
    )
    await sub_model.create_submission(sub)

    fact_model = FactExtractionModel(db_session)
    await fact_model.create_or_update(
        req_id,
        {
            "ai_viability": {"category": "VIABLE", "reason": "Standard NLP"},
            "data_readiness": {"category": "PARTIAL", "reason": "Missing labeled samples"},
            "problem_clarity": {"category": "AMBIGUOUS", "reason": "Unclear success metrics"},
            "integration_feasibility": {"category": "MODERATE", "reason": "Custom webhook required"},
            "governance_and_safety": {"category": "MEDIUM_RISK", "reason": "Internal usage only"},
        },
    )

    scoring_model = ScoringModel(db_session)
    await scoring_model.create_or_update(
        req_id,
        {
            "score": 45,
            "percentage": 45,
            "decision": "NEEDS_CLARIFICATION",
            "breakdown": {
                "sub_scores": {
                    "ai_viability": 20,
                    "data_readiness": 10,
                    "problem_clarity": 10,
                    "integration": 5,
                    "governance": 0,
                },
                "veto_triggered": False,
                "veto_reasons": [],
            },
        },
    )

    pending_res = await async_client.get("/api/dashboard/pending")
    assert pending_res.status_code == 200
    pending_items = pending_res.json()
    matching = [p for p in pending_items if p["request_id"] == req_id]
    assert len(matching) == 1
    item = matching[0]

    assert item["score"] == 45
    assert item["decision"] == "NEEDS_CLARIFICATION"
    assert item["sub_scores"]["ai_viability"] == 20
    assert item["ai_viability_category"] == "VIABLE"
    assert item["data_readiness_category"] == "PARTIAL"
    assert item["problem_clarity_category"] == "AMBIGUOUS"
    assert item["veto_triggered"] is False


@pytest.mark.asyncio
async def test_ingest_historic_project_not_found(async_client: AsyncClient):
    """Test 404 response when attempting to ingest a non-existent submission."""
    payload = {
        "project_name": "Non-existent Project",
        "department": "corporate_support",
        "problem_description": "Valid problem description for testing 404 response.",
        "solution_description": "Valid solution description for testing 404 response.",
        "outcome": "Valid outcome metrics achieved.",
    }
    res = await async_client.post(
        "/api/dashboard/00000000-0000-0000-0000-000000000000/ingest-historic",
        json=payload,
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ingest_historic_project_validation_error(async_client: AsyncClient):
    """Test 422 response when required fields are missing or invalid."""
    res = await async_client.post(
        "/api/dashboard/00000000-0000-0000-0000-000000000000/ingest-historic",
        json={"project_name": "Incomplete"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_ingest_historic_project_success(async_client: AsyncClient, seeded_department):
    """Test successful ingestion of a completed project into pgvector knowledge base."""
    from unittest.mock import patch
    from backend.config import EMBEDDING_DIMENSION

    # 1. Create a submission first
    payload = {
        "project_name": "Autonomous Drone Inspection",
        "department": "aerospace",
        "team_contact_name": "Jean Dupont",
        "team_contact_email": "jean.dupont@segula.fr",
        "problem_description": "Automated crack inspection on aircraft wings using drone video feed.",
        "current_process": "Manual scaffolding inspection taking 48 hours.",
        "expected_outcome": "Real-time edge detection in 15 minutes.",
        "deadline_urgency": "high",
        "department_specific": {},
    }
    create_res = await async_client.post("/api/submissions/", json=payload)
    assert create_res.status_code == 201
    req_id = create_res.json()["request_id"]

    # 2. Ingest into knowledge base (with mocked embedding)
    ingest_payload = {
        "project_name": "Autonomous Drone Inspection",
        "department": "aerospace",
        "problem_description": "Automated crack inspection on aircraft wings using drone video feed.",
        "solution_description": "Edge YOLOv8 segmentation on NVIDIA Jetson Orin with TensorRT runtime.",
        "outcome": "99.1% precision in crack detection, reduced inspection time from 48h to 15min.",
        "contact_person": "Jean Dupont",
        "year": 2026,
        "ai_techniques": ["YOLOv8", "TensorRT", "Jetson Orin", "Edge AI"],
        "tags": ["aerospace", "inspection", "drones", "cv"],
        "lessons_learned": "Lighting variations compensated with real-time histogram equalization.",
    }

    with patch("backend.services.vectorstore.generate_embedding", return_value=[0.02] * EMBEDDING_DIMENSION):
        ingest_res = await async_client.post(
            f"/api/dashboard/{req_id}/ingest-historic",
            json=ingest_payload,
        )

    assert ingest_res.status_code == 201
    ingest_data = ingest_res.json()
    assert ingest_data["request_id"] == req_id
    assert ingest_data["historic_id"].startswith("HIST-2026-")
    assert ingest_data["status"] == "IMPLEMENTED"
    from backend.config import EMBEDDING_DIMENSION
    assert ingest_data["embedding_dimension"] == EMBEDDING_DIMENSION

    # 3. Verify submission status updated to IMPLEMENTED
    sub_res = await async_client.get(f"/api/submissions/{req_id}")
    assert sub_res.status_code == 200
    assert sub_res.json()["status"] == "IMPLEMENTED"

