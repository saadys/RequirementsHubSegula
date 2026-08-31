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


def test_5_pillar_categorical_fact_extraction():
    """Test 5-pillar CategoricalFactExtraction and individual pillar schemas."""
    from backend.schemas import (
        CategoricalFactExtraction,
        PillarAIViability,
        PillarDataReadiness,
        PillarGovernance,
        PillarIntegration,
        PillarProblemClarity,
    )

    data = {
        "project_summary": "Automating invoice OCR and ERP line-item reconciliation.",
        "identified_technique": "OCR + Fuzzy Matching",
        "target_sub_function": "FINANCE_CONTROLLING",
        "department_relevance": "RELEVANT",
        "ai_viability": {"category": "HIGHLY_VIABLE", "reason": "Standard NLP/OCR automation task."},
        "data_readiness": {"category": "READY", "reason": "1,200 clean PDF invoices monthly."},
        "problem_clarity": {"category": "CLEAR", "reason": "Clear inputs, outputs, and measurable KPIs."},
        "integration_feasibility": {"category": "MODERATE", "reason": "Integrates with SAP ERP via standard table read."},
        "governance_and_safety": {"category": "SAFE", "reason": "Internal accounting data with standard privacy controls."},
    }

    extraction = CategoricalFactExtraction(**data)
    assert extraction.ai_viability.category == "HIGHLY_VIABLE"
    assert extraction.data_readiness.category == "READY"
    assert extraction.problem_clarity.category == "CLEAR"
    assert extraction.integration_feasibility.category == "MODERATE"
    assert extraction.governance_and_safety.category == "SAFE"
    assert extraction.identified_technique == "OCR + Fuzzy Matching"
    assert extraction.department_relevance == "RELEVANT"

    # Test invalid category throws validation error
    invalid_data = data.copy()
    invalid_data["ai_viability"] = {"category": "INVALID_CATEGORY", "reason": "Foo"}
    with pytest.raises(ValidationError):
        CategoricalFactExtraction(**invalid_data)


def test_clarification_questions_model():
    """Test ClarificationQuestionsModel and QuestionItem schemas."""
    from backend.schemas import ClarificationQuestionsModel, QuestionItem

    item = QuestionItem(
        question="What is the expected daily invoice volume?",
        target_pillar="data_readiness",
        technical_reasoning="Needed to evaluate throughput requirements.",
    )
    assert item.target_pillar == "data_readiness"

    model = ClarificationQuestionsModel(questions=[item])
    assert len(model.questions) == 1
    assert model.questions[0].question == "What is the expected daily invoice volume?"


def test_pipeline_state_new_fields():
    """Test PipelineState contains sub_scores, veto_reasons, and veto_triggered fields."""
    from backend.contracts.state import PipelineState

    state: PipelineState = {
        "request_id": "test-req-123",
        "score": 85,
        "sub_scores": {"ai_viability": 30, "data_readiness": 25},
        "veto_triggered": False,
        "veto_reasons": [],
        "decision": "GO",
    }
    assert state["sub_scores"]["ai_viability"] == 30
    assert state["veto_triggered"] is False
    assert state["veto_reasons"] == []


