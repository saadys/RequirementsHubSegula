"""
models/db_schemes/requirementshub/schemes/submission.py
ORM model for the `submissions` table.
Main table representing an AI project request submitted by a business team.
"""

import uuid
from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base

JSON_TYPE = JSONB().with_variant(JSON, "sqlite")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Project identity
    project_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )

    # Requester contact
    team_contact_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    team_contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Business problem description
    problem_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_process: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Urgency: 'low' | 'medium' | 'high' | 'critical'
    deadline_urgency: Mapped[str] = mapped_column(
        String(20), nullable=False, default="low"
    )

    # JSONB: dynamic department-specific fields (e.g., vehicle_type, contract_number)
    department_specific: Mapped[dict] = mapped_column(
        JSON_TYPE, nullable=False, default=dict
    )

    # Extracted text from uploaded documents (PDFs)
    parsed_files_text: Mapped[list] = mapped_column(
        JSON_TYPE, nullable=False, default=list
    )

    # Pipeline status: PENDING | INCOMPLETE | FAST_TRACK | PROCESSED |
    #                  COMPLETED | REJECTED | NEEDS_CLARIFICATION | FAILED
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="PENDING"
    )

    # Timestamps
    created_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=True
    )
    updated_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True
    )

    # Relationships (1:1 and 1:N)
    department_rel: Mapped["Department"] = relationship(back_populates="submissions")
    fact_extraction: Mapped["FactExtraction | None"] = relationship(
        back_populates="submission", uselist=False, cascade="all, delete-orphan"
    )
    scoring_result: Mapped["ScoringResult | None"] = relationship(
        back_populates="submission", uselist=False, cascade="all, delete-orphan"
    )
    clarification_rounds: Mapped[list["ClarificationRound"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan", order_by="ClarificationRound.round_number"
    )
    report: Mapped["Report | None"] = relationship(
        back_populates="submission", uselist=False, cascade="all, delete-orphan"
    )
    reviewer_overrides: Mapped[list["ReviewerOverride"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Submission id={self.id} status={self.status!r}>"
