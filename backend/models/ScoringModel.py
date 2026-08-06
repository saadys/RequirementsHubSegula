"""
models/ScoringModel.py
DB operations for the `scoring_results` table.
Written by the deterministic scoring node. Read by admin dashboard and routes.
"""

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .BaseDataModel import BaseDataModel, to_uuid
from .db_schemes.requirementshub.schemes.scoring_result import ScoringResult

logger = logging.getLogger("backend.models.scoring")


class ScoringModel(BaseDataModel):

    def __init__(self, db_client: AsyncSession):
        super().__init__(db_client)

    async def create_or_update(
        self, submission_id: str | uuid.UUID, data: dict[str, Any]
    ) -> ScoringResult:
        """
        Upsert scoring result for a submission.
        Idempotent: if scoring is re-run after clarification, updates existing row.
        The original score is overwritten — audit trail is in reviewer_overrides.
        """
        uid = to_uuid(submission_id)
        if not uid:
            raise ValueError(f"Invalid UUID: {submission_id}")
        existing = await self.get_by_submission_id(uid)

        if existing:
            for key, value in data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            await self.db_client.commit()
            await self.db_client.refresh(existing)
            logger.info("ScoringResult updated for submission %s", submission_id)
            return existing

        scoring = ScoringResult(submission_id=uid, **data)
        return await self.save_and_return(scoring)

    async def save_scoring_result(self, scoring: ScoringResult) -> ScoringResult:
        """Save a ScoringResult ORM instance."""
        if isinstance(scoring, ScoringResult):
            return await self.save_and_return(scoring)
        return await self.create_or_update(scoring["submission_id"], scoring)

    async def get_by_submission_id(self, submission_id: str | uuid.UUID) -> ScoringResult | None:
        """Fetch scoring result by submission UUID."""
        uid = to_uuid(submission_id)
        if not uid:
            return None
        result = await self.db_client.execute(
            select(ScoringResult).where(ScoringResult.submission_id == uid)
        )
        return result.scalar_one_or_none()
