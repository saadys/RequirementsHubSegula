"""
models/ReviewerModel.py
DB operations for the `reviewer_overrides` table.
Append-only audit log — each override creates a NEW row, never updates existing ones.
The original scoring_result is preserved separately for historical traceability.
"""

import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .BaseDataModel import BaseDataModel, to_uuid
from .db_schemes.requirementshub.schemes.reviewer_override import ReviewerOverride

logger = logging.getLogger("backend.models.reviewer")


class ReviewerModel(BaseDataModel):

    def __init__(self, db_client: AsyncSession):
        super().__init__(db_client)

    async def create_override(
        self,
        submission_id: str | uuid.UUID,
        previous_decision: str,
        new_decision: str,
        reviewer_name: str | None = "AI Engineer",
        reviewer_notes: str | None = None,
    ) -> ReviewerOverride:
        """
        Append a new override record.
        Never updates an existing override — full audit history is preserved.
        """
        uid = to_uuid(submission_id)
        if not uid:
            raise ValueError(f"Invalid UUID: {submission_id}")
        override = ReviewerOverride(
            submission_id=uid,
            previous_decision=previous_decision,
            new_decision=new_decision,
            reviewer_name=reviewer_name,
            reviewer_notes=reviewer_notes,
        )
        logger.info(
            "Override created: submission=%s %s -> %s by %s",
            submission_id,
            previous_decision,
            new_decision,
            reviewer_name,
        )
        return await self.save_and_return(override)

    async def save_override(self, override: ReviewerOverride) -> ReviewerOverride:
        """Save a ReviewerOverride ORM instance."""
        return await self.save_and_return(override)

    async def get_overrides_for_submission(
        self, submission_id: str | uuid.UUID
    ) -> list[ReviewerOverride]:
        """Returns all overrides for a submission, ordered by creation date."""
        uid = to_uuid(submission_id)
        if not uid:
            return []
        result = await self.db_client.execute(
            select(ReviewerOverride)
            .where(ReviewerOverride.submission_id == uid)
            .order_by(ReviewerOverride.created_at.desc())
        )
        return list(result.scalars().all())

    get_overrides_by_submission_id = get_overrides_for_submission
