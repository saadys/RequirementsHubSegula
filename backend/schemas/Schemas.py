"""
Pydantic Schemas for AI Requirement Hub.
Centralized definitions for request/response payloads, fact extractions, scoring, departments, reports, and clarification.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from backend.config import MAX_CLARIFICATION_ROUNDS
# pyrefly: ignore [missing-import]
from .Enums import Decision, SubmissionStatus


# ── 5-Pillar Categorical Extraction Schemas ───────────────────────────

class PillarAIViability(BaseModel):
    category: Literal["HIGHLY_VIABLE", "MARGINAL", "NOT_AI", "IMPOSSIBLE"] = Field(
        ...,
        description=(
            "HIGHLY_VIABLE: The requested business capability is fundamentally well-suited to AI, established techniques can plausibly achieve the required outcome, and AI provides meaningful value compared with deterministic or conventional software..\n"
            "MARGINAL: AI can technically be used, but conventional software, SaaS, rules, or simpler analytics are likely to achieve the business objective more reliably, cheaply, or transparently...\n"
            "NOT_AI: The requested outcome is fundamentally deterministic and does not require prediction, inference, generation, perception, or learning.\n"
            "IMPOSSIBLE: Defies physics, math, causality, or The requested outcome cannot reasonably be achieved with current AI capabilities or the stated constraints.."
        )
    )
    reason: str = Field(..., description="1-2 sentences technical justification.")


class PillarDataReadiness(BaseModel):
    category: Literal["READY", "UNLABELED_OR_MESSY", "NONE"] = Field(
        ...,
        description=(
            "READY: Relevant data is demonstrably accessible, sufficiently structured/clean "
            "for the proposed approach, and the required labels or target variables exist "
            "when supervised learning is required.\n"
            "UNLABELED_OR_MESSY: Relevant data exists, but labels, structure, quality, "
            "access rights, completeness, or other requirements needed for the proposed "
            "approach are missing or unconfirmed.\n"
            "NONE: No data exists yet or it is scattered on personal laptops without access permissions or the user does not have the permission to access the data or he dont answer the data description in a logical way"
        )
    )
    reason: str = Field(..., description="1-2 sentences data readiness assessment.")


class PillarProblemClarity(BaseModel):
    category: Literal["CLEAR", "PARTIAL", "CONTRADICTORY", "VAGUE"] = Field(
        ...,
        description=(
            "CLEAR: Concrete workflow, defined inputs/outputs, explicit pain point, and measurable KPIs , ONLY IF THE USER STATED ALL OF THIS THEN ITS CLEAR IF SOMETHING IS MISSING FROM THESE 4 ITS PARTIAL.\n"
            "PARTIAL: Clear business intent but missing volume, format, or success threshold , any missing clarification from the user of this (Concrete workflow, defined inputs/outputs, explicit pain point, and measurable KPIs ) its considered partial , all of them needs to be present to be considered clear.\n"
            "CONTRADICTORY: Contains mutually exclusive requirements (e.g. 100% autonomous with 100% human approval).\n"
            "VAGUE: Pure buzzwords with no concrete business process."
        )
    )
    reason: str = Field(..., description="1-2 sentences problem clarity assessment.")


class PillarIntegration(BaseModel):
    category: Literal["SIMPLE", "MODERATE", "COMPLEX"] = Field(
        ...,
        description=(
            "SIMPLE: Standalone UI, batch file export, or clean REST API.\n"
            "MODERATE: Standard enterprise systems (SharePoint, Jira, modern ERP).\n"
            "COMPLEX: Legacy SAP write permissions, real-time robotics, or hard infra dependencies."
        )
    )
    reason: str = Field(..., description="1-2 sentences integration assessment.")


class PillarGovernance(BaseModel):
    category: Literal["SAFE", "MODERATE_RISK", "CRITICAL_RISK"] = Field(
        ...,
        description=(
            "SAFE: No meaningful privacy, security, safety, legal, or ethical concerns are evident..\n"
            "MODERATE_RISK: Contains personal/internal data or requires meaningful human oversight, but there is no evident prohibited use, high-impact profiling, surveillance, sensitive inference, or serious legal/compliance concern. IF THE USER DO NOT SPECIFY HOW TO HANDLE THE RISK DO NOT ASSUME POSITIVELY , IF ITS CRITICAL ITS CRITICAL IF THERE ARE NO SOLUTIONS TO HANDLE IT WITH COMPLIANCE TO General Data Protection Regulation flag it directly to critical , if there is a solution flag it as moderate\n"
            "CRITICAL_RISK: The described use case involves prohibited activity, unauthorized surveillance, sensitive profiling/inference of individuals, high-impact employment decisions based on personal data, serious privacy violations, illegal activity, or other substantial legal/ethical risk.."
        )
    )
    reason: str = Field(..., description="1-2 sentences governance and compliance assessment.")


CorporateSubFunction = Literal[
    "HR_PERSONNEL",
    "RECRUITMENT_TALENT_ACQUISITION",
    "FINANCE_CONTROLLING",
    "PROCUREMENT_PURCHASING",
    "IT_INTERNAL_HELPDESK",
    "LEGAL_COMPLIANCE",
    "GENERAL_ADMIN_FACILITIES",
    "QUALITY_INTERNAL_AUDIT",
    "TRAINING_ONBOARDING",
    "DOCUMENT_ENGINEERING",
    "OUT_OF_SCOPE_ENGINEERING",
    "OUT_OF_SCOPE_OTHER",
]


class CategoricalFactExtraction(BaseModel):
    project_summary: str = Field(..., description="2-3 sentences concise technical summary of the submission.")
    identified_technique: str = Field(..., description="Recommended technical approach (e.g., 'OCR + Fuzzy Matching', 'RAG', 'Standard Python ETL Script') , 'LLM + Agentic Workflow', etc.")
    target_sub_function: CorporateSubFunction = Field(
        ...,
        description=(
            "HR_PERSONNEL: Human Resources, employee lifecycle, personnel administration.\n"
            "RECRUITMENT_TALENT_ACQUISITION: Candidate screening, job matching, CV parsing.\n"
            "FINANCE_CONTROLLING: Accounting, invoicing, expense tracking, cost control.\n"
            "PROCUREMENT_PURCHASING: Vendor management, supplier orders, purchase order processing.\n"
            "IT_INTERNAL_HELPDESK: Internal employee IT ticketing, hardware/software assets, internal corporate portals (NOT engineering simulation/CAD/CAE clusters).\n"
            "LEGAL_COMPLIANCE: Contracts, regulatory compliance, GDPR data privacy.\n"
            "GENERAL_ADMIN_FACILITIES: Office management, building logistics, site operations.\n"
            "QUALITY_INTERNAL_AUDIT: Internal ISO standards compliance, audit support, deliverable quality checks.\n"
            "TRAINING_ONBOARDING: Employee training, technical onboarding, skills upskilling.\n"
            "DOCUMENT_ENGINEERING: Internal user manuals, technical documentation, knowledge base indexing.\n"
            "OUT_OF_SCOPE_ENGINEERING: Operational engineering (Mechanical, FEA, CFD, CAD, crash simulation, automotive design, mechatronics, embedded systems).\n"
            "OUT_OF_SCOPE_OTHER: Any other operational or external domain outside corporate support."
        ),
    )
    department_relevance: Literal["RELEVANT", "PARTIALLY_RELEVANT", "UNRELATED"] = Field(
        default="RELEVANT",
        description=(
            "RELEVANT: The project clearly falls within one of the 11 Corporate & Support Services functions "
            "(HR, Recruitment, Finance, Procurement, IT, Admin, Legal, Communication, Quality, Training, Knowledge Management).\n"
            "PARTIALLY_RELEVANT: The project has a Corporate Support component but also touches engineering/operational domains.\n"
            "UNRELATED: The project is clearly an engineering, manufacturing, automotive, medical, or other domain "
            "that does not belong to Corporate & Support Services."
        ),
    )
    ai_viability: PillarAIViability
    data_readiness: PillarDataReadiness
    problem_clarity: PillarProblemClarity
    integration_feasibility: PillarIntegration
    governance_and_safety: PillarGovernance

    @field_validator("target_sub_function", mode="before")
    @classmethod
    def normalize_target_sub_function(cls, v: Any) -> str:
        if v is None or v == "":
            raise ValueError("target_sub_function is required and cannot be null.")
        s = str(v).strip().upper()
        if "ENGINEERING" in s or "MECHANICAL" in s or "AUTOMOTIVE" in s or "CAD" in s or "FEA" in s or "SIMULATION" in s:
            return "OUT_OF_SCOPE_ENGINEERING"
        if "RECRUIT" in s or "TALENT" in s or "CV" in s:
            return "RECRUITMENT_TALENT_ACQUISITION"
        if "HR" in s or "PERSONNEL" in s:
            return "HR_PERSONNEL"
        if "FINANCE" in s or "ACCOUNTING" in s or "INVOICE" in s:
            return "FINANCE_CONTROLLING"
        if "PROCURE" in s or "PURCHAS" in s or "ACHAT" in s or "SUPPLIER" in s:
            return "PROCUREMENT_PURCHASING"
        if "HELPDESK" in s or "IT_SUPPORT" in s or "TICKET" in s:
            return "IT_INTERNAL_HELPDESK"
        if "LEGAL" in s or "COMPLIANCE" in s or "GDPR" in s or "JURIDIQUE" in s:
            return "LEGAL_COMPLIANCE"
        if "ADMIN" in s or "FACILIT" in s:
            return "GENERAL_ADMIN_FACILITIES"
        if "QUALITY" in s or "AUDIT" in s or "ISO" in s:
            return "QUALITY_INTERNAL_AUDIT"
        if "TRAIN" in s or "ONBOARD" in s:
            return "TRAINING_ONBOARDING"
        if "DOCUMENT" in s or "KNOWLEDGE" in s:
            return "DOCUMENT_ENGINEERING"
        if "OUT_OF_SCOPE" in s or "OTHER" in s or "UNRELATED" in s:
            return "OUT_OF_SCOPE_OTHER"
        return s

    @model_validator(mode="after")
    def sync_department_relevance(self) -> "CategoricalFactExtraction":
        if self.target_sub_function in ("OUT_OF_SCOPE_ENGINEERING", "OUT_OF_SCOPE_OTHER"):
            self.department_relevance = "UNRELATED"
        return self


class QuestionItem(BaseModel):
    question: str
    target_pillar: str = Field(
        default="problem_clarity",
        description="Target pillar or requirement category (e.g. data_readiness, problem_clarity, integration, governance)",
    )
    technical_reasoning: str = Field(
        default="Required to resolve scope and technical feasibility ambiguities.",
        description="Technical rationale for why this clarification is needed",
    )


class ClarificationQuestionsModel(BaseModel):
    questions: List[QuestionItem] = Field(default_factory=list, max_length=4)


# ── LLM Extraction Schema (Legacy Compatibility) ─────────────────────

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
    sub_scores: Dict[str, int] = Field(default_factory=dict, description="5-pillar sub-scores")
    veto_triggered: bool = Field(default=False, description="Whether a circuit breaker veto was triggered")
    veto_reasons: List[str] = Field(default_factory=list, description="Veto reasons if triggered")
    report_type: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)
    clarification_questions: List[Any] = Field(default_factory=list)
    clarification_round: int = Field(0, description="Current clarification round number")
    max_rounds: int = Field(MAX_CLARIFICATION_ROUNDS, description="Maximum allowed clarification rounds")
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
        None, description="Pipeline routing decision: GO, NO_GO, NEEDS_CLARIFICATION, FAST_TRACK"
    )
    score: Optional[int] = Field(
        None, description="Feasibility score (0-100)"
    )
    sub_scores: Dict[str, int] = Field(
        default_factory=dict,
        description="5-pillar sub-score breakdown",
    )
    veto_triggered: bool = Field(
        default=False,
        description="Whether a circuit-breaker veto was triggered",
    )
    veto_reasons: List[str] = Field(
        default_factory=list,
        description="List of circuit-breaker veto reasons",
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
        None, description="Pipeline routing decision: GO, NO_GO, NEEDS_CLARIFICATION, FAST_TRACK"
    )
    sub_scores: Dict[str, int] = Field(
        default_factory=dict,
        description="5-pillar sub-scores (ai_viability, data_readiness, problem_clarity, integration, governance)",
    )
    veto_triggered: bool = Field(
        default=False,
        description="Whether a circuit-breaker veto was triggered",
    )
    veto_reasons: List[str] = Field(
        default_factory=list,
        description="List of circuit-breaker veto reasons",
    )
    breakdown: Dict[str, Any] = Field(
        default_factory=dict,
        description="Score breakdown dict detailing criteria points or sub-scores",
    )
    pillars: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Categorical breakdown per pillar if available",
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
    questions: List[Any] = Field(default_factory=list)
    answers: List[str] = Field(default_factory=list)
    score: Optional[int] = None
    decision: Optional[str] = None
    sub_scores: Dict[str, int] = Field(default_factory=dict)
    veto_triggered: bool = Field(default=False)
    veto_reasons: List[str] = Field(default_factory=list)
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
    sub_scores: Dict[str, int] = Field(default_factory=dict)
    veto_triggered: bool = False
    veto_reasons: List[str] = Field(default_factory=list)
    ai_viability_category: Optional[str] = None
    data_readiness_category: Optional[str] = None
    problem_clarity_category: Optional[str] = None
    integration_category: Optional[str] = None
    governance_category: Optional[str] = None
    clarification_round: int = 0
    created_at: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)
    has_report: bool = False
    report_type: Optional[str] = None


class HistoricProjectIngestInput(BaseModel):
    """Payload for ingesting a successfully delivered project into the historic vector knowledge base."""

    project_name: str = Field(..., min_length=2, description="Name of the delivered AI project")
    department: str = Field(..., min_length=2, description="Originating department or business unit")
    problem_description: str = Field(..., min_length=10, description="Detailed problem statement and initial requirements")
    solution_description: str = Field(..., min_length=10, description="Real-world delivered AI architecture and methodology")
    outcome: str = Field(..., min_length=5, description="Actual achieved metric, ROI, accuracy, or business outcome")
    contact_person: Optional[str] = Field(None, description="Lead AI engineer or contact point")
    year: Optional[int] = Field(None, description="Delivery year (e.g. 2026)")
    ai_techniques: List[str] = Field(default_factory=list, description="AI models, algorithms, and frameworks used")
    tags: List[str] = Field(default_factory=list, description="Categorization tags and domain keywords")
    lessons_learned: Optional[str] = Field(None, description="Practical advice, operational pitfalls, and key learnings")


class HistoricProjectIngestResponse(BaseModel):
    """Response payload after ingesting a project into the pgvector knowledge base."""

    request_id: str = Field(..., description="Original submission UUID")
    historic_id: str = Field(..., description="Generated historic project ID (e.g. HIST-2026-XXXX)")
    project_name: str
    status: str = "IMPLEMENTED"
    embedding_dimension: int = 768
    message: str = "Project successfully vectorized and ingested into knowledge base."

