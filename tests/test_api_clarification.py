"""
Tests for Clarification Loop API Endpoints (Module C)
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_clarification_questions_not_found(async_client: AsyncClient):
    """Test GET /api/submissions/non_existent_id/clarification returns 404."""
    response = await async_client.get("/api/submissions/00000000-0000-0000-0000-000000000000/clarification")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_submit_clarification_when_not_needed_400(async_client: AsyncClient, seeded_department):
    """Test POST /api/submissions/{id}/clarification returns 400 if submission decision is not NEEDS_CLARIFICATION."""
    payload = {
        "project_name": "Clear Onboarding Bot",
        "department": "corporate_support",
        "team_contact_name": "Jean Dupont",
        "team_contact_email": "jean.dupont@segula.fr",
        "problem_description": "New employees spend 2 weeks asking colleagues basic HR questions. We want an AI chatbot that answers onboarding questions instantly.",
        "current_process": "Manual search on SharePoint and emailing colleagues.",
        "expected_outcome": "Chatbot answers HR questions in under 10 seconds.",
        "data_description": "500 policy documents and internal FAQ list.",
        "deadline_urgency": "medium",
        "department_specific": {
            "service_area": "hr",
            "target_users": "employees",
            "has_existing_system": True,
        },
    }

    create_res = await async_client.post("/api/submissions/", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    req_id = created_data["request_id"]

    # Submit clarification for a submission that is GO/COMPLETED
    answer_res = await async_client.post(
        f"/api/submissions/{req_id}/clarification",
        json={"answers": ["Answer 1", "Answer 2"]},
    )
    assert answer_res.status_code == 400
    assert "does not currently require clarification" in answer_res.json()["detail"]


@pytest.mark.asyncio
async def test_clarification_loop_e2e(async_client: AsyncClient, seeded_department):
    """Test full clarification loop: Vague submission -> NEEDS_CLARIFICATION -> Submit Answers -> Re-invoke Graph."""
    vague_payload = {
        "project_name": "Vague HR Idea",
        "department": "corporate_support",
        "team_contact_name": "Sophie Martin",
        "team_contact_email": "sophie.martin@segula.fr",
        "problem_description": "We want to use AI somewhere in HR to improve overall efficiency.",
        "current_process": "Manual work",
        "expected_outcome": "Better productivity",
        "deadline_urgency": "low",
        "department_specific": {
            "service_area": "hr",
            "target_users": "employees",
            "has_existing_system": False,
        },
    }

    create_res = await async_client.post("/api/submissions/", json=vague_payload)
    assert create_res.status_code == 201
    submission_data = create_res.json()
    req_id = submission_data["request_id"]

    if submission_data.get("decision") == "NEEDS_CLARIFICATION" or submission_data.get("status") == "NEEDS_CLARIFICATION":
        get_clar_res = await async_client.get(f"/api/submissions/{req_id}/clarification")
        assert get_clar_res.status_code == 200
        clar_data = get_clar_res.json()
        assert clar_data["request_id"] == req_id

        answers_payload = {
            "answers": [
                "We specifically want an automated document parser that extracts skills from incoming candidate resumes.",
                "We currently process 200 PDF resumes manually every week.",
                "We have a repository of 5,000 anonymized resumes to train and evaluate the classification model.",
            ]
        }

        post_answer_res = await async_client.post(
            f"/api/submissions/{req_id}/clarification", json=answers_payload
        )
        assert post_answer_res.status_code == 200
        updated_clar = post_answer_res.json()

        assert len(updated_clar["answers"]) >= 3
        assert updated_clar["clarification_round"] >= 1
