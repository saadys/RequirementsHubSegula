"""
Pydantic Schemas — Shared Data Models

All structured data models used across the pipeline.
FactExtraction is the bridge between Track A (LLM) and Track B (scoring).

⚠️  SHARED FILE — Do not edit without agreement from both engineers.
"""

from typing import Literal

from pydantic import BaseModel, Field


# ── LLM Output Schema ────────────────────────────────────────────


class FactExtraction(BaseModel):
    """Structured facts the LLM extracts from a business team's AI request.
    Used by the deterministic scoring engine to calculate feasibility."""

    # Problem Understanding
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

    # Data Assessment
    data_availability: Literal["none", "partial", "full"] = Field(
        description="How much relevant data the team currently has"
    )
    data_volume_sufficient: Literal["yes", "no", "unknown"] = Field(
        description="Whether the described data volume is enough for the approach"
    )

    # Technical Assessment
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

    # Qualitative
    risks_identified: list[str] = Field(
        description="List of potential risks or blockers"
    )
    extracted_requirements: list[str] = Field(
        description="Concrete requirements extracted from the request"
    )
    summary: str = Field(
        description="2-3 sentence summary of what the team needs"
    )


# ── API Input Schema ─────────────────────────────────────────────


class FormSubmission(BaseModel):
    """What the API receives when a team submits a request."""

    project_name: str
    department: str
    team_contact_name: str
    team_contact_email: str
    problem_description: str  # min 100 chars
    current_process: str  # How they do it today
    expected_outcome: str  # What success looks like
    data_description: str | None = None
    deadline_urgency: Literal["low", "medium", "high", "critical"]
    # Department-specific fields stored as flexible dict
    department_specific: dict = {}


# ── Scoring Output Schema ────────────────────────────────────────


class ScoringResult(BaseModel):
    """Output of the deterministic scoring engine."""

    score: int  # 0-100
    percentage: int
    decision: Literal["GO", "NO_GO", "NEEDS_CLARIFICATION"]
    breakdown: dict  # criterion -> {"score": int, "max": int}


# ── Clarification Schema ─────────────────────────────────────────


class ClarificationQuestions(BaseModel):
    """Structured output for clarification questions the LLM generates."""

    questions: list[str] = Field(
        description="Targeted questions to clarify gaps, max 5 questions"
    )
    reasoning: list[str] = Field(
        description="Why each question is being asked (1:1 with questions)"
    )
