"""
models/db_schemes/requirementshub/schemes/scoring_result.py
ORM model for the `scoring_results` table.
Stores automated feasibility score and deterministic routing decision.
1:1 relationship with submissions (UNIQUE constraint on submission_id).
"""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base

if TYPE_CHECKING:
    from .submission import Submission

JSON_TYPE = JSONB().with_variant(JSON, "sqlite")


class ScoringResult(Base):
    __tablename__ = "scoring_results"
    __table_args__ = (UniqueConstraint("submission_id", name="uq_scoring_result_submission"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Scores: 0 to 100
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    percentage: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # GO | NO_GO | NEEDS_CLARIFICATION
    decision: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # JSONB: detailed 7-criterion breakdown
    # Example: {"data_quality": {"points": 15, "max": 20}, ...}
    breakdown: Mapped[dict] = mapped_column(JSON_TYPE, nullable=False, default=dict)

    created_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=True
    )

    # Relationship back to submission
    submission: Mapped["Submission"] = relationship(back_populates="scoring_result")

    def __repr__(self) -> str:
        return (
            f"<ScoringResult submission_id={self.submission_id} "
            f"score={self.score} decision={self.decision!r}>"
        )
