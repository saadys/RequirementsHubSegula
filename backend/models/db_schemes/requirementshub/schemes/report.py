"""
models/db_schemes/requirementshub/schemes/report.py
ORM model for the `reports` table.
Stores the final generated Markdown document for a submission.
1:1 relationship with submissions (UNIQUE constraint on submission_id).
"""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base

if TYPE_CHECKING:
    from .submission import Submission


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (UniqueConstraint("submission_id", name="uq_report_submission"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # FULL_CAHIER_DES_CHARGES | FAST_TRACK_SOLUTION | NO_GO_SUMMARY
    report_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Full Markdown content
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=True
    )

    # Relationship back to submission
    submission: Mapped["Submission"] = relationship(back_populates="report")

    def __repr__(self) -> str:
        return (
            f"<Report submission_id={self.submission_id} "
            f"type={self.report_type!r}>"
        )
