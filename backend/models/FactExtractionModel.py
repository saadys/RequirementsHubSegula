"""
models/FactExtractionModel.py
DB operations for the `fact_extractions` table.
Written by the LLM analyze node. Read by the scoring node and admin dashboard.
"""

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from .BaseDataModel import BaseDataModel, to_uuid
from .db_schemes.requirementshub.schemes.fact_extraction import FactExtraction

logger = logging.getLogger("backend.models.fact_extraction")


class FactExtractionModel(BaseDataModel):

    def __init__(self, db_client: AsyncSession):
        super().__init__(db_client)

    async def create_or_update(
        self, submission_id: str | uuid.UUID, data: dict[str, Any]
    ) -> FactExtraction:
        """
        Upsert fact extraction for a submission.
        Uses PostgreSQL ON CONFLICT for idempotent pipeline re-runs.
        If the LLM pipeline reruns (e.g., after clarification), the existing
        row is updated rather than creating a duplicate.
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
            logger.info("FactExtraction updated for submission %s", submission_id)
            return existing

        fact = FactExtraction(submission_id=uid, **data)
        return await self.save_and_return(fact)

    async def save_fact_extraction(self, fact: FactExtraction) -> FactExtraction:
        """Save a FactExtraction ORM instance."""
        if isinstance(fact, FactExtraction):
            return await self.save_and_return(fact)
        return await self.create_or_update(fact["submission_id"], fact)

    async def get_by_submission_id(self, submission_id: str | uuid.UUID) -> FactExtraction | None:
        """Fetch fact extraction by submission UUID."""
        uid = to_uuid(submission_id)
        if not uid:
            return None
        result = await self.db_client.execute(
            select(FactExtraction).where(FactExtraction.submission_id == uid)
        )
        return result.scalar_one_or_none()
