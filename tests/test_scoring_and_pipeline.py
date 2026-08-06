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
        "has_clear_problem_statement": True,      # 20 pts
        "problem_is_ai_solvable": True,           # 15 pts
        "data_availability": "full",               # 20 pts
        "requires_new_research": False,            # 10 pts
        "ai_technique_identified": "nlp",          # 10 pts
        "integration_complexity": "low",           # 10 pts
    }
    rag_scores = [0.80]                            # 15 pts (max RAG >= 0.75)
    # Total expected score = 20 + 15 + 20 + 15 + 10 + 10 + 10 = 100

    result = calculate_feasibility_score(facts, rag_scores)
    assert result["score"] == 100
    assert result["decision"] == "GO"
    assert result["breakdown"]["problem_clarity"]["score"] == 20
    assert result["breakdown"]["data_availability"]["score"] == 20


def test_calculate_feasibility_score_needs_clarification():
    """Test feasibility calculation returning a mid-range score (NEEDS_CLARIFICATION decision)."""
    facts = {
        "has_clear_problem_statement": True,      # 20 pts
        "problem_is_ai_solvable": True,           # 15 pts
        "data_availability": "partial",            # 10 pts
        "requires_new_research": True,             # 3 pts
        "ai_technique_identified": "unknown",      # 0 pts
        "integration_complexity": "medium",        # 7 pts
    }
    rag_scores = [0.10]                            # 5 pts
    # Total score = 20 + 15 + 10 + 5 + 3 + 0 + 7 = 60

    result = calculate_feasibility_score(facts, rag_scores)
    assert 40 <= result["score"] < 70
    assert result["decision"] == "NEEDS_CLARIFICATION"


def test_calculate_feasibility_score_no_go_decision():
    """Test feasibility calculation returning a low score (NO_GO decision)."""
    facts = {
        "has_clear_problem_statement": False,     # 0 pts
        "problem_is_ai_solvable": False,          # 0 pts
        "data_availability": "none",               # 0 pts
        "requires_new_research": True,             # 3 pts
        "ai_technique_identified": "unknown",      # 0 pts
        "integration_complexity": "high",          # 3 pts
    }
    rag_scores = []                                # 5 pts
    # Total score = 0 + 0 + 0 + 5 + 3 + 0 + 3 = 11

    result = calculate_feasibility_score(facts, rag_scores)
    assert result["score"] < 40
    assert result["decision"] == "NO_GO"


def test_deterministic_score_node():
    """Test LangGraph node wrapper deterministic_score()."""
    state = {
        "extracted_facts": {
            "has_clear_problem_statement": True,
            "problem_is_ai_solvable": True,
            "data_availability": "full",
            "requires_new_research": False,
            "ai_technique_identified": "classification",
            "integration_complexity": "low",
        },
        "rag_scores": [0.90],
    }

    node_output = deterministic_score(state)
    assert "score" in node_output
    assert "score_breakdown" in node_output
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
