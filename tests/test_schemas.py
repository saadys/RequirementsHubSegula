"""
Unit tests for backend.schemas (Enums and Pydantic Schemas).
Verifies model instantiation, defaults, field validation, and Enums values.
"""

import pytest
from pydantic import ValidationError

from backend.schemas import (
    ClarificationQuestions,
    DeadlineUrgency,
    Decision,
    DecisionOverrideInput,
    DecisionOverrideResponse,
    FactExtraction,
    FormSubmission,
    PendingSubmissionItem,
    ProblemCategory,
    ScoringResult,
    SubmissionResponse,
    SubmissionStatus,
)


def test_enums_values():
    """Verify Enum string values match expected domain contract."""
    assert SubmissionStatus.PROCESSED.value == "PROCESSED"
    assert SubmissionStatus.COMPLETED.value == "COMPLETED"
    assert SubmissionStatus.REJECTED.value == "REJECTED"
    assert SubmissionStatus.NEEDS_CLARIFICATION.value == "NEEDS_CLARIFICATION"
    assert SubmissionStatus.INCOMPLETE.value == "INCOMPLETE"
    assert SubmissionStatus.FAST_TRACK.value == "FAST_TRACK"
    assert SubmissionStatus.PENDING.value == "PENDING"

    assert Decision.GO.value == "GO"
    assert Decision.NO_GO.value == "NO_GO"
    assert Decision.NEEDS_CLARIFICATION.value == "NEEDS_CLARIFICATION"

    assert DeadlineUrgency.LOW.value == "low"
    assert DeadlineUrgency.HIGH.value == "high"

    assert ProblemCategory.NLP.value == "nlp"
    assert ProblemCategory.CLASSIFICATION.value == "classification"


def test_form_submission_defaults():
    """Test FormSubmission instantiation and default values."""
    sub = FormSubmission(project_name="AI Test Project")
    assert sub.project_name == "AI Test Project"
    assert sub.department == "corporate_support"
    assert sub.deadline_urgency == "low"
    assert sub.department_specific == {}


def test_submission_response_schema():
    """Test SubmissionResponse schema formatting."""
    resp = SubmissionResponse(
        request_id="test-uuid-123",
        status=SubmissionStatus.COMPLETED.value,
        decision=Decision.GO.value,
        score=85,
    )
    assert resp.request_id == "test-uuid-123"
    assert resp.status == "COMPLETED"
    assert resp.decision == "GO"
    assert resp.score == 85
    assert resp.missing_fields == []
    assert resp.clarification_questions == []


def test_fact_extraction_validation():
    """Test FactExtraction structured model validation."""
    facts_data = {
        "has_clear_problem_statement": True,
        "problem_is_ai_solvable": True,
        "problem_category": "nlp",
        "data_availability": "full",
        "data_volume_sufficient": "yes",
        "ai_technique_identified": "RAG + LLM",
        "requires_new_research": False,
        "integration_complexity": "low",
        "estimated_effort": "small",
        "risks_identified": ["Data security"],
        "extracted_requirements": ["Automate policy answers"],
        "summary": "AI Chatbot for internal HR policies.",
    }
    facts = FactExtraction(**facts_data)
    assert facts.problem_category == "nlp"
    assert facts.data_availability == "full"
    assert facts.summary == "AI Chatbot for internal HR policies."

    # Test invalid category
    invalid_data = facts_data.copy()
    invalid_data["problem_category"] = "invalid_category_xyz"
    with pytest.raises(ValidationError):
        FactExtraction(**invalid_data)


def test_decision_override_input():
    """Test DecisionOverrideInput schema."""
    override = DecisionOverrideInput(
        decision="GO",
        reviewer_notes="Approved after manual risk check.",
        reviewer_name="Lead AI Engineer",
    )
    assert override.decision == "GO"
    assert override.reviewer_name == "Lead AI Engineer"


def test_department_schemas():
    """Test DepartmentSummary and DepartmentDetail schemas."""
    from backend.schemas import DepartmentDetail, DepartmentSummary, SpecificField

    summary = DepartmentSummary(
        id="corporate_support",
        display_name="Corporate & Support Services",
        description="HR & IT Services",
        enabled=True,
    )
    assert summary.id == "corporate_support"
    assert summary.enabled is True

    field = SpecificField(name="service_area", label="Service Area", type="select", options=["hr", "it"], required=True)
    detail = DepartmentDetail(
        id="corporate_support",
        display_name="Corporate & Support Services",
        description="HR & IT Services",
        enabled=True,
        specific_fields=[field],
        required_base_fields=["project_name"],
    )
    assert len(detail.specific_fields) == 1
    assert detail.specific_fields[0].name == "service_area"


def test_report_and_score_schemas():
    """Test ReportResponse and ScoreResponse schemas."""
    from backend.schemas import ReportResponse, ScoreResponse

    report_resp = ReportResponse(
        request_id="req-101",
        report_type="FULL_CAHIER_DES_CHARGES",
        report="# Project Feasibility Report",
        decision="GO",
        is_available=True,
    )
    assert report_resp.is_available is True
    assert report_resp.decision == "GO"

    score_resp = ScoreResponse(
        request_id="req-101",
        score=85,
        percentage=85,
        decision="GO",
        breakdown={"problem_clarity": {"score": 20, "max": 20}},
    )
    assert score_resp.score == 85
    assert "problem_clarity" in score_resp.breakdown


def test_clarification_schemas():
    """Test ClarificationAnswerInput and ClarificationResponse schemas."""
    from backend.schemas import ClarificationAnswerInput, ClarificationResponse

    answer_input = ClarificationAnswerInput(answers=["We have 500 PDF documents."])
    assert len(answer_input.answers) == 1

    clarif_resp = ClarificationResponse(
        request_id="req-102",
        status="NEEDS_CLARIFICATION",
        clarification_round=1,
        max_rounds=2,
        questions=["How many users?"],
        answers=["Around 200 users."],
    )
    assert clarif_resp.clarification_round == 1
    assert clarif_resp.max_rounds == 2
