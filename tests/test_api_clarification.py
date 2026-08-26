import asyncio
import uuid
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient

from backend.models.db_schemes.requirementshub.schemes import (
    Submission,
    ScoringResult,
    ClarificationRound,
)
from backend.models.enums.SubmissionStatusEnum import SubmissionStatus
from backend.schemas import (
    CategoricalFactExtraction,
    ClarificationQuestionsModel,
    QuestionItem,
    PillarAIViability,
    PillarDataReadiness,
    PillarProblemClarity,
    PillarIntegration,
    PillarGovernance,
)


def _mock_llm(return_value, model_used="mock/test-model"):
    """Fake LLMInterface whose generate_structured_output resolves to return_value."""
    llm = AsyncMock()
    llm.generate_structured_output = AsyncMock(return_value=return_value)
    llm.last_model_used = model_used
    return llm


def _facts(
    ai_viability="HIGHLY_VIABLE",
    data_readiness="READY",
    problem_clarity="CLEAR",
    integration="SIMPLE",
    governance="SAFE",
    department_relevance="RELEVANT",
    summary="Mocked project summary.",
    technique="RAG + Classification",
) -> CategoricalFactExtraction:
    return CategoricalFactExtraction(
        project_summary=summary,
        identified_technique=technique,
        department_relevance=department_relevance,
        ai_viability=PillarAIViability(category=ai_viability, reason="Mocked reasoning."),
        data_readiness=PillarDataReadiness(category=data_readiness, reason="Mocked reasoning."),
        problem_clarity=PillarProblemClarity(category=problem_clarity, reason="Mocked reasoning."),
        integration_feasibility=PillarIntegration(category=integration, reason="Mocked reasoning."),
        governance_and_safety=PillarGovernance(category=governance, reason="Mocked reasoning."),
    )


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

    vague_facts = _facts(problem_clarity="VAGUE", data_readiness="NONE", summary="Vague HR AI idea, no defined scope.")
    resolved_facts = _facts(problem_clarity="CLEAR", data_readiness="READY", summary="Resume skill parser, scoped and data-backed.")
    mock_questions = ClarificationQuestionsModel(questions=[
        QuestionItem(question="What specific HR process should this target?", target_pillar="problem_clarity"),
    ])

    with patch("backend.nodes.llm_analyze.get_structured_llm", return_value=_mock_llm(vague_facts)), \
         patch("backend.nodes.generate_questions.get_clarification_llm", return_value=_mock_llm(mock_questions)):
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

        with patch("backend.nodes.llm_analyze.get_structured_llm", return_value=_mock_llm(resolved_facts)), \
             patch("backend.nodes.generate_questions.get_clarification_llm", return_value=_mock_llm(mock_questions)):
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
    resolved_facts = _facts(problem_clarity="CLEAR", data_readiness="READY", summary="Ticket routing classifier, resolved scope and data.")
    with patch("backend.nodes.llm_analyze.get_structured_llm", return_value=_mock_llm(resolved_facts)):
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
    still_unclear_facts = _facts(problem_clarity="PARTIAL", data_readiness="UNLABELED_OR_MESSY", summary="HVAC predictive maintenance, still ambiguous scope.")
    with patch("backend.nodes.llm_analyze.get_structured_llm", return_value=_mock_llm(still_unclear_facts)):
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
    assert (
        "already been completed" in r3_res.json()["detail"].lower()
        or "does not currently require clarification" in r3_res.json()["detail"].lower()
    )


@pytest.mark.asyncio
async def test_clarification_preserves_parsed_files_text(
    async_client: AsyncClient, db_session, seeded_department
):
    """Test that parsed_files_text persisted on Submission is preserved and accessible in clarification."""
    req_uuid = uuid.uuid4()
    req_id = str(req_uuid)

    sub = Submission(
        id=req_uuid,
        project_name="AI Fleet Maintenance",
        department_id="automotive",
        team_contact_name="Claire Martin",
        team_contact_email="claire.martin@segula.fr",
        problem_description="Predictive maintenance needed for truck fleet.",
        current_process="Scheduled maintenance every 10k km.",
        expected_outcome="Predict failures 48h in advance.",
        data_description="CAN bus logs and maintenance history.",
        deadline_urgency="high",
        department_specific={"powertrain_type": "diesel"},
        parsed_files_text=["--- Page 1 ---\nTechnical CAN bus specs and error codes attached."],
        status=SubmissionStatus.NEEDS_CLARIFICATION.value,
    )
    db_session.add(sub)

    scoring = ScoringResult(
        submission_id=req_uuid,
        score=65,
        decision="NEEDS_CLARIFICATION",
        breakdown={"sub_scores": {"ai_viability": 70, "data_readiness": 60}},
    )
    db_session.add(scoring)

    round_1 = ClarificationRound(
        submission_id=req_uuid,
        round_number=1,
        questions=[{"question": "How many vehicles are in the active fleet?", "target_pillar": "data_readiness"}],
        answers=[],
    )
    db_session.add(round_1)
    await db_session.commit()

    # Verify submission response includes parsed_files_text
    get_res = await async_client.get(f"/api/submissions/{req_id}")
    assert get_res.status_code == 200
    assert get_res.json()["parsed_files_text"] == ["--- Page 1 ---\nTechnical CAN bus specs and error codes attached."]


@pytest.mark.asyncio
async def test_clarification_fallback_empty_answers(async_client: AsyncClient, db_session, seeded_department, monkeypatch):
    """Test that submitting clarification handles answers safely without NameError."""
    from unittest.mock import AsyncMock, MagicMock

    req_uuid = uuid.uuid4()
    req_id = str(req_uuid)

    sub = Submission(
        id=req_uuid,
        project_name="Empty Answers Fallback Test",
        department_id="corporate_support",
        team_contact_name="Tester",
        team_contact_email="tester@segula.fr",
        problem_description="Test problem description",
        current_process="Manual",
        expected_outcome="Automated",
        data_description="Some data",
        deadline_urgency="low",
        department_specific={"service_area": "hr"},
        status=SubmissionStatus.NEEDS_CLARIFICATION.value,
    )
    db_session.add(sub)

    scoring = ScoringResult(
        submission_id=req_uuid,
        score=50,
        decision="NEEDS_CLARIFICATION",
        breakdown={"sub_scores": {"ai_viability": 50}},
    )
    db_session.add(scoring)

    round_1 = ClarificationRound(
        submission_id=req_uuid,
        round_number=1,
        questions=[{"question": "Can you specify the scope?", "target_pillar": "problem_clarity"}],
        answers=[],
    )
    db_session.add(round_1)
    await db_session.commit()

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value={
        "status": "COMPLETED",
        "score": 80,
        "decision": "GO",
        "score_breakdown": {"ai_viability": 80},
        "report": "Final evaluation report content.",
    })
    # No checkpoint exists for this thread_id (state was seeded directly in the DB,
    # the graph never actually ran) — aget_state must report an empty snapshot so
    # the route takes the fallback (reconstruct-and-rerun) path, not the resume path.
    empty_snapshot = MagicMock()
    empty_snapshot.values = {}
    empty_snapshot.next = ()
    mock_graph.aget_state = AsyncMock(return_value=empty_snapshot)
    monkeypatch.setattr("backend.api.routes_clarification.get_compiled_graph", lambda checkpointer=None: mock_graph)

    res = await async_client.post(
        f"/api/submissions/{req_id}/clarification",
        json={"answers": ["Scope is restricted to internal documentation search."]}
    )
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data["answers"], list)
    assert len(data["answers"]) == 1
    assert data["decision"] == "GO"



