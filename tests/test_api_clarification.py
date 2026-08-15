import asyncio
import uuid
import pytest
from httpx import AsyncClient

from backend.models.db_schemes.requirementshub.schemes import (
    Submission,
    ScoringResult,
    ClarificationRound,
)
from backend.models.enums.SubmissionStatusEnum import SubmissionStatus


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


@pytest.mark.asyncio
async def test_clarification_resolved_early_to_go(async_client: AsyncClient, db_session, seeded_department):
    """Test that if answers in Round 1 resolve ambiguity and achieve GO, status transitions to COMPLETED and report is generated."""
    req_uuid = uuid.uuid4()
    req_id = str(req_uuid)

    sub = Submission(
        id=req_uuid,
        project_name="Support Ticket Routing System",
        department_id="corporate_support",
        team_contact_name="Marc Lemaire",
        team_contact_email="marc.lemaire@segula.fr",
        problem_description="We want an AI solution to automatically classify IT helpdesk tickets.",
        current_process="Support team spends 3 hours daily sorting tickets by hand.",
        expected_outcome="Automated classification with > 90% routing accuracy to correct tier.",
        data_description="Zendesk exports with 15,000 historical categorized tickets.",
        deadline_urgency="medium",
        department_specific={"service_area": "it", "target_users": "employees", "has_existing_system": False},
        status=SubmissionStatus.NEEDS_CLARIFICATION.value,
    )
    db_session.add(sub)

    scoring = ScoringResult(
        submission_id=req_uuid,
        score=45,
        percentage=45,
        decision="NEEDS_CLARIFICATION",
        breakdown={"sub_scores": {"ai_viability": 20, "data_readiness": 10, "problem_clarity": 10, "integration": 5, "governance": 5}},
    )
    db_session.add(scoring)

    round_1 = ClarificationRound(
        submission_id=req_uuid,
        round_number=1,
        questions=[{"question": "How many labeled tickets exist in your export?", "target_pillar": "data_readiness"}],
        answers=[],
    )
    db_session.add(round_1)
    await db_session.commit()

    # Round 1 answer submission providing high-quality data details
    answers_r1 = {
        "answers": [
            "We have 15,000 cleaned and labeled historical tickets categorized into 8 IT categories with ground truth labels.",
        ]
    }
    r1_res = await async_client.post(f"/api/submissions/{req_id}/clarification", json=answers_r1)
    assert r1_res.status_code == 200
    r1_data = r1_res.json()
    assert r1_data["clarification_round"] >= 1
    assert r1_data["report"] is not None
    assert len(r1_data["report"]) > 50

    # Verify GET /submissions/{id} shows evaluated state
    get_sub = await async_client.get(f"/api/submissions/{req_id}")
    assert get_sub.status_code == 200
    sub_data = get_sub.json()
    assert sub_data["clarification_questions"] == []


@pytest.mark.asyncio
async def test_clarification_max_rounds_exhaustion(async_client: AsyncClient, db_session, seeded_department):
    """Test that when Round 2 is reached, the clarification loop is marked completed, questions are cleared, report is ready, and Round 3 is blocked."""
    req_uuid = uuid.uuid4()
    req_id = str(req_uuid)

    sub = Submission(
        id=req_uuid,
        project_name="Complex Edge Analytics Idea",
        department_id="corporate_support",
        team_contact_name="Marc Lemaire",
        team_contact_email="marc.lemaire@segula.fr",
        problem_description="We want AI for predictive analysis on office energy usage.",
        current_process="Monthly electricity bill review.",
        expected_outcome="Smart suggestions on HVAC controls.",
        data_description="Some utility bills and sensor logs in disparate formats.",
        deadline_urgency="low",
        department_specific={"service_area": "facilities", "target_users": "facilities", "has_existing_system": False},
        status=SubmissionStatus.NEEDS_CLARIFICATION.value,
    )
    db_session.add(sub)

    scoring = ScoringResult(
        submission_id=req_uuid,
        score=40,
        percentage=40,
        decision="NEEDS_CLARIFICATION",
        breakdown={"sub_scores": {"ai_viability": 15, "data_readiness": 10, "problem_clarity": 10, "integration": 5, "governance": 0}},
    )
    db_session.add(scoring)

    # Seed round 1 as already answered, and round 2 as active
    round_1 = ClarificationRound(
        submission_id=req_uuid,
        round_number=1,
        questions=[{"question": "Do you have digital IoT meter streams?", "target_pillar": "data_readiness"}],
        answers=["We have some CSV logs exported manually every month."],
    )
    db_session.add(round_1)

    round_2 = ClarificationRound(
        submission_id=req_uuid,
        round_number=2,
        questions=[{"question": "What frequency are HVAC metrics logged?", "target_pillar": "integration"}],
        answers=[],
    )
    db_session.add(round_2)
    await db_session.commit()

    # Submit answers for Round 2 (the final allowed round)
    answers_r2 = {
        "answers": [
            "Metrics are logged hourly via Modbus gateway.",
        ]
    }
    r2_res = await async_client.post(f"/api/submissions/{req_id}/clarification", json=answers_r2)
    assert r2_res.status_code == 200
    r2_data = r2_res.json()

    # After round 2, clarification is exhausted
    assert r2_data["clarification_round"] == 2
    assert r2_data["questions"] == []
    assert r2_data["report"] is not None
    assert len(r2_data["report"]) > 50

    # Verify GET /submissions/{id}/clarification reflects exhausted state
    get_clar = await async_client.get(f"/api/submissions/{req_id}/clarification")
    assert get_clar.status_code == 200
    get_data = get_clar.json()
    assert get_data["questions"] == []
    assert get_data["clarification_round"] == 2

    # Verify GET /submissions/{id} also reflects no pending questions
    get_sub = await async_client.get(f"/api/submissions/{req_id}")
    assert get_sub.status_code == 200
    sub_data = get_sub.json()
    assert sub_data["clarification_questions"] == []
    assert sub_data["clarification_round"] == 2
    assert sub_data["report"] is not None

    # Attempting to submit answers a 3rd time should return 400 Bad Request
    r3_res = await async_client.post(
        f"/api/submissions/{req_id}/clarification",
        json={"answers": ["Attempting round 3 answer"]},
    )
    assert r3_res.status_code == 400
    assert "already been completed" in r3_res.json()["detail"].lower()
