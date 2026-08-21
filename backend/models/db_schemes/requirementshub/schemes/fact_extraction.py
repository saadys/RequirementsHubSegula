"""
models/db_schemes/requirementshub/schemes/fact_extraction.py
ORM model for the `fact_extractions` table.
Stores structured facts extracted by the LLM pipeline from a raw submission.
1:1 relationship with submissions (UNIQUE constraint on submission_id).
"""

import uuid
from sqlalchemy import String, Boolean, Text, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base

JSON_TYPE = JSONB().with_variant(JSON, "sqlite")


class FactExtraction(Base):
    __tablename__ = "fact_extractions"
    __table_args__ = (UniqueConstraint("submission_id", name="uq_fact_extraction_submission"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── 5-Pillar Categorical Extraction Columns ───────────────────────────
    # AI Viability (HIGHLY_VIABLE, MARGINAL, NOT_AI, IMPOSSIBLE)
    ai_viability_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_viability_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Data Readiness (READY, UNLABELED_OR_MESSY, NONE)
    data_readiness_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    data_readiness_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Problem Clarity (CLEAR, PARTIAL, CONTRADICTORY, VAGUE)
    problem_clarity_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    problem_clarity_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Integration Feasibility (SIMPLE, MODERATE, COMPLEX)
    integration_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    integration_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Governance & Safety (SAFE, MODERATE_RISK, CRITICAL_RISK)
    governance_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    governance_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Technical Details
    identified_technique: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Raw Structured JSON Payload
    raw_extraction: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False, default=dict)

    # ── Legacy Backward-Compatible Columns ───────────────────────────────
    has_clear_problem_statement: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    problem_is_ai_solvable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    requires_new_research: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    problem_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    data_availability: Mapped[str | None] = mapped_column(String(20), nullable=True)
    data_volume_sufficient: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_technique_identified: Mapped[str | None] = mapped_column(Text, nullable=True)
    integration_complexity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    estimated_effort: Mapped[str | None] = mapped_column(String(20), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Provider/model that actually produced this extraction (e.g. "gemini/gemini-3.1-flash-lite",
    # "openai/gpt-4o" after a silent fallback). Governance trail for GO/NO-GO decisions.
    llm_model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # JSONB arrays
    extracted_requirements: Mapped[list] = mapped_column(JSON_TYPE, nullable=False, default=list)
    risks_identified: Mapped[list] = mapped_column(JSON_TYPE, nullable=False, default=list)

    # Relationship back to submission
    submission: Mapped["Submission"] = relationship(back_populates="fact_extraction")

    def __repr__(self) -> str:
        cat = self.ai_viability_category or self.problem_category or "unknown"
        return f"<FactExtraction submission_id={self.submission_id} category={cat!r}>"
