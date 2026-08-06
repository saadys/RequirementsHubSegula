"""
Pydantic Schemas for AI Requirement Hub.
Centralized definitions for request/response payloads, fact extractions, scoring, departments, reports, and clarification.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from backend.config import MAX_CLARIFICATION_ROUNDS
# pyrefly: ignore [missing-import]
from .Enums import Decision, SubmissionStatus


# ── LLM Extraction Schema ────────────────────────────────────────────

class FactExtraction(BaseModel):
    """Structured facts extracted by LLM from business requests."""

    has_clear_problem_statement: bool = Field(
        description="The team clearly described what problem they want to solve"
    )
    problem_is_ai_solvable: bool = Field(
        description="The described problem can realistically be solved with AI/ML"
    )
    problem_category: Literal[
        "classification",
        "regression",
        "clustering",
        "nlp",
        "computer_vision",
        "time_series",
        "recommendation",
        "optimization",
        "generative",
        "other",
        "unknown",
    ] = Field(description="The AI/ML problem type that best fits this request")

    data_availability: Literal["none", "partial", "full"] = Field(
        description="How much relevant data the team currently has"
    )
    data_volume_sufficient: Literal["yes", "no", "unknown"] = Field(
        description="Whether the described data volume is enough for the approach"
    )

    ai_technique_identified: str = Field(
        description="Specific AI technique recommended, or 'unknown'"
    )
    requires_new_research: bool = Field(
        description="Whether this requires research beyond established techniques"
    )
    integration_complexity: Literal["low", "medium", "high"] = Field(
        description="How complex it would be to integrate the AI solution"
    )
    estimated_effort: Literal["small", "medium", "large"] = Field(
        description="small (<4 weeks), medium (4-12), large (>12)"
    )

    risks_identified: List[str] = Field(
        description="List of potential risks or blockers"
    )
    extracted_requirements: List[str] = Field(
        description="Concrete requirements extracted from the request"
    )
    summary: str = Field(
        description="2-3 sentence summary of what the team needs"
    )


# ── Submission & Request Schemas ─────────────────────────────────────

class FormSubmission(BaseModel):
    """Payload received when a team submits an AI project request."""

    project_name: Optional[str] = None
    department: Optional[str] = "corporate_support"
    team_contact_name: Optional[str] = None
    team_contact_email: Optional[str] = None
    problem_description: Optional[str] = None
    current_process: Optional[str] = None
    expected_outcome: Optional[str] = None
    data_description: Optional[str] = None
    deadline_urgency: Optional[Literal["low", "medium", "high", "critical"]] = "low"
    department_specific: Dict[str, Any] = Field(default_factory=dict)


class SubmissionResponse(BaseModel):
    """Response payload returned for a submission."""

    request_id: str
    status: str
    decision: Optional[str] = None
    score: Optional[int] = None
    report_type: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)
    clarification_questions: List[str] = Field(default_factory=list)
    parsed_files_text: List[str] = Field(default_factory=list)
    report: Optional[str] = None
    created_at: Optional[str] = None
    form_data: Dict[str, Any] = Field(default_factory=dict)


# ── Department Schemas ───────────────────────────────────────────────

class DepartmentSummary(BaseModel):
    """Summary representation of a department."""

    id: str = Field(..., description="Unique department identifier")
    display_name: str = Field(..., description="Human-readable department name")
    description: str = Field(..., description="Brief description of department scope")
    enabled: bool = Field(..., description="Whether department form is currently active")


class SpecificField(BaseModel):
    """Field specification for dynamic department fields."""

    name: str
    label: str
    type: str
    options: List[str] = Field(default_factory=list)
    required: bool = False


class DepartmentDetail(BaseModel):
    """Detailed specification for a department form."""

    id: str
    display_name: str
    description: str
    enabled: bool
    specific_fields: List[SpecificField] = Field(default_factory=list)
    required_base_fields: List[str] = Field(default_factory=list)


# ── Report & Score Schemas ───────────────────────────────────────────

class ReportResponse(BaseModel):
    """Payload for markdown report endpoint."""

    request_id: str
    report_type: Optional[str] = Field(
        None, description="Type of report generated: FULL_CAHIER_DES_CHARGES, FAST_TRACK_SOLUTION, NO_GO_SUMMARY"
    )
    report: Optional[str] = Field(
        None, description="Full Markdown content of the report"
    )
    decision: Optional[str] = Field(
        None, description="Pipeline routing decision: GO, NO_GO, NEEDS_CLARIFICATION"
    )
    is_available: bool = Field(
        False, description="Whether the report has been generated and is ready for download"
    )


class ScoreResponse(BaseModel):
    """Payload for score breakdown endpoint."""

    request_id: str
    score: Optional[int] = Field(
        None, description="Overall feasibility score (0-100)"
    )
    percentage: Optional[int] = Field(
        None, description="Overall score percentage"
    )
    decision: Optional[str] = Field(
        None, description="Pipeline routing decision: GO, NO_GO, NEEDS_CLARIFICATION"
    )
    breakdown: Dict[str, Any] = Field(
        default_factory=dict,
        description="7-criterion score breakdown dict detailing criteria points and maximums",
    )


# ── Scoring & Clarification Schemas ─────────────────────────────────

class ScoringResult(BaseModel):
    """Output of the deterministic scoring engine."""

    score: int
    percentage: int
    decision: Decision
    breakdown: Dict[str, Any]


class ClarificationQuestions(BaseModel):
    """Structured output for clarification questions generated by LLM."""

    questions: List[str] = Field(
        description="Targeted questions to clarify gaps, max 5 questions"
    )
    reasoning: List[str] = Field(
        description="Why each question is being asked (1:1 with questions)"
    )


class ClarificationAnswerInput(BaseModel):
    """Input payload when submitting clarification answers."""

    answers: List[str] = Field(
        ...,
        description="List of text answers responding to each clarification question",
        min_length=1,
    )


class ClarificationResponse(BaseModel):
    """Payload returned by clarification endpoints."""

    request_id: str
    status: str
    clarification_round: int
    max_rounds: int = MAX_CLARIFICATION_ROUNDS
    questions: List[str] = Field(default_factory=list)
    answers: List[str] = Field(default_factory=list)
    score: Optional[int] = None
    decision: Optional[str] = None
    report_type: Optional[str] = None
    report: Optional[str] = None


# ── Dashboard & Reviewer Schemas ────────────────────────────────────

class DecisionOverrideInput(BaseModel):
    """Payload for manual decision override by an AI Engineer."""

    decision: Literal["GO", "NO_GO", "NEEDS_CLARIFICATION"] = Field(
        ..., description="New decision status override by AI engineer"
    )
    reviewer_notes: Optional[str] = Field(
        None, description="Optional feedback or rationale from the AI engineer"
    )
    reviewer_name: Optional[str] = Field(
        "AI Engineer", description="Name or ID of the reviewing AI engineer"
    )


class DecisionOverrideResponse(BaseModel):
    """Response payload after a decision override."""

    request_id: str
    decision: str
    status: str
    score: Optional[int] = None
    reviewer_notes: Optional[str] = None
    reviewer_name: Optional[str] = None
    manual_override: bool = True
    updated_at: Optional[str] = None


class PendingSubmissionItem(BaseModel):
    """Submission item overview for the AI Engineer dashboard."""

    request_id: str
    project_name: Optional[str] = "Untitled Project"
    department: Optional[str] = "corporate_support"
    team_contact_name: Optional[str] = "N/A"
    team_contact_email: Optional[str] = "N/A"
    status: str
    decision: Optional[str] = None
    score: Optional[int] = None
    clarification_round: int = 0
    created_at: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)
    has_report: bool = False
    report_type: Optional[str] = None
