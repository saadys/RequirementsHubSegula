"""
models/db_schemes/requirementshub/schemes/reviewer_override.py
ORM model for the `reviewer_overrides` table.
Audit log when an AI Engineer manually changes an automated decision.
The original scoring_result is preserved — this is an append-only audit trail.
"""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base

if TYPE_CHECKING:
    from .submission import Submission


class ReviewerOverride(Base):
    __tablename__ = "reviewer_overrides"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # GO | NO_GO | NEEDS_CLARIFICATION
    previous_decision: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_decision: Mapped[str | None] = mapped_column(String(30), nullable=True)

    reviewer_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=True
    )

    # Relationship back to submission (N:1 — multiple overrides possible)
    submission: Mapped["Submission"] = relationship(back_populates="reviewer_overrides")

    def __repr__(self) -> str:
        return (
            f"<ReviewerOverride submission_id={self.submission_id} "
            f"{self.previous_decision!r} -> {self.new_decision!r}>"
        )