def test_historic_project_ingest_schemas():
    """Test HistoricProjectIngestInput and HistoricProjectIngestResponse schemas."""
    from backend.schemas import (
        HistoricProjectIngestInput,
        HistoricProjectIngestResponse,
        SubmissionStatus,
    )

    assert SubmissionStatus.IMPLEMENTED.value == "IMPLEMENTED"

    valid_payload = {
        "project_name": "Automated LiDAR Defect Detector",
        "department": "automotive",
        "problem_description": "Detect subtle micro-cracks in composite body panels in real-time.",
        "solution_description": "Deployed YOLOv8 segmentation on NVIDIA Jetson with TensorRT acceleration.",
        "outcome": "99.2% defect detection accuracy, reducing inspection time from 15 mins to 8 seconds.",
        "contact_person": "Jane Doe (Lead AI Engineer)",
        "year": 2026,
        "ai_techniques": ["YOLOv8", "TensorRT", "Computer Vision"],
        "tags": ["automotive", "quality_control", "edge_ai"],
        "lessons_learned": "Camera calibration under industrial glare required polarized optical filters.",
    }

    ingest_input = HistoricProjectIngestInput(**valid_payload)
    assert ingest_input.project_name == "Automated LiDAR Defect Detector"
    assert ingest_input.department == "automotive"
    assert len(ingest_input.ai_techniques) == 3
    assert ingest_input.year == 2026

    # Test missing required field raises ValidationError
    invalid_payload = valid_payload.copy()
    del invalid_payload["solution_description"]
    with pytest.raises(ValidationError):
        HistoricProjectIngestInput(**invalid_payload)

    # Test short field fails min_length validation
    invalid_short = valid_payload.copy()
    invalid_short["outcome"] = "bad"  # < 5 chars
    with pytest.raises(ValidationError):
        HistoricProjectIngestInput(**invalid_short)

    # Test response schema
    response = HistoricProjectIngestResponse(
        request_id="req-uuid-999",
        historic_id="HIST-2026-0042",
        project_name="Automated LiDAR Defect Detector",
        status=SubmissionStatus.IMPLEMENTED.value,
        embedding_dimension=768,
    )
    assert response.request_id == "req-uuid-999"
    assert response.historic_id == "HIST-2026-0042"
    assert response.status == "IMPLEMENTED"
    assert response.embedding_dimension == 768


def test_corporate_sub_function_and_out_of_scope_veto():
    """Test CorporateSubFunction mapping and automatic UNRELATED veto coupling."""
    from backend.schemas import (
        CategoricalFactExtraction,
        PillarAIViability,
        PillarDataReadiness,
        PillarGovernance,
        PillarIntegration,
        PillarProblemClarity,
    )

    # 1. Valid in-scope HR project
    hr_data = {
        "project_summary": "Automated CV Screening for Talent Acquisition",
        "identified_technique": "LLM + Fuzzy Matching",
        "target_sub_function": "RECRUITMENT_TALENT_ACQUISITION",
        "department_relevance": "RELEVANT",
        "ai_viability": {"category": "HIGHLY_VIABLE", "reason": "Standard NLP"},
        "data_readiness": {"category": "READY", "reason": "5,000 CVs"},
        "problem_clarity": {"category": "CLEAR", "reason": "Clear KPIs"},
        "integration_feasibility": {"category": "SIMPLE", "reason": "REST API"},
        "governance_and_safety": {"category": "SAFE", "reason": "Anonymized"},
    }
    ext_hr = CategoricalFactExtraction(**hr_data)
    assert ext_hr.target_sub_function == "RECRUITMENT_TALENT_ACQUISITION"
    assert ext_hr.department_relevance == "RELEVANT"

    # 2. Out-of-scope Mechanical/FEA project (e.g. Vehicle Chassis Topology)
    eng_data = {
        "project_summary": "AI-Driven Vehicle Chassis Topology Optimization",
        "identified_technique": "3D Graph Neural Network",
        "target_sub_function": "OUT_OF_SCOPE_ENGINEERING",
        "department_relevance": "RELEVANT", # Model mistakenly passed RELEVANT, validator must force UNRELATED
        "ai_viability": {"category": "HIGHLY_VIABLE", "reason": "GNN surrogate"},
        "data_readiness": {"category": "READY", "reason": "10,000 ANSYS simulations"},
        "problem_clarity": {"category": "CLEAR", "reason": "Von Mises stress prediction"},
        "integration_feasibility": {"category": "MODERATE", "reason": "ANSYS API"},
        "governance_and_safety": {"category": "SAFE", "reason": "Internal CAD"},
    }
    ext_eng = CategoricalFactExtraction(**eng_data)
    assert ext_eng.target_sub_function == "OUT_OF_SCOPE_ENGINEERING"
    assert ext_eng.department_relevance == "UNRELATED"
