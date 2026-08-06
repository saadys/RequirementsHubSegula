"""
models/db_schemes/requirementshub/schemes/clarification_round.py
ORM model for the `clarification_rounds` table.
Tracks clarification Q&A iterations between the LLM and the business user.
1:N relationship with submissions.
"""

import uuid
from sqlalchemy import Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base

JSON_TYPE = JSONB().with_variant(JSON, "sqlite")


class ClarificationRound(Base):
    __tablename__ = "clarification_rounds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Iteration counter: 1 to MAX_CLARIFICATION_ROUNDS
    round_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # JSONB arrays
    questions: Mapped[list] = mapped_column(JSON_TYPE, nullable=False, default=list)
    answers: Mapped[list] = mapped_column(JSON_TYPE, nullable=False, default=list)

    created_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=True
    )

    # Relationship back to submission (N:1)
    submission: Mapped["Submission"] = relationship(back_populates="clarification_rounds")

    def __repr__(self) -> str:
        return (
            f"<ClarificationRound submission_id={self.submission_id} "
            f"round={self.round_number}>"
        )
