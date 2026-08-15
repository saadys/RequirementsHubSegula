"""
tests/test_scoring_and_pipeline.py
Production Unit Tests for Deterministic Scoring Engine & Pydantic Validation Schemas.
"""

import pytest
from pydantic import ValidationError

from backend.nodes.deterministic_score import calculate_feasibility_score, deterministic_score
from backend.schemas.Schemas import (
    FormSubmission,
    DecisionOverrideInput,
    ClarificationAnswerInput,
)
from backend.schemas.Enums import Decision, DeadlineUrgency, SubmissionStatus


def test_calculate_feasibility_score_go_decision():
    """Test feasibility calculation returning a high score (GO decision)."""
    facts = {
        "ai_viability": {"category": "HIGHLY_VIABLE", "reason": "NLP search"},
        "data_readiness": {"category": "READY", "reason": "350 clean indexed documents"},
        "problem_clarity": {"category": "CLEAR", "reason": "Precise onboarding Q&A"},
        "integration_feasibility": {"category": "SIMPLE", "reason": "Web assistant"},
        "governance_and_safety": {"category": "SAFE", "reason": "Standard internal policies"},
    }
    rag_scores = [0.65]  # RAG boost +5
    # Total score = min(100, (30 + 25 + 20 + 15 + 10) + 5) = 100

    result = calculate_feasibility_score(facts, rag_scores)
    assert result["score"] == 100
    assert result["decision"] == "GO"
    assert result["breakdown"]["ai_viability"]["score"] == 30
    assert result["breakdown"]["data_readiness"]["score"] == 25


def test_calculate_feasibility_score_needs_clarification():
    """Test feasibility calculation returning a mid-range score (NEEDS_CLARIFICATION decision)."""
    facts = {
        "ai_viability": {"category": "HIGHLY_VIABLE", "reason": "Computer vision defect detection"},
        "data_readiness": {"category": "UNLABELED_OR_MESSY", "reason": "Unlabeled X-ray images"},
        "problem_clarity": {"category": "PARTIAL", "reason": "Missing clear defect classes"},
        "integration_feasibility": {"category": "MODERATE", "reason": "PACS hospital system"},
        "governance_and_safety": {"category": "SAFE", "reason": "De-identified medical imaging"},
    }
    rag_scores = [0.10]
    # Score: 30 + 10 + 10 + 10 + 10 = 70. With MODERATE/COMPLEX:
    facts["integration_feasibility"] = {"category": "COMPLEX", "reason": "Legacy PACS hospital system"}
    # Score: 30 + 10 + 10 + 5 + 10 = 65

    result = calculate_feasibility_score(facts, rag_scores)
    assert 20 <= result["score"] < 70
    assert result["decision"] == "NEEDS_CLARIFICATION"


def test_calculate_feasibility_score_no_go_decision():
    """Test feasibility calculation returning a low score with veto (NO_GO decision)."""
    facts = {
        "ai_viability": {"category": "IMPOSSIBLE", "reason": "Sentient conscious AI replacing all humans"},
        "data_readiness": {"category": "NONE", "reason": "All of internet"},
        "problem_clarity": {"category": "VAGUE", "reason": "No concrete workflow"},
        "integration_feasibility": {"category": "COMPLEX", "reason": "Universal integration"},
        "governance_and_safety": {"category": "SAFE", "reason": "Hypothetical"},
    }
    rag_scores = []

    result = calculate_feasibility_score(facts, rag_scores)
    assert result["score"] <= 18
    assert result["decision"] == "NO_GO"
    assert result["veto_triggered"] is True


def test_deterministic_score_node():
    """Test LangGraph node wrapper deterministic_score()."""
    state = {
        "extracted_facts": {
            "ai_viability": {"category": "HIGHLY_VIABLE", "reason": "OCR + matching"},
            "data_readiness": {"category": "READY", "reason": "Historical PDFs and DB"},
            "problem_clarity": {"category": "CLEAR", "reason": "Clear manual invoice pain point"},
            "integration_feasibility": {"category": "MODERATE", "reason": "SAP ERP read/match"},
            "governance_and_safety": {"category": "SAFE", "reason": "Internal invoice data"},
        },
        "rag_scores": [0.65],
    }

    node_output = deterministic_score(state)
    assert "score" in node_output
    assert "score_breakdown" in node_output
    assert "sub_scores" in node_output
    assert node_output["decision"] == "GO"


def test_pydantic_form_submission_validation():
    """Test Pydantic validation for FormSubmission schema."""
    valid_payload = {
        "project_name": "Test Project",
        "department": "corporate_support",
        "team_contact_name": "Jane Doe",
        "team_contact_email": "jane.doe@segula.fr",
        "problem_description": "Valid problem description text.",
        "deadline_urgency": "medium",
    }
    form = FormSubmission(**valid_payload)
    assert form.project_name == "Test Project"
    assert form.deadline_urgency == DeadlineUrgency.MEDIUM

    # Invalid deadline_urgency Literal value should raise ValidationError
    invalid_urgency_payload = dict(valid_payload, deadline_urgency="SUPER_URGENT")
    with pytest.raises(ValidationError):
        FormSubmission(**invalid_urgency_payload)


def test_pydantic_decision_override_validation():
    """Test Pydantic validation for DecisionOverrideInput schema."""
    valid_override = {
        "decision": "GO",
        "reviewer_name": "Engineer Alex",
        "reviewer_notes": "Reviewed and approved.",
    }
    override = DecisionOverrideInput(**valid_override)
    assert override.decision == Decision.GO.value

    # Invalid decision enum raises ValidationError
    with pytest.raises(ValidationError):
        DecisionOverrideInput(decision="SUPER_APPROVED", reviewer_name="Test")
